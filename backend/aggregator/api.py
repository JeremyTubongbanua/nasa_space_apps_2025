from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
import sys
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
try:
    from twilio.base.exceptions import TwilioException
    from twilio.rest import Client as TwilioClient
except ImportError:  # pragma: no cover - optional dependency safeguard
    TwilioClient = None  # type: ignore

    class TwilioException(Exception):
        """Fallback Twilio exception when library is unavailable."""

import uvicorn

if __name__ == "__main__" and __package__ is None:
    package_root = Path(__file__).resolve().parent
    if str(package_root) not in sys.path:
        sys.path.append(str(package_root))
    from insights import generate_insights  # type: ignore
    from openaq import router as openaq_router  # type: ignore
    from openmeteo import router as openmeteo_router  # type: ignore
    from openmeteo.data_access import LOCATION_CATALOG  # type: ignore
else:
    from .insights import generate_insights
    from .openaq import router as openaq_router
    from .openmeteo import router as openmeteo_router
    from .openmeteo.data_access import LOCATION_CATALOG

app = FastAPI()
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(openaq_router)
app.include_router(openmeteo_router)


AQI_ENDPOINTS: Tuple[str, ...] = (
    "https://air-quality-api.open-meteo.com/v1/air-quality",
    "https://api.open-meteo.com/v1/air-quality",
)
GEOCODING_ENDPOINT = "https://geocoding-api.open-meteo.com/v1/search"
AQI_PARAMS = {"current": "us_aqi", "timezone": "auto"}
QUIZ_DATA_PATH = Path(__file__).resolve().parent / "data" / "quiz_responses.json"
TWILIO_COUNT_PATH = Path(__file__).resolve().parent / "data" / "twilio_send_count.json"
TWILIO_ENV_PATH = Path(__file__).resolve().parents[1] / "twilio" / ".env"


def _ensure_twilio_env_loaded() -> None:
    """Populate Twilio environment variables from backend/twilio/.env if missing."""

    if not TWILIO_ENV_PATH.exists():
        return

    try:
        with TWILIO_ENV_PATH.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key:
                    os.environ[key] = value
    except OSError as exc:  # pragma: no cover - filesystem edge case
        logger.warning("Could not load Twilio .env file: %s", exc)


_ensure_twilio_env_loaded()


def _twilio_config() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    _ensure_twilio_env_loaded()
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER") or os.getenv("TWILIO_FROM_NUMBER") or "+14632783084"
    logger.debug(
        "Twilio config loaded: sid=%s token=%s from=%s",
        "set" if sid else "missing",
        "set" if token else "missing",
        from_number,
    )
    return sid, token, from_number


QUIZ_LOCK = Lock()


class AQIFetchError(Exception):
    """Raised when the AQI service cannot return a valid reading."""


def _format_catalog_entry(slug: str, catalog: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    entry = catalog.get(slug, {}).copy()
    entry.setdefault("slug", slug)
    entry.setdefault("location_name", slug.replace("_", " ").title())
    return entry


def fetch_current_aqi(latitude: float, longitude: float) -> Dict[str, Any]:
    """Fetch a US AQI snapshot for a coordinate pair."""

    params = {**AQI_PARAMS, "latitude": latitude, "longitude": longitude}
    last_error: Optional[str] = None

    for endpoint in AQI_ENDPOINTS:
        try:
            response = requests.get(endpoint, params=params, timeout=10)
        except requests.RequestException as exc:  # network hiccups
            last_error = str(exc)
            continue

        if not response.ok:
            last_error = f"HTTP {response.status_code}: {response.reason}"
            continue

        payload = response.json()
        current = payload.get("current") or {}
        value = current.get("us_aqi")
        timestamp = current.get("time")
        units = (payload.get("current_units") or {}).get("us_aqi")

        if value is None:
            last_error = "Service returned no us_aqi value"
            continue

        return {
            "us_aqi": value,
            "timestamp": timestamp,
            "units": units or "US AQI",
            "source": "Open-Meteo",
        }

    raise AQIFetchError(last_error or "Unable to reach AQI provider")


def geocode_query(query: str) -> Optional[Dict[str, Any]]:
    params = {"name": query, "count": 1, "language": "en"}
    try:
        response = requests.get(GEOCODING_ENDPOINT, params=params, timeout=10)
        if not response.ok:
            return None
        payload = response.json()
    except requests.RequestException:
        return None

    results = payload.get("results")
    if not results:
        return None

    result = results[0]
    return {
        "name": result.get("name"),
        "latitude": result.get("latitude"),
        "longitude": result.get("longitude"),
        "country": result.get("country"),
        "admin1": result.get("admin1"),
    }


def resolve_display_name(resolution: Dict[str, Any]) -> Optional[str]:
    if not resolution:
        return None
    name = resolution.get("name")
    if not name:
        return None
    parts = [name]
    admin = resolution.get("admin1")
    country = resolution.get("country")
    if admin:
        parts.append(admin)
    if country:
        parts.append(country)
    return ", ".join(parts)


@app.get("/aqi/current/preset")
def get_preset_aqi() -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for slug in ("ajax", "north_york", "oshawa", "scarborough", "toronto"):
        entry = _format_catalog_entry(slug, LOCATION_CATALOG)
        latitude = entry.get("latitude")
        longitude = entry.get("longitude")
        try:
            if latitude is None or longitude is None:
                raise AQIFetchError("Missing coordinates")
            snapshot = fetch_current_aqi(float(latitude), float(longitude))
            results.append({**entry, **snapshot})
        except AQIFetchError as exc:
            results.append({**entry, "error": str(exc)})
    return results


@app.get("/aqi/current")
def get_current_aqi(
    query: Optional[str] = Query(None, description="Location search term"),
    latitude: Optional[float] = Query(None, description="Latitude in decimal degrees"),
    longitude: Optional[float] = Query(None, description="Longitude in decimal degrees"),
) -> Dict[str, Any]:
    resolved_name: Optional[str] = None
    resolved_lat: Optional[float] = latitude
    resolved_lon: Optional[float] = longitude

    if query:
        resolution = geocode_query(query)
        if not resolution or resolution.get("latitude") is None or resolution.get("longitude") is None:
            raise HTTPException(status_code=404, detail="Location not found")
        resolved_lat = float(resolution["latitude"])
        resolved_lon = float(resolution["longitude"])
        resolved_name = resolve_display_name(resolution)

    if resolved_lat is None or resolved_lon is None:
        raise HTTPException(status_code=400, detail="Provide either a query or both latitude and longitude")

    try:
        snapshot = fetch_current_aqi(float(resolved_lat), float(resolved_lon))
    except AQIFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    payload: Dict[str, Any] = {
        "latitude": resolved_lat,
        "longitude": resolved_lon,
        **snapshot,
    }
    if resolved_name:
        payload["location_name"] = resolved_name

    return payload


class QuizSubmission(BaseModel):
    health_sensitivities: List[str] = Field(default_factory=list, alias="healthSensitivities")
    activity_type: Optional[str] = Field(default=None, alias="activityType")
    audience: Optional[str] = None
    interests: List[str] = Field(default_factory=list)
    phone_number: Optional[str] = Field(default=None, alias="phoneNumber")
    region: str = Field(alias="region")
    location_name: Optional[str] = Field(default=None, alias="locationName")
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        allow_population_by_field_name = True


def _load_quiz_responses() -> List[Dict[str, Any]]:
    if QUIZ_DATA_PATH.exists():
        try:
            with QUIZ_DATA_PATH.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
                if isinstance(data, list):
                    return data
        except json.JSONDecodeError:
            # If the file is corrupt, start fresh but preserve the original content for debugging.
            corrupt_path = QUIZ_DATA_PATH.with_suffix(".corrupt")
            try:
                QUIZ_DATA_PATH.rename(corrupt_path)
            except FileExistsError:
                corrupt_path.unlink()
                QUIZ_DATA_PATH.rename(corrupt_path)
    return []


def _append_quiz_response(entry: Dict[str, Any]) -> None:
    QUIZ_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with QUIZ_LOCK:
        data = _load_quiz_responses()
        data.append(entry)
        with QUIZ_DATA_PATH.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)


def _load_twilio_send_count() -> int:
    if TWILIO_COUNT_PATH.exists():
        try:
            with TWILIO_COUNT_PATH.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
                if isinstance(payload, dict) and isinstance(payload.get("count"), int):
                    return payload["count"]
                if isinstance(payload, int):
                    return payload
        except json.JSONDecodeError:
            logger.warning("Twilio send count file corrupt; resetting to zero")
    return 0


def _save_twilio_send_count(count: int) -> None:
    TWILIO_COUNT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TWILIO_COUNT_PATH.open("w", encoding="utf-8") as handle:
        json.dump({"count": count}, handle, indent=2)


def _should_send_twilio_sms() -> bool:
    return _load_twilio_send_count() < 100


def _increment_twilio_count() -> None:
    current = _load_twilio_send_count()
    _save_twilio_send_count(current + 1)


def _twilio_client() -> Optional[TwilioClient]:
    sid, token, _ = _twilio_config()
    if TwilioClient is None:
        logger.info("Twilio SDK not available; skipping SMS send")
        return None
    if not sid or not token:
        logger.info("Twilio credentials not configured; skipping SMS send")
        return None
    try:
        return TwilioClient(sid, token)
    except TwilioException as exc:
        logger.error("Failed to instantiate Twilio client: %s", exc)
        return None


def send_quiz_confirmation_sms(phone_number: str, region: str) -> Optional[str]:
    if not phone_number.strip():
        return "Missing phone number"
    if not _should_send_twilio_sms():
        logger.warning("Twilio send limit reached; not sending SMS")
        return "Send limit reached"

    client = _twilio_client()
    if client is None:
        return "Twilio not configured"

    body = (
        "Thank you for subscribing! We will send you notifications for your region "
        f"{region.strip() or 'your area'}."
    )

    try:
        _, _, from_number = _twilio_config()
        client.messages.create(body=body, from_=from_number, to=phone_number)
        _increment_twilio_count()
        logger.info("Sent Twilio confirmation to %s for region %s", phone_number, region)
        return None
    except TwilioException as exc:
        logger.error("Twilio send failed for %s: %s", phone_number, exc)
        return str(exc)


@app.post("/quiz/responses")
def submit_quiz_response(payload: QuizSubmission) -> Dict[str, Any]:
    timestamp = datetime.utcnow().isoformat() + "Z"
    cleaned = {
        "health_sensitivities": payload.health_sensitivities,
        "activity_type": payload.activity_type,
        "audience": payload.audience,
        "interests": payload.interests,
        "phone_number": payload.phone_number,
        "region": payload.region,
        "location_name": payload.location_name or payload.region,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "submitted_at": timestamp,
    }

    logger.info("Quiz submission received: %s", cleaned)
    _append_quiz_response(cleaned)

    response: Dict[str, Any] = {"status": "ok", "submitted_at": timestamp}
    response["sms"] = {"status": "skipped", "reason": "Temporarily disabled"}

    try:
        if payload.latitude is not None and payload.longitude is not None:
            response["insights"] = generate_insights(
                latitude=float(payload.latitude),
                longitude=float(payload.longitude),
                user_profile={
                    "health_sensitivity": payload.health_sensitivities,
                    "activity_type": payload.activity_type,
                    "audience": payload.audience,
                    "interest": payload.interests,
                },
                rain_mm=None,
            )
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Failed to generate insights: %s", exc)
        response["insights"] = {"status": "error", "message": "Could not generate insights."}

    return response


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
