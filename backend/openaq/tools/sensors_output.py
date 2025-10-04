"""CLI tool for fetching OpenAQ sensor metadata and exporting to CSV."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from lib.api import APIError
from lib.api.fetch_sensor_ids_from_bounding_box import (
    fetch_sensor_ids_from_bounding_box,
)
from lib.api.fetch_sensor_ids_from_point_and_radius import (
    fetch_sensor_ids_from_point_and_radius,
)
from lib.api_key import MissingAPIKeyError, get_api_key
from lib.constants import (
    DEFAULT_OPENAQ_LIMIT,
    DEFAULT_OPENAQ_RADIUS_METERS,
    DEFAULT_TORONTO_LATITUDE,
    DEFAULT_TORONTO_LONGITUDE,
)
from lib.csv_helper import write_dicts_to_csv


CSV_HEADERS = ["id", "name", "latitude", "longitude", "timezone"]
DEFAULT_OUTPUT_PATH = ROOT_DIR / "data" / "sensors.csv"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Configure and parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Fetch OpenAQ sensor metadata and write it to CSV",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Destination CSV file path (default: data/sensors.csv)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_OPENAQ_LIMIT,
        help=f"Number of records to fetch (default: {DEFAULT_OPENAQ_LIMIT})",
    )
    parser.add_argument(
        "--latitude",
        type=float,
        default=DEFAULT_TORONTO_LATITUDE,
        help=f"Latitude for point query (default: {DEFAULT_TORONTO_LATITUDE})",
    )
    parser.add_argument(
        "--longitude",
        type=float,
        default=DEFAULT_TORONTO_LONGITUDE,
        help=f"Longitude for point query (default: {DEFAULT_TORONTO_LONGITUDE})",
    )
    parser.add_argument(
        "--radius",
        type=int,
        default=DEFAULT_OPENAQ_RADIUS_METERS,
        help=(
            "Radius in meters for point query "
            f"(default: {DEFAULT_OPENAQ_RADIUS_METERS})"
        ),
    )
    parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"),
        help=(
            "Use bounding box query instead of point query; provide "
            "minLon minLat maxLon maxLat"
        ),
    )

    return parser.parse_args(argv)


def fetch_locations(
    api_key: str,
    *,
    limit: int,
    latitude: float,
    longitude: float,
    radius: int,
    bbox: list[float] | None,
) -> list[dict[str, object]]:
    """Fetch sensor locations using either point-radius or bounding box."""

    if bbox:
        min_lon, min_lat, max_lon, max_lat = bbox
        return fetch_sensor_ids_from_bounding_box(
            api_key=api_key,
            min_longitude=min_lon,
            min_latitude=min_lat,
            max_longitude=max_lon,
            max_latitude=max_lat,
            limit=limit,
        )

    return fetch_sensor_ids_from_point_and_radius(
        api_key=api_key,
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius,
        limit=limit,
    )


def build_rows(locations: list[dict[str, object]]) -> list[dict[str, object]]:
    """Project OpenAQ API results into the CSV schema."""

    rows: list[dict[str, object]] = []

    for entry in locations:
        coordinates = entry.get("coordinates") or {}
        latitude = None
        longitude = None

        if isinstance(coordinates, dict):
            latitude = coordinates.get("latitude")
            longitude = coordinates.get("longitude")

        rows.append(
            {
                "id": entry.get("id"),
                "name": entry.get("name"),
                "latitude": latitude,
                "longitude": longitude,
                "timezone": entry.get("timezone"),
            }
        )

    return rows


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        api_key = get_api_key()
    except MissingAPIKeyError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        locations = fetch_locations(
            api_key,
            limit=args.limit,
            latitude=args.latitude,
            longitude=args.longitude,
            radius=args.radius,
            bbox=args.bbox,
        )
    except APIError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    output_path = args.output.resolve()

    try:
        write_dicts_to_csv(build_rows(locations), output_path, CSV_HEADERS)
    except OSError as exc:
        print(f"Failed to write CSV: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {len(locations)} rows to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
