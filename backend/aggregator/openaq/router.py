"""FastAPI router exposing OpenAQ-backed endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Union

from fastapi import APIRouter

from . import data_access as dao

router = APIRouter(tags=["openaq"])


@router.get("/locations")
def get_locations() -> Dict[str, Any]:
    locations = dao.load_locations()
    enriched: Dict[str, Any] = {}
    for location_id, location in locations.items():
        enriched[location_id] = {
            **location,
            "location_name": dao.get_location_name(location),
        }
    return enriched


@router.get("/locations/{location_id}")
def get_location_parameters(location_id: str) -> Union[List[str], Dict[str, str]]:
    locations = dao.load_locations()
    if location_id not in locations:
        return {"error": "Location not found"}
    return dao.list_parameters(locations[location_id])


@router.get("/locations/{location_id}/{parameter}")
def get_location_parameter(location_id: str, parameter: str) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    locations = dao.load_locations()
    if location_id not in locations:
        return {"error": "Location not found"}
    file_name = dao.resolve_parameter_file(locations[location_id], parameter)
    if not file_name:
        return {"error": "Parameter not found"}
    return dao.load_parameter_records(file_name)


@router.get("/locations/{location_id}/{parameter}/{date}")
def get_location_parameter_for_date(
    location_id: str,
    parameter: str,
    date: str,
) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    locations = dao.load_locations()
    if location_id not in locations:
        return {"error": "Location not found"}
    file_name = dao.resolve_parameter_file(locations[location_id], parameter)
    if not file_name:
        return {"error": "Parameter not found"}
    records = dao.load_parameter_records(file_name)
    return dao.filter_records_by_date(records, date)
