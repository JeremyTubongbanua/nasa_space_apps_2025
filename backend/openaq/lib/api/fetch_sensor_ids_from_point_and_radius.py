"""Fetch sensor details using a point and radius query."""

from __future__ import annotations

from . import APIError, fetch_json_via_curl
from ._formatters import summarize_locations
from lib.constants import DEFAULT_OPENAQ_LIMIT, OPENAQ_LOCATIONS_URL


def fetch_sensor_ids_from_point_and_radius(
    api_key: str,
    latitude: float,
    longitude: float,
    radius_meters: int,
    limit: int = DEFAULT_OPENAQ_LIMIT,
) -> list[dict[str, object]]:
    """Return OpenAQ sensor metadata for a point and radius query."""

    query = "&".join(
        [
            f"coordinates={latitude},{longitude}",
            f"radius={radius_meters}",
            f"limit={limit}",
        ]
    )
    url = f"{OPENAQ_LOCATIONS_URL}?{query}"

    payload = fetch_json_via_curl(url, headers={"X-API-Key": api_key})
    results = payload.get("results")

    if not isinstance(results, list):
        raise APIError("Unexpected response payload: 'results' missing or invalid")

    return summarize_locations(results)
