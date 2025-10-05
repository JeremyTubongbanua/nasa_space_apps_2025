"""FastAPI router for Open-Meteo datasets."""
from __future__ import annotations

from typing import Any, Dict, List, Union

from fastapi import APIRouter

from . import data_access as dao

router = APIRouter(prefix="/openmeteo", tags=["openmeteo"])


@router.get("/locations")
def list_locations() -> List[Dict[str, Any]]:
    return dao.load_location_metadata()


@router.get("/locations/{location_slug}/parameters")
def get_location_parameters(location_slug: str) -> Union[List[str], Dict[str, str]]:
    parameters = dao.list_parameters(location_slug)
    if parameters is None:
        return {"error": "Location not found"}
    return parameters


@router.get("/locations/{location_slug}/parameters/{parameter}")
def get_location_parameter(location_slug: str, parameter: str) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    records = dao.load_parameter_records(location_slug, parameter)
    if records is None:
        return {"error": "Location not found"}
    return records


@router.get("/locations/{location_slug}/parameters/{parameter}/{date}")
def get_location_parameter_for_date(
    location_slug: str,
    parameter: str,
    date: str,
) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    records = dao.load_parameter_records(location_slug, parameter)
    if records is None:
        return {"error": "Location not found"}
    return dao.filter_records_by_date(records, date)
