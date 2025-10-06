"""Generate personalized air-quality insights based on sensor data and quiz inputs."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import atan2, cos, radians, sin, sqrt
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    from .openaq import data_access as openaq_dao
except ImportError:  # pragma: no cover - support script execution
    import importlib.util
    from pathlib import Path

    module_path = Path(__file__).resolve().parent / "openaq" / "data_access.py"
    spec = importlib.util.spec_from_file_location("_openaq_data_access", module_path)
    if spec is None or spec.loader is None:
        raise
    openaq_dao = importlib.util.module_from_spec(spec)  # type: ignore
    spec.loader.exec_module(openaq_dao)  # type: ignore


SEVERITY_ORDER = [
    "good",
    "fair",
    "sens_caution",
    "caution",
    "high",
    "very_high",
    "extreme",
]

POLLUTANT_BINS = {
    "PM25": ([0, 10, 15, 25, 35, 55.5], ["good", "fair", "caution", "high", "very_high", "extreme"]),
    "O3": ([0, 50, 60, 70, 85, 105], ["good", "fair", "caution", "high", "very_high", "extreme"]),
    "NO2": ([0, 10, 25, 50, 100, 200], ["good", "sens_caution", "caution", "high", "very_high", "extreme"]),
    "SO2": ([0, 5, 10, 20, 50, 75], ["good", "sens_caution", "caution", "high", "very_high", "extreme"]),
}

POLLUTANT_PARAMS = {
    "PM25": "pm25",
    "O3": "o3",
    "NO2": "no2",
    "SO2": "so2",
}


@dataclass
class Measurement:
    value: Optional[float]
    unit: Optional[str]
    timestamp: Optional[str]
    previous: Optional[float]


@dataclass
class SensorContext:
    sensor_id: str
    location_name: Optional[str]
    latitude: float
    longitude: float
    measurements: Dict[str, Measurement]


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    phi1, phi2 = radians(lat1), radians(lat2)
    d_phi = radians(lat2 - lat1)
    d_lambda = radians(lon2 - lon1)
    a = sin(d_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(d_lambda / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return radius * c


def _latest_measurement(file_name: str) -> Measurement:
    records = openaq_dao.load_parameter_records(file_name)
    if not records:
        return Measurement(None, None, None, None)

    records_sorted = sorted(
        (record for record in records if record.get("value") is not None),
        key=lambda rec: (rec.get("datetimeLocal") or rec.get("datetimeUtc") or ""),
    )
    if not records_sorted:
        return Measurement(None, None, None, None)

    latest = records_sorted[-1]
    previous = records_sorted[-2] if len(records_sorted) > 1 else None

    def _to_float(value: Any) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    latest_value = _to_float(latest.get("value"))
    previous_value = _to_float(previous.get("value")) if previous else None
    timestamp = latest.get("datetimeLocal") or latest.get("datetimeUtc")
    unit = latest.get("unit")
    return Measurement(latest_value, unit if isinstance(unit, str) else None, timestamp, previous_value)


def _nearest_openaq_sensor(latitude: float, longitude: float) -> Optional[SensorContext]:
    locations = openaq_dao.load_locations()
    nearest_id = None
    nearest_distance = float("inf")
    nearest_location: Optional[Dict[str, Any]] = None

    for location_id, location in locations.items():
        sensor_lat = location.get("latitude")
        sensor_lon = location.get("longitude")
        if not isinstance(sensor_lat, (int, float)) or not isinstance(sensor_lon, (int, float)):
            continue
        distance = _haversine_km(latitude, longitude, sensor_lat, sensor_lon)
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_id = location_id
            nearest_location = location

    if nearest_id is None or nearest_location is None:
        return None

    location_name = openaq_dao.get_location_name(nearest_location)
    measurements: Dict[str, Measurement] = {}
    for pollutant, parameter in POLLUTANT_PARAMS.items():
        file_name = openaq_dao.resolve_parameter_file(nearest_location, parameter)
        if not file_name:
            measurements[pollutant] = Measurement(None, None, None, None)
            continue
        measurements[pollutant] = _latest_measurement(file_name)

    return SensorContext(
        sensor_id=str(nearest_id),
        location_name=location_name,
        latitude=float(nearest_location.get("latitude")),
        longitude=float(nearest_location.get("longitude")),
        measurements=measurements,
    )


def _tier(value: Optional[float], bins: Iterable[float], labels: Iterable[str]) -> str:
    if value is None:
        return "unknown"
    bins_list = list(bins)
    labels_list = list(labels)
    for boundary, label in zip(bins_list[1:], labels_list):
        if value < boundary:
            return label
    return labels_list[-1]


def _severity_rank(label: str) -> int:
    try:
        return SEVERITY_ORDER.index(label)
    except ValueError:
        return 0


def _direction(measurement: Measurement) -> str:
    if measurement.value is None:
        return "—"
    if measurement.previous is None:
        return "at current levels"
    delta = measurement.value - measurement.previous
    if abs(delta) < 0.5:
        return "holding steady"
    return "rising" if delta > 0 else "declining"


def _top_pollutants(severities: Dict[str, str], measurements: Dict[str, Measurement], limit: int = 2) -> List[str]:
    ranked = sorted(
        ((pollutant, severity) for pollutant, severity in severities.items() if severity != "unknown"),
        key=lambda item: _severity_rank(item[1]),
        reverse=True,
    )
    return [pollutant for pollutant, _ in ranked[:limit]]


def _best_window(no2: Optional[float], o3: Optional[float], pm25: Optional[float], rain: Optional[float]) -> str:
    if o3 is not None and o3 >= 70:
        return "early morning (before 9am) or evening (after 7pm)"
    if no2 is not None and no2 >= 10:
        return "outside of rush hours; late morning or mid-afternoon away from major roads"
    if pm25 is not None and pm25 >= 15 and (rain or 0) == 0:
        return "after tonight if rain arrives; otherwise keep outdoor sessions short"
    return "anytime"


def _interest_block(interest: str, *, top_pollutant: str, best_window: str) -> Optional[str]:
    if interest == "health_alerts":
        return f"Health alert: {top_pollutant} is driving today’s risk."
    if interest == "best_time_outdoors":
        return f"Best time outside: {best_window}."
    if interest == "weather_trends" or interest == "trends":
        return "Trend: Levels are expected to fluctuate with local weather — monitor updates through the day."
    if interest == "pollution_sources":
        hints = {
            "NO2": "Vehicle traffic and combustion sources",
            "PM25": "Fine particles from traffic, smoke, or industry",
            "O3": "Sunlight-driven ozone chemistry",
            "SO2": "Industrial or shipping sources",
        }
        source_hint = hints.get(top_pollutant, "Regional transport and local activity")
        return f"Likely sources: {source_hint}."
    return None


def _pollutant_display_name(pollutant: str) -> str:
    mapping = {
        "PM25": "PM₂.₅",
        "O3": "O₃",
        "NO2": "NO₂",
        "SO2": "SO₂",
    }
    return mapping.get(pollutant, pollutant)


def generate_insights(
    *,
    latitude: float,
    longitude: float,
    user_profile: Dict[str, Any],
    rain_mm: Optional[float] = None,
) -> Dict[str, Any]:
    sensor = _nearest_openaq_sensor(latitude, longitude)
    if sensor is None:
        return {"status": "error", "message": "No nearby sensors available."}

    severities: Dict[str, str] = {}
    for pollutant, (bins, labels) in POLLUTANT_BINS.items():
        measurement = sensor.measurements.get(pollutant)
        value = measurement.value if measurement else None
        severities[pollutant] = _tier(value, bins, labels)

    overall = max(severities.values(), key=_severity_rank) if severities else "unknown"
    top_pollutants = _top_pollutants(severities, sensor.measurements)
    dominant = top_pollutants[0] if top_pollutants else None

    health_sensitivity = set(user_profile.get("health_sensitivity") or [])
    activity_type = user_profile.get("activity_type")
    audience = user_profile.get("audience")
    interests = list(user_profile.get("interest") or [])

    sensitivity_flags = {
        "children_family": audience in {"family", "students"},
        "asthma": "asthma" in health_sensitivity,
        "heart": "heart_condition" in health_sensitivity,
        "outdoor_worker": activity_type == "work_outdoors",
    }

    measurements = sensor.measurements
    pm25_value = measurements.get("PM25").value if measurements.get("PM25") else None
    no2_value = measurements.get("NO2").value if measurements.get("NO2") else None
    o3_value = measurements.get("O3").value if measurements.get("O3") else None
    so2_value = measurements.get("SO2").value if measurements.get("SO2") else None

    advice: List[str] = []
    if no2_value is not None and no2_value >= 10 and (sensitivity_flags["children_family"] or sensitivity_flags["asthma"]):
        advice.append("Because you’re checking for kids, avoid stroller time near busy roads; choose parks or residential streets.")
        if sensitivity_flags["asthma"]:
            advice.append("If you have asthma, carry your reliever and avoid rush-hour corridors.")
    if pm25_value is not None and pm25_value >= 15 and sensitivity_flags["heart"]:
        advice.append("If you have a heart condition, keep exertion light and prefer indoor exercise today.")
    if o3_value is not None and o3_value >= 70 and activity_type in {"jogging", "cycling"}:
        advice.append("Shift runs to early morning or evening to avoid ozone peaks.")
    if sensitivity_flags["outdoor_worker"]:
        advice.append("Use regular breaks in cleaner indoor air and consider a well-fitting mask during high particle periods.")

    best_window = _best_window(no2_value, o3_value, pm25_value, rain_mm)
    interest_blocks: List[str] = []
    if dominant:
        for interest in interests:
            block = _interest_block(interest, top_pollutant=dominant, best_window=best_window)
            if block:
                interest_blocks.append(block)

    callouts: List[str] = []
    for pollutant in top_pollutants:
        measurement = measurements.get(pollutant)
        if not measurement or measurement.value is None:
            continue
        direction = _direction(measurement)
        unit = measurement.unit or ("µg/m³" if pollutant == "PM25" else "ppb")
        callouts.append(
            f"{_pollutant_display_name(pollutant)} {measurement.value:.1f} {unit} ({direction})."
        )

    severity_headline = {
        "good": "Air quality is good in {location}.",
        "fair": "Air quality is slightly reduced in {location}.",
        "sens_caution": "Air quality needs extra care for sensitive groups in {location}.",
        "caution": "Air quality requires caution in {location}.",
        "high": "Air quality is poor in {location} — limit exposure.",
        "very_high": "Air quality is very poor — reduce outdoor time.",
        "extreme": "Hazardous air quality — stay indoors if possible.",
    }.get(overall, "Air quality update for {location}.")

    timestamp = datetime.utcnow().isoformat() + "Z"

    sources = [
        {
            "label": "WHO Global Air Quality Guidelines (2021)",
            "url": "https://www.who.int/publications/i/item/9789240034228",
        },
        {
            "label": "U.S. EPA National Ambient Air Quality Standards",
            "url": "https://www.epa.gov/naaqs",
        },
        {
            "label": "OpenAQ Sensor Network",
            "url": "https://openaq.org/",
        },
    ]

    payload = {
        "status": "ok",
        "generated_at": timestamp,
        "overall_severity": overall,
        "dominant_pollutant": _pollutant_display_name(dominant) if dominant else None,
        "headline": severity_headline.format(location=sensor.location_name or "your area"),
        "callouts": callouts,
        "advice": advice,
        "interest": interest_blocks,
        "best_window": best_window,
        "footers": [
            "Units: NO₂/O₃/SO₂ in ppb; PM₂.₅ in µg/m³.",
            "Thresholds reflect WHO (2021) & U.S. EPA guidance.",
        ],
        "sensor": {
            "id": sensor.sensor_id,
            "location_name": sensor.location_name,
            "latitude": sensor.latitude,
            "longitude": sensor.longitude,
            "measurements": {
                pollutant: {
                    "value": measurement.value,
                    "unit": measurement.unit,
                    "timestamp": measurement.timestamp,
                    "previous": measurement.previous,
                }
                for pollutant, measurement in sensor.measurements.items()
            },
        },
        "sources": sources,
    }

    return payload


__all__ = ["generate_insights"]
