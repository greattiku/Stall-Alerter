"""Read hiring-board CSV files while preserving individual rows for validation."""

import csv
from pathlib import Path


REQUIRED_COLUMNS = {"candidate_name", "email", "current_stage", "stage_start_date", "assessment_scores", "assessment_status"}
OPTIONAL_COLUMNS = {"assessment_scores", "assessment_status"}
# Canonical column order shared by the Streamlit editor, CSV imports, and persisted records.
CANDIDATE_COLUMNS = ["candidate_name", "email", "current_stage", "stage_start_date", "assessment_scores", "assessment_status"]


class DataFileError(ValueError):
    """Raised when a hiring-board file cannot be processed at all."""


def load_candidates(path: str | Path) -> list[dict[str, str]]:
    """Read rows from CSV and fail clearly for missing columns or empty input."""
    csv_path = Path(path)
    if not csv_path.is_file():
        raise DataFileError(f"Hiring-board CSV not found: {csv_path}")
    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames:
                raise DataFileError("The hiring-board CSV is empty or has no header row.")
            # Reject blank or duplicate normalized headers instead of silently overwriting CSV values.
            normalized_headers = [header.strip() if header else "" for header in reader.fieldnames]
            if any(not header for header in normalized_headers):
                raise DataFileError("The CSV header contains a blank column name.")
            if len(set(normalized_headers)) != len(normalized_headers):
                raise DataFileError("The CSV contains duplicate column names after whitespace normalization.")
            headers = set(normalized_headers)
            missing = REQUIRED_COLUMNS - headers
            if missing:
                raise DataFileError("Missing required CSV column(s): " + ", ".join(sorted(missing)))
            rows = []
            for row_number, row in enumerate(reader, start=2):
                # Normalise header whitespace but retain cell values for clear validation messages.
                normalised = {(key or "").strip(): (value or "").strip() for key, value in row.items() if key}
                normalised["_row_number"] = str(row_number)
                for column in OPTIONAL_COLUMNS:
                    normalised.setdefault(column, "")
                rows.append(normalised)
    except UnicodeDecodeError as exc:
        raise DataFileError("The CSV must be saved as UTF-8 text.") from exc
    except OSError as exc:
        raise DataFileError(f"Could not read hiring-board CSV: {exc}") from exc
    if not rows:
        raise DataFileError("The hiring-board CSV contains headers but no candidate records.")
    return rows
