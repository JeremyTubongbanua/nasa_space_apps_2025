"""Shared constant values for the backend services."""

from __future__ import annotations


OPENAQ_LOCATIONS_URL = "https://api.openaq.org/v3/locations"
OPENAQ_SENSORS_URL = "https://api.openaq.org/v3/sensors"
OPENAQ_PARAMETERS_URL = "https://api.openaq.org/v3/parameters"

DEFAULT_OPENAQ_LIMIT = 50
DEFAULT_OPENAQ_RADIUS_METERS = 25_000

# Toronto
DEFAULT_TORONTO_LATITUDE = 43.6532
DEFAULT_TORONTO_LONGITUDE = -79.3832
