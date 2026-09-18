from __future__ import annotations

import csv
import io


class CsvFormatError(Exception):
    """Raised when an uploaded file can't be parsed as the expected CSV
    shape (empty, undecodable, or missing a required column) -- callers
    turn this into a 400 rather than letting the upload crash."""


def parse_csv_rows(file_bytes: bytes, required_columns: set[str]) -> list[dict[str, str]]:
    """Parses CSV bytes into a list of rows keyed by lowercase, stripped
    column names, so callers never have to worry about header casing or
    incidental whitespace.
    """
    if not file_bytes.strip():
        raise CsvFormatError("The CSV file is empty.")

    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CsvFormatError("The file could not be read as UTF-8 text.") from exc

    reader = csv.DictReader(io.StringIO(text))
    fieldnames = reader.fieldnames or []
    normalized_columns = {name.strip().lower() for name in fieldnames if name}

    missing = required_columns - normalized_columns
    if missing:
        raise CsvFormatError(
            f"CSV is missing required column(s): {', '.join(sorted(missing))}."
        )

    rows: list[dict[str, str]] = []
    for raw_row in reader:
        row: dict[str, str] = {}
        for key, value in raw_row.items():
            # DictReader maps any columns beyond the header count to a
            # `None` key holding a list -- skip those rather than crash.
            if key is None:
                continue
            row[key.strip().lower()] = (value or "").strip()
        rows.append(row)
    return rows
