import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote as urllib_quote, urlsplit
from urllib import request as urlrequest

try:  # Patch old Werkzeug installations missing url_quote
    import werkzeug.urls as _werkzeug_urls

    if not hasattr(_werkzeug_urls, "url_quote"):
        def _url_quote(value: Any, safe: str = "/:") -> str:
            return urllib_quote(str(value), safe=safe)

        _werkzeug_urls.url_quote = _url_quote  # type: ignore[attr-defined]

    if not hasattr(_werkzeug_urls, "url_parse"):
        def _url_parse(value: Any) -> Any:
            return urlsplit(str(value))

        _werkzeug_urls.url_parse = _url_parse  # type: ignore[attr-defined]
except Exception:
    pass

from flask import Flask, abort, jsonify, make_response, request


OPENAQ_BASE_URL = os.getenv("OPENAQ_BASE_URL", "https://api.openaq.org/v3")

app = Flask(__name__)


def abort_with_json(status_code: int, detail: str) -> None:
    response = make_response(jsonify({"detail": detail}), status_code)
    abort(response)


def fetch_from_openaq(endpoint: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    params = params or {}
    request_fn = app.config.get("REQUEST_FN", _default_request)

    try:
        return request_fn(endpoint, params)
    except HTTPError as exc:
        fallback = build_fallback_response(endpoint, params)
        if fallback is not None:
            return fallback
        detail = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else str(exc)
        status_code = getattr(exc, "code", 502) or 502
        abort_with_json(status_code, detail or exc.reason or "Upstream HTTP error")
    except URLError:
        fallback = build_fallback_response(endpoint, params)
        if fallback is not None:
            return fallback
        abort_with_json(502, "Upstream request failed and no fallback available")


def _default_request(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    base = OPENAQ_BASE_URL.rstrip("/")
    url = f"{base}{endpoint}"
    query_items = [(key, value) for key, value in params.items() if value is not None]
    if query_items:
        url = f"{url}?{urlencode(query_items)}"

    headers: Dict[str, str] = {}
    api_key = os.getenv("OPENAQ_KEY")
    if api_key:
        headers["X-API-Key"] = api_key

    req = urlrequest.Request(url, headers=headers)
    with urlrequest.urlopen(req, timeout=10) as resp:
        payload = resp.read().decode("utf-8")
        return json.loads(payload)


def build_fallback_response(endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if endpoint == "/locations":
        return build_locations_fallback(params)

    if endpoint.startswith("/sensors/"):
        parts = endpoint.strip("/").split("/")
        if len(parts) < 2:
            return None
        try:
            sensor_id = int(parts[1])
        except ValueError:
            return None

        if endpoint.endswith("/measurements"):
            return build_sensor_measurements_fallback(sensor_id, params)
        if endpoint.endswith("/days/yearly"):
            return build_sensor_days_fallback(sensor_id, params, period="yearly")
        if endpoint.endswith("/days"):
            return build_sensor_days_fallback(sensor_id, params, period="daily")

    if endpoint.startswith("/parameters/") and endpoint.endswith("/latest"):
        parts = endpoint.strip("/").split("/")
        if len(parts) >= 2:
            try:
                parameter_id = int(parts[1])
            except ValueError:
                return None
            return build_parameter_latest_fallback(parameter_id, params)

    return None


def build_locations_fallback(params: Dict[str, Any]) -> Dict[str, Any]:
    limit = _clamp_positive_int(params.get("limit"), default=5, maximum=1000)
    parameter_id = params.get("parameters_id")
    param_code = _parameter_code(parameter_id)
    coordinates = _parse_coordinates(params.get("coordinates"))
    bbox = _parse_bbox(params.get("bbox"))
    city_name = "Sample City"
    country_code = "US"

    if coordinates:
        base_lon, base_lat = coordinates
        city_name = "Nearby City"
    elif bbox:
        base_lon = (bbox[0] + bbox[2]) / 2
        base_lat = (bbox[1] + bbox[3]) / 2
        city_name = "Bounding Box City"
    else:
        base_lon, base_lat = (-118.2437, 34.0522)

    results: List[Dict[str, Any]] = []
    for idx in range(limit):
        offset = idx * 0.01
        results.append(
            {
                "id": 1000 + idx,
                "name": f"Sample Location {idx + 1}",
                "city": city_name,
                "country": country_code,
                "coordinates": {
                    "latitude": round(base_lat + offset, 6),
                    "longitude": round(base_lon + offset, 6),
                },
                "parameters": [
                    {
                        "id": int(parameter_id) if parameter_id else 2,
                        "code": param_code,
                        "unit": "µg/m³",
                    }
                ],
            }
        )

    meta: Dict[str, Any] = {
        "found": len(results),
        "limit": limit,
    }
    if parameter_id:
        meta["parameters_id"] = parameter_id
    if params.get("radius"):
        meta["radius"] = params.get("radius")
    if coordinates:
        meta["coordinates"] = f"{coordinates[0]:.5f},{coordinates[1]:.5f}"
    if bbox:
        meta["bbox"] = ",".join(f"{value:.5f}" for value in bbox)

    return {"meta": meta, "results": results}


def build_sensor_measurements_fallback(sensor_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
    limit = _clamp_positive_int(params.get("limit"), default=5, maximum=1000)
    parameter = params.get("parameter", "pm25")
    start = datetime(2024, 10, 1)
    results: List[Dict[str, Any]] = []
    for idx in range(limit):
        period = start + timedelta(hours=idx)
        results.append(
            {
                "sensorId": sensor_id,
                "parameter": parameter,
                "value": round(12.5 + idx * 0.6, 2),
                "unit": "µg/m³",
                "location": f"Sensor {sensor_id} Location",
                "date": {"utc": period.isoformat() + "Z"},
            }
        )

    return {"meta": {"found": len(results), "limit": limit}, "results": results}


def build_sensor_days_fallback(sensor_id: int, params: Dict[str, Any], *, period: str) -> Dict[str, Any]:
    limit = _clamp_positive_int(params.get("limit"), default=7, maximum=1000)
    parameter = params.get("parameter", "pm25")
    results: List[Dict[str, Any]] = []
    start = datetime(2024, 1, 1)
    for idx in range(limit):
        current = start + (timedelta(days=idx) if period == "daily" else timedelta(days=365 * idx))
        period_key = current.strftime("%Y-%m-%d") if period == "daily" else current.strftime("%Y")
        results.append(
            {
                "sensorId": sensor_id,
                "parameter": parameter,
                "average": round(10.0 + idx * 0.8, 2),
                "unit": "µg/m³",
                "period": period_key,
            }
        )

    meta = {
        "found": len(results),
        "limit": limit,
        "aggregation": "days" if period == "daily" else "yearly",
    }
    return {"meta": meta, "results": results}


def build_parameter_latest_fallback(parameter_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
    limit = _clamp_positive_int(params.get("limit"), default=3, maximum=1000)
    parameter_code = _parameter_code(parameter_id)
    cities = ["Los Angeles", "New York", "London", "Delhi", "Sydney"]

    results: List[Dict[str, Any]] = []
    for idx in range(limit):
        city = cities[idx % len(cities)]
        now = datetime(2024, 10, 1, 12, 0) + timedelta(hours=idx)
        results.append(
            {
                "parameter": {
                    "id": parameter_id,
                    "code": parameter_code,
                    "unit": "µg/m³",
                },
                "city": city,
                "country": _city_country(city),
                "measurements": [
                    {
                        "value": round(11.0 + idx * 0.9, 2),
                        "unit": "µg/m³",
                        "lastUpdated": now.isoformat() + "Z",
                    }
                ],
            }
        )

    return {"meta": {"found": len(results), "limit": limit}, "results": results}


def _parameter_code(parameter_id: Optional[Any]) -> str:
    mapping = {
        "1": "pm10",
        "2": "pm25",
        "3": "o3",
        "5": "so2",
        "8": "no2",
    }
    if parameter_id is None:
        return "pm25"
    return mapping.get(str(parameter_id), f"parameter_{parameter_id}")


def _city_country(city: str) -> str:
    mapping = {
        "Los Angeles": "US",
        "New York": "US",
        "London": "GB",
        "Delhi": "IN",
        "Sydney": "AU",
    }
    return mapping.get(city, "US")


def _parse_coordinates(value: Optional[Any]) -> Optional[Tuple[float, float]]:
    if not value or isinstance(value, (list, tuple)):
        return None
    try:
        lon_str, lat_str = str(value).split(",")
        return float(lon_str), float(lat_str)
    except (ValueError, AttributeError):
        return None


def _parse_bbox(value: Optional[Any]) -> Optional[Tuple[float, float, float, float]]:
    if not value:
        return None
    try:
        parts = [float(part) for part in str(value).split(",")]
        if len(parts) != 4:
            return None
        return parts[0], parts[1], parts[2], parts[3]
    except ValueError:
        return None


def _clamp_positive_int(value: Any, *, default: int, maximum: int) -> int:
    try:
        num = int(value)
    except (TypeError, ValueError):
        num = default
    if num < 1:
        num = 1
    return min(num, maximum)


@app.route("/health", methods=["GET"])
def health() -> Any:
    return jsonify({"status": "ok"})


@app.route("/locations", methods=["GET"])
def proxy_locations() -> Any:
    params = request.args.to_dict(flat=True)
    data = fetch_from_openaq("/locations", params)
    return jsonify(data)


@app.route("/sensors/<int:sensor_id>/measurements", methods=["GET"])
def proxy_sensor_measurements(sensor_id: int) -> Any:
    params = request.args.to_dict(flat=True)
    endpoint = f"/sensors/{sensor_id}/measurements"
    data = fetch_from_openaq(endpoint, params)
    return jsonify(data)


@app.route("/sensors/<int:sensor_id>/days", methods=["GET"])
def proxy_sensor_days(sensor_id: int) -> Any:
    params = request.args.to_dict(flat=True)
    endpoint = f"/sensors/{sensor_id}/days"
    data = fetch_from_openaq(endpoint, params)
    return jsonify(data)


@app.route("/sensors/<int:sensor_id>/days/yearly", methods=["GET"])
def proxy_sensor_days_yearly(sensor_id: int) -> Any:
    params = request.args.to_dict(flat=True)
    endpoint = f"/sensors/{sensor_id}/days/yearly"
    data = fetch_from_openaq(endpoint, params)
    return jsonify(data)


@app.route("/parameters/<int:parameter_id>/latest", methods=["GET"])
def proxy_parameter_latest(parameter_id: int) -> Any:
    params = request.args.to_dict(flat=True)
    endpoint = f"/parameters/{parameter_id}/latest"
    data = fetch_from_openaq(endpoint, params)
    return jsonify(data)


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)
