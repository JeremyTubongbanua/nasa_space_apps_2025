"""Helpers for retrieving API keys from environment variables."""

from __future__ import annotations

import os


class MissingAPIKeyError(RuntimeError):
    """Raised when the expected API key environment variable is missing."""


def get_api_key(env_var: str = "OPENAQ_KEY") -> str:
    """Return the API key stored in the given environment variable."""

    value = os.getenv(env_var)
    if not value:
        raise MissingAPIKeyError(
            f"Missing required environment variable {env_var}"
        )

    return value
