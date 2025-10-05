from fastapi import FastAPI
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import pandas as pd
import uvicorn

BASE_DIR = Path(__file__).resolve().parent
TRANSFORMED_DIR = BASE_DIR.parent / "openaq" / "transformed"
LOCATIONS_PATH = TRANSFORMED_DIR / "locations.json"

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

def _load_locations() -> Dict[str, Any]:
    with LOCATIONS_PATH.open() as f:
        return json.load(f)


def _get_location_name(location_id: str, location: Dict[str, Any]) -> Optional[str]:
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
                # If file exists but no name found continue to next file
        except OSError:
            continue

    # Fall back to placeholder if we cannot resolve a name
    return None


def _resolve_parameter_file(location: Dict[str, Any], parameter: str) -> Optional[str]:
    for file_name in location.get("files", []):
        candidate = file_name.split("_")[-1].split(".")[0]
        if candidate == parameter:
            return file_name
    return None


def _load_parameter_records(file_name: str) -> List[Dict[str, Any]]:
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


@app.get("/locations")
def get_locations():
    locations = _load_locations()

    enriched: Dict[str, Any] = {}
    for location_id, location in locations.items():
        name = _get_location_name(location_id, location)
        enriched[location_id] = {
            **location,
            "location_name": name,
        }

    return enriched


@app.get("/locations/{location_id}")
def get_location_parameters(location_id: str):
    locations = _load_locations()

    if location_id not in locations:
        return {"error": "Location not found"}

    parameters: List[str] = []
    seen_parameters = set()

    for file_name in locations[location_id].get("files", []):
        parameter = file_name.split("_")[-1].split(".")[0]
        if parameter not in seen_parameters:
            parameters.append(parameter)
            seen_parameters.add(parameter)

    return parameters


@app.get("/locations/{location_id}/{parameter}")
def get_location_parameter(location_id: str, parameter: str):
    locations = _load_locations()

    if location_id not in locations:
        return {"error": "Location not found"}

    file_name = _resolve_parameter_file(locations[location_id], parameter)
    if not file_name:
        return {"error": "Parameter not found"}

    return _load_parameter_records(file_name)


@app.get("/locations/{location_id}/{parameter}/{date}")
def get_location_parameter_for_date(location_id: str, parameter: str, date: str):
    locations = _load_locations()

    if location_id not in locations:
        return {"error": "Location not found"}

    file_name = _resolve_parameter_file(locations[location_id], parameter)
    if not file_name:
        return {"error": "Parameter not found"}

    records = _load_parameter_records(file_name)
    filtered_records = [
        record
        for record in records
        if isinstance(record.get("datetimeLocal"), str)
        and record["datetimeLocal"].startswith(date)
    ]

    return filtered_records

def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
