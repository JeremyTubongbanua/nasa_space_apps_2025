"""Fetch sensor details using a bounding box query."""

from __future__ import annotations

from urllib.parse import urlencode

from . import APIError, fetch_json_via_curl
from lib.constants import DEFAULT_OPENAQ_LIMIT, OPENAQ_LOCATIONS_URL


def fetch_sensor_ids_from_bounding_box(
    api_key: str,
    min_longitude: float,
    min_latitude: float,
    max_longitude: float,
    max_latitude: float,
    limit: int = DEFAULT_OPENAQ_LIMIT,
) -> list[dict[str, object]]:
    """Return OpenAQ sensor metadata for a bounding box query."""

    params = {
        "bbox": f"{min_longitude},{min_latitude},{max_longitude},{max_latitude}",
        "limit": limit,
    }
    url = f"{OPENAQ_LOCATIONS_URL}?{urlencode(params)}"

    payload = fetch_json_via_curl(url, headers={"X-API-Key": api_key})
    results = payload.get("results")

    if not isinstance(results, list):
        raise APIError("Unexpected response payload: 'results' missing or invalid")

    return results
