"""Utilities for loading Open-Meteo CSV exports."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

AGGREGATOR_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = AGGREGATOR_ROOT.parent / "openmeteo" / "data"
BASE_COLUMNS = {"location_name", "time"}
PROVIDER_NAME = "Open-Meteo"

LOCATION_CATALOG: Dict[str, Dict[str, Any]] = {
    "oshawa": {
        "slug": "oshawa",
        "latitude": 43.905249,
        "longitude": -78.86109,
        "location_name": "Oshawa",
    },
    "toronto": {
        "slug": "toronto",
        "latitude": 43.647064,
        "longitude": -79.374389,
        "location_name": "Toronto",
    },
    "scarborough": {
        "slug": "scarborough",
        "latitude": 43.786553,
        "longitude": -79.307373,
        "location_name": "Scarborough",
    },
    "north_york": {
        "slug": "north_york",
        "latitude": 43.781385,
        "longitude": -79.425984,
        "location_name": "North York",
    },
    "ajax": {
        "slug": "ajax",
        "latitude": 43.878928,
        "longitude": -79.031005,
        "location_name": "Ajax",
    },
}

PARAMETER_UNITS: Dict[str, str] = {
    "temperature_2m": "degC",
    "relative_humidity_2m": "%",
    "rain": "mm",
    "wind_speed_120m": "m/s",
    "wind_speed_80m": "m/s",
    "wind_speed_40m": "m/s",
    "wind_speed_10m": "m/s",
    "wind_direction_10m": "deg",
    "wind_direction_40m": "deg",
    "wind_direction_80m": "deg",
    "wind_direction_120m": "deg",
    "snowfall": "cm",
    "pm10": "ug/m3",
    "pm2_5": "ug/m3",
    "ozone": "ug/m3",
    "uv_index": "index",
    "dust": "ug/m3",
    "carbon_dioxide": "ppm",
    "nitrogen_dioxide": "ug/m3",
    "sulphur_dioxide": "ug/m3",
}


def available_location_files() -> Dict[str, Path]:
    if not DATA_DIR.exists():
        return {}
    return {
        path.stem: path
        for path in DATA_DIR.glob("*.csv")
        if path.is_file()
    }


def _read_location_frame(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def list_parameters(slug: str) -> Optional[List[str]]:
    files = available_location_files()
    path = files.get(slug)
    if path is None:
        return None
    frame = pd.read_csv(path, nrows=0)
    return [column for column in frame.columns if column not in BASE_COLUMNS]


def load_location_metadata() -> List[Dict[str, Any]]:
    metadata: List[Dict[str, Any]] = []
    for slug, path in available_location_files().items():
        frame = _read_location_frame(path)
        parameters = [column for column in frame.columns if column not in BASE_COLUMNS]
        catalog_entry = LOCATION_CATALOG.get(slug, {})

        location_name: Optional[str] = None
        if not frame.empty and "location_name" in frame.columns:
            value = frame.iloc[0].get("location_name")
            if isinstance(value, str) and value.strip():
                location_name = value.strip()
            elif pd.notna(value):
                location_name = str(value)

        metadata.append(
            {
                "slug": slug,
                "location_name": location_name or catalog_entry.get("location_name"),
                "latitude": catalog_entry.get("latitude"),
                "longitude": catalog_entry.get("longitude"),
                "parameters": parameters,
                "filename": path.name,
            }
        )
    return metadata


def _coerce_records(frame: pd.DataFrame, parameter: str, slug: str) -> List[Dict[str, Any]]:
    if parameter not in frame.columns:
        return []

    series = frame[["time", "location_name", parameter]].copy()
    series.rename(columns={"time": "datetimeLocal", parameter: "value"}, inplace=True)
    series["parameter"] = parameter
    series["unit"] = PARAMETER_UNITS.get(parameter)
    series["provider"] = PROVIDER_NAME
    series["location_id"] = slug
    series["datetimeUtc"] = None

    # Replace inf/-inf with NaN then with None for JSON serialization.
    series.replace([np.inf, -np.inf], np.nan, inplace=True)
    series = series.astype(object)
    series = series.where(pd.notnull(series), None)

    records: List[Dict[str, Any]] = series.to_dict(orient="records")
    return records


def load_parameter_records(slug: str, parameter: str) -> Optional[List[Dict[str, Any]]]:
    files = available_location_files()
    path = files.get(slug)
    if path is None:
        return None
    frame = _read_location_frame(path)
    return _coerce_records(frame, parameter, slug)


def filter_records_by_date(records: Iterable[Dict[str, Any]], date: str) -> List[Dict[str, Any]]:
    prefix = str(date)
    return [
        record
        for record in records
        if isinstance(record.get("datetimeLocal"), str)
        and record["datetimeLocal"].startswith(prefix)
    ]
