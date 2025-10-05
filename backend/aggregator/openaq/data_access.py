"""Data access helpers for OpenAQ-derived datasets."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

AGGREGATOR_ROOT = Path(__file__).resolve().parents[1]
TRANSFORMED_DIR = AGGREGATOR_ROOT.parent / "openaq" / "transformed"
LOCATIONS_PATH = TRANSFORMED_DIR / "locations.json"


def load_locations() -> Dict[str, Any]:
    with LOCATIONS_PATH.open() as handle:
        return json.load(handle)


def get_location_name(location: Dict[str, Any]) -> Optional[str]:
    for file_name in location.get("files", []):
        csv_path = TRANSFORMED_DIR / file_name
        if not csv_path.exists():
            continue
        try:
            with csv_path.open(newline="") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    candidate = row.get("location_name")
                    if candidate:
                        return str(candidate)
        except OSError:
            continue
    return None


def list_parameters(location: Dict[str, Any]) -> List[str]:
    parameters: List[str] = []
    seen: set[str] = set()
    for file_name in location.get("files", []):
        parameter = file_name.split("_")[-1].split(".")[0]
        if parameter not in seen:
            parameters.append(parameter)
            seen.add(parameter)
    return parameters


def resolve_parameter_file(location: Dict[str, Any], parameter: str) -> Optional[str]:
    for file_name in location.get("files", []):
        candidate = file_name.split("_")[-1].split(".")[0]
        if candidate == parameter:
            return file_name
    return None


def load_parameter_records(file_name: str) -> List[Dict[str, Any]]:
    csv_path = TRANSFORMED_DIR / file_name
    df = pd.read_csv(csv_path)
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.astype(object)
    df = df.where(pd.notnull(df), None)
    records: List[Dict[str, Any]] = df.to_dict(orient="records")
    for record in records:
        for key in ("datetimeUtc", "datetimeLocal"):
            value = record.get(key)
            if isinstance(value, pd.Timestamp):
                record[key] = value.isoformat()
    return records


def filter_records_by_date(records: Iterable[Dict[str, Any]], date: str) -> List[Dict[str, Any]]:
    prefix = str(date)
    return [
        record
        for record in records
        if isinstance(record.get("datetimeLocal"), str)
        and record["datetimeLocal"].startswith(prefix)
    ]
