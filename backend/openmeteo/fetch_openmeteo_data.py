"""Fetch hourly Open-Meteo data for predefined GTA locations and export per-location CSVs."""
from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import requests

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
FORECAST_PARAMS = {
    "hourly": (
        "temperature_2m,relative_humidity_2m,rain,wind_speed_120m,wind_speed_80m,"
        "wind_speed_40m,wind_speed_10m,wind_direction_10m,wind_direction_40m,"
        "wind_direction_80m,wind_direction_120m,snowfall"
    ),
    "models": "gem_seamless",
    "timezone": "America/New_York",
    "past_days": 60,
    "forecast_days": 3,
}

AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
AIR_QUALITY_PARAMS = {
    "hourly": "pm10,pm2_5,ozone,uv_index,dust,carbon_dioxide,nitrogen_dioxide,sulphur_dioxide",
    "timezone": "America/New_York",
    "past_days": 60,
    "forecast_days": 3,
}

LOCATIONS: Tuple[Dict[str, Any], ...] = (
    {
        "slug": "oshawa",
        "location_name": "Oshawa",
        "latitude": 43.905249,
        "longitude": -78.86109,
    },
    {
        "slug": "toronto",
        "location_name": "Toronto",
        "latitude": 43.647064,
        "longitude": -79.374389,
    },
    {
        "slug": "scarborough",
        "location_name": "Scarborough",
        "latitude": 43.786553,
        "longitude": -79.307373,
    },
    {
        "slug": "north_york",
        "location_name": "North York",
        "latitude": 43.781385,
        "longitude": -79.425984,
    },
    {
        "slug": "ajax",
        "location_name": "Ajax",
        "latitude": 43.878928,
        "longitude": -79.031005,
    },
)

OUTPUT_DIRNAME = "data"
TIME_FIELD = "time"
FORECAST_FIELDS = (
    "temperature_2m",
    "relative_humidity_2m",
    "rain",
    "wind_speed_120m",
    "wind_speed_80m",
    "wind_speed_40m",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_direction_40m",
    "wind_direction_80m",
    "wind_direction_120m",
    "snowfall",
)
AIR_QUALITY_FIELDS = (
    "pm10",
    "pm2_5",
    "ozone",
    "uv_index",
    "dust",
    "carbon_dioxide",
    "nitrogen_dioxide",
    "sulphur_dioxide",
)
ALL_FIELDS = (TIME_FIELD,) + FORECAST_FIELDS + AIR_QUALITY_FIELDS


def _fetch_hourly_dataset(
    url: str,
    base_params: Dict[str, object],
    location: Dict[str, Any],
    required_fields: Tuple[str, ...],
    dataset_label: str,
) -> Dict[str, List[Any]]:
    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        **base_params,
    }
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    payload = response.json()
    hourly = payload.get("hourly")
    if not hourly:
        raise ValueError(f"No hourly data returned for {location['location_name']} ({dataset_label})")

    missing_fields = [field for field in (TIME_FIELD,) + required_fields if field not in hourly]
    if missing_fields:
        raise ValueError(
            "Missing fields {} in hourly data for {} ({})".format(
                ", ".join(missing_fields), location["location_name"], dataset_label
            )
        )

    return hourly


def fetch_location_hourly(location: Dict[str, Any]) -> Tuple[Dict[str, List[Any]], Dict[str, List[Any]]]:
    forecast_hourly = _fetch_hourly_dataset(
        FORECAST_URL,
        FORECAST_PARAMS,
        location,
        FORECAST_FIELDS,
        "forecast",
    )
    air_quality_hourly = _fetch_hourly_dataset(
        AIR_QUALITY_URL,
        AIR_QUALITY_PARAMS,
        location,
        AIR_QUALITY_FIELDS,
        "air_quality",
    )
    return forecast_hourly, air_quality_hourly


def iter_hourly_rows(
    location: Dict[str, Any],
    forecast_hourly: Dict[str, Iterable],
    air_quality_hourly: Dict[str, Iterable],
) -> Iterable[Dict[str, object]]:
    rows_by_time: Dict[str, Dict[str, object]] = {}

    def _apply(hourly: Dict[str, Iterable], fields: Tuple[str, ...], label: str) -> None:
        times = hourly.get(TIME_FIELD)
        if isinstance(times, str) or times is None:
            raise ValueError(f"Missing '{TIME_FIELD}' series for {location['location_name']} ({label})")
        times_list = list(times)

        series_map: Dict[str, List[Any]] = {}
        for field in fields:
            if field not in hourly:
                continue
            series_list = list(hourly[field])
            if len(series_list) != len(times_list):
                sys.stderr.write(
                    f"Warning: uneven sequence lengths for {location['location_name']} ({label}:{field});"
                    f" truncating to {min(len(series_list), len(times_list))} records.\n"
                )
            series_map[field] = series_list

        for idx, timestamp in enumerate(times_list):
            row = rows_by_time.setdefault(
                timestamp,
                {"location_name": location["location_name"], TIME_FIELD: timestamp},
            )
            for field, series_list in series_map.items():
                if idx < len(series_list):
                    row[field] = series_list[idx]

    _apply(forecast_hourly, FORECAST_FIELDS, "forecast")
    _apply(air_quality_hourly, AIR_QUALITY_FIELDS, "air_quality")

    for timestamp in sorted(rows_by_time):
        yield rows_by_time[timestamp]


def write_csv(rows: Iterable[Dict[str, object]], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ("location_name",) + ALL_FIELDS
    with destination.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def filename_for_location(location: Dict[str, Any]) -> str:
    slug = str(location.get("slug") or location["location_name"].lower().replace(" ", "_"))
    return f"{slug}.csv"


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    output_dir = base_dir / OUTPUT_DIRNAME
    for location in LOCATIONS:
        forecast_hourly, air_quality_hourly = fetch_location_hourly(location)
        rows = list(iter_hourly_rows(location, forecast_hourly, air_quality_hourly))
        output_path = output_dir / filename_for_location(location)
        write_csv(rows, output_path)
        print(f"Wrote {len(rows)} rows to {output_path}")


if __name__ == "__main__":
    main()
