"""Utility script to cache recent Toronto OpenAQ data.

The script queries the local Flask proxy for multiple endpoints and stores
flattened CSV files under ``data/`` so downstream notebooks or dashboards can
re-use the payloads without re-scraping the API each time.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


BASE_URL = os.getenv("OPENAQ_PROXY_URL", "http://127.0.0.1:8000")
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

TORONTO_COORDS = (-79.3832, 43.6532)
SEARCH_RADIUS_METERS = 25_000
MAX_DAYS = 5

# Known PM2.5 monitor close to Toronto core taken from latest OpenAQ pulls.
TORONTO_SENSOR_IDS = [10017217]


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)

    locations = fetch_locations()
    write_locations_csv(locations, DATA_DIR / "toronto_locations.csv")

    for sensor_id in TORONTO_SENSOR_IDS:
        fetch_and_write_recent_measurements(sensor_id)
        fetch_and_write_daily_summary(sensor_id)


def fetch_locations() -> List[Mapping[str, Any]]:
    params = {
        "coordinates": f"{TORONTO_COORDS[0]},{TORONTO_COORDS[1]}",
        "radius": SEARCH_RADIUS_METERS,
        "limit": 100,
    }
    payload = get_json("/locations", params)
    return payload.get("results", [])


def fetch_and_write_recent_measurements(sensor_id: int) -> None:
    all_rows: List[MutableMapping[str, Any]] = []
    today = date.today()

    for offset in range(MAX_DAYS):
        day = today - timedelta(days=offset)
        start_dt = datetime.combine(day, time.min, tzinfo=timezone.utc)
        end_dt = datetime.combine(day, time.max, tzinfo=timezone.utc)
        params = {
            "date_from": isoformat_utc(start_dt),
            "date_to": isoformat_utc(end_dt),
            "limit": 1000,
            "parameter": "pm25",
        }
        payload = get_json(f"/sensors/{sensor_id}/measurements", params)
        results = payload.get("results", [])

        normalized = [normalize_measurement(row, default_sensor_id=sensor_id) for row in results]
        filtered = [row for row in normalized if row["timestamp_utc"] or row["datetime_from_utc"]]

        csv_path = DATA_DIR / f"sensor_{sensor_id}_measurements_{day.isoformat()}.csv"
        write_csv(filtered, csv_path, measurement_headers())
        all_rows.extend(filtered)

    combined_path = DATA_DIR / f"sensor_{sensor_id}_measurements_recent.csv"
    write_csv(sorted(all_rows, key=_measurement_sort_key, reverse=True), combined_path, measurement_headers())


def fetch_and_write_daily_summary(sensor_id: int) -> None:
    params = {
        "parameter": "pm25",
        "limit": MAX_DAYS,
    }
    payload = get_json(f"/sensors/{sensor_id}/days", params)
    rows = [normalize_daily(entry, default_sensor_id=sensor_id) for entry in payload.get("results", [])]

    csv_path = DATA_DIR / f"sensor_{sensor_id}_daily_summary.csv"
    write_csv(rows, csv_path, daily_headers())


def get_json(endpoint: str, params: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    base = BASE_URL.rstrip("/") + "/"
    url = urljoin(base, endpoint.lstrip("/"))
    cleaned_params = {key: value for key, value in (params or {}).items() if value not in (None, "")}
    if cleaned_params:
        url = f"{url}?{urlencode(cleaned_params)}"

    req = Request(url, headers={"Accept": "application/json"})

    try:
        with urlopen(req) as resp:
            payload = resp.read().decode("utf-8")
    except HTTPError as exc:  # pragma: no cover - passthrough for CLI feedback
        detail = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else str(exc)
        raise RuntimeError(f"HTTP error {exc.code} for {url}: {detail}")
    except URLError as exc:  # pragma: no cover - passthrough for CLI feedback
        raise RuntimeError(f"Failed to reach {url}: {exc.reason}") from exc

    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON from {url}: {exc}") from exc


def write_locations_csv(results: Iterable[Mapping[str, Any]], output_path: Path) -> None:
    rows = [normalize_location(entry) for entry in results]
    write_csv(rows, output_path, location_headers())


def normalize_location(entry: Mapping[str, Any]) -> Dict[str, Any]:
    coordinates = entry.get("coordinates") or {}
    country = entry.get("country")
    country_code = country.get("code") if isinstance(country, Mapping) else country
    parameters = entry.get("parameters") or entry.get("sensors")

    parameter_ids: List[str] = []
    if isinstance(parameters, list):
        for item in parameters:
            code: Optional[Any] = None
            if isinstance(item, Mapping):
                parameter_meta = item.get("parameter") if isinstance(item.get("parameter"), Mapping) else item
                if isinstance(parameter_meta, Mapping):
                    code = (
                        parameter_meta.get("name")
                        or parameter_meta.get("code")
                        or parameter_meta.get("id")
                    )
                if not code:
                    code = item.get("code") or item.get("id")
            elif isinstance(item, str):
                code = item

            if code:
                parameter_ids.append(str(code))

    return {
        "location_id": entry.get("id"),
        "name": entry.get("name"),
        "city": entry.get("city") or entry.get("locality"),
        "country_code": country_code,
        "latitude": coordinates.get("latitude"),
        "longitude": coordinates.get("longitude"),
        "parameter_codes": ",".join(parameter_ids),
    }


def normalize_measurement(entry: Mapping[str, Any], *, default_sensor_id: Optional[int] = None) -> Dict[str, Any]:
    parameter = entry.get("parameter")
    if isinstance(parameter, Mapping):
        parameter_id = parameter.get("id") or parameter.get("code")
        parameter_name = parameter.get("name") or parameter.get("code")
        units = parameter.get("units")
    else:
        parameter_id = None
        parameter_name = parameter
        units = None

    coverage = entry.get("coverage") if isinstance(entry.get("coverage"), Mapping) else {}
    period = entry.get("period") if isinstance(entry.get("period"), Mapping) else {}

    return {
        "sensor_id": entry.get("sensorId")
        or entry.get("sensor_id")
        or entry.get("sensorsId")
        or default_sensor_id,
        "parameter_id": parameter_id,
        "parameter_name": parameter_name,
        "value": entry.get("value") or entry.get("measurement"),
        "unit": entry.get("unit") or units,
        "location": entry.get("location"),
        "timestamp_utc": extract_timestamp(entry.get("date")),
        "datetime_from_utc": extract_timestamp(period.get("datetimeFrom")),
        "datetime_to_utc": extract_timestamp(period.get("datetimeTo")),
        "period_label": period.get("label"),
        "period_interval": period.get("interval"),
        "coverage_expected_count": coverage.get("expectedCount"),
        "coverage_observed_count": coverage.get("observedCount"),
        "coverage_percent_complete": coverage.get("percentComplete"),
        "coverage_percent_coverage": coverage.get("percentCoverage"),
    }


def normalize_daily(entry: Mapping[str, Any], *, default_sensor_id: Optional[int] = None) -> Dict[str, Any]:
    parameter = entry.get("parameter")
    if isinstance(parameter, Mapping):
        parameter_id = parameter.get("id") or parameter.get("code")
        parameter_name = parameter.get("name") or parameter.get("code")
        units = parameter.get("units")
    else:
        parameter_id = None
        parameter_name = parameter
        units = None

    summary = entry.get("summary") if isinstance(entry.get("summary"), Mapping) else {}
    coverage = entry.get("coverage") if isinstance(entry.get("coverage"), Mapping) else {}

    return {
        "sensor_id": entry.get("sensorId")
        or entry.get("sensor_id")
        or entry.get("sensorsId")
        or default_sensor_id,
        "parameter_id": parameter_id,
        "parameter_name": parameter_name,
        "value": entry.get("value") or entry.get("average"),
        "unit": entry.get("unit") or units,
        "period": entry.get("period") or entry.get("period", {}),
        "period_start_utc": extract_timestamp(_ensure_mapping(entry.get("period")).get("datetimeFrom")),
        "period_end_utc": extract_timestamp(_ensure_mapping(entry.get("period")).get("datetimeTo")),
        "coverage_expected_count": coverage.get("expectedCount"),
        "coverage_observed_count": coverage.get("observedCount"),
        "coverage_percent_complete": coverage.get("percentComplete"),
        "coverage_percent_coverage": coverage.get("percentCoverage"),
        "summary_avg": summary.get("avg"),
        "summary_min": summary.get("min"),
        "summary_max": summary.get("max"),
        "summary_median": summary.get("median"),
        "summary_sd": summary.get("sd"),
        "summary_q02": summary.get("q02"),
        "summary_q25": summary.get("q25"),
        "summary_q75": summary.get("q75"),
        "summary_q98": summary.get("q98"),
    }


def write_csv(rows: Iterable[Mapping[str, Any]], output_path: Path, headers: List[str]) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in headers})


def isoformat_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def extract_timestamp(value: Any) -> Optional[str]:
    if not value:
        return None
    if isinstance(value, Mapping):
        if value.get("utc"):
            return value["utc"]
        if value.get("date"):
            return value["date"]
    if isinstance(value, (list, tuple)) and value:
        return extract_timestamp(value[0])
    if isinstance(value, str):
        return value
    return None


def _ensure_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def measurement_headers() -> List[str]:
    return [
        "sensor_id",
        "parameter_id",
        "parameter_name",
        "value",
        "unit",
        "location",
        "timestamp_utc",
        "datetime_from_utc",
        "datetime_to_utc",
        "period_label",
        "period_interval",
        "coverage_expected_count",
        "coverage_observed_count",
        "coverage_percent_complete",
        "coverage_percent_coverage",
    ]


def daily_headers() -> List[str]:
    return [
        "sensor_id",
        "parameter_id",
        "parameter_name",
        "value",
        "unit",
        "period",
        "period_start_utc",
        "period_end_utc",
        "coverage_expected_count",
        "coverage_observed_count",
        "coverage_percent_complete",
        "coverage_percent_coverage",
        "summary_avg",
        "summary_min",
        "summary_max",
        "summary_median",
        "summary_sd",
        "summary_q02",
        "summary_q25",
        "summary_q75",
        "summary_q98",
    ]


def location_headers() -> List[str]:
    return [
        "location_id",
        "name",
        "city",
        "country_code",
        "latitude",
        "longitude",
        "parameter_codes",
    ]


def _measurement_sort_key(row: Mapping[str, Any]) -> Any:
    """Sort by timestamp, falling back to period start."""

    return (
        row.get("timestamp_utc")
        or row.get("datetime_from_utc")
        or row.get("datetime_to_utc")
        or ""
    )


if __name__ == "__main__":  # pragma: no cover - manual execution
    try:
        main()
    except Exception as exc:  # pragma: no cover - surface error in CLI
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
