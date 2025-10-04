"""Utilities for working with CSV files."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable


def write_dicts_to_csv(
    records: Iterable[dict[str, object]],
    destination: Path,
    fieldnames: list[str],
) -> None:
    """Write an iterable of dictionaries to a CSV file with the given headers."""

    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in records:
            writer.writerow(row)
