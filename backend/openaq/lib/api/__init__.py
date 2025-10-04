"""Core helpers for interacting with the OpenAQ API."""

from __future__ import annotations

import json
import subprocess


class APIError(RuntimeError):
    """Raised when an external API interaction fails."""


def fetch_json_via_curl(url: str, headers: dict[str, str] | None = None) -> dict[str, object]:
    """Execute a curl request and return the parsed JSON payload."""

    command = ["curl", "-s", url]

    if headers:
        for name, value in headers.items():
            command.extend(["-H", f"{name}: {value}"])

    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise APIError("curl command not found on PATH") from exc
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or "unknown error"
        raise APIError(f"curl command failed with exit code {exc.returncode}: {message}") from exc

    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise APIError("Unable to decode JSON response") from exc


__all__ = ["APIError", "fetch_json_via_curl"]
