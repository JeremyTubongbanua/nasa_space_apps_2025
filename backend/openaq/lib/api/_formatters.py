"""Helper functions for shaping OpenAQ API responses."""

from __future__ import annotations


def summarize_locations(results: list[dict[str, object]]) -> list[dict[str, object]]:
    """Return jq-style summaries for location results."""

    summaries: list[dict[str, object]] = []

    for location in results:
        if not isinstance(location, dict):
            continue

        coordinates = location.get("coordinates")
        if isinstance(coordinates, dict):
            coordinates_summary: dict[str, object] | None = {
                "latitude": coordinates.get("latitude"),
                "longitude": coordinates.get("longitude"),
            }
        else:
            coordinates_summary = None

        summaries.append(
            {
                "id": location.get("id"),
                "name": location.get("name"),
                "coordinates": coordinates_summary,
                "timezone": location.get("timezone"),
            }
        )

    return summaries
