# """Validate candidate rows and assessment data; report row-level problems clearly."""

# import json
# import re
# from datetime import date, datetime
# from typing import Any


# def parse_assessments(raw_scores: str, raw_status: str) -> tuple[float | None, str, str | None]:
#     """Return (score, display status, warning); scores must be percentages from 0 to 100.

#     A completed score is calculated only when the status is completed and a non-empty JSON
#     array of numeric scores is present. An explicitly incomplete assessment remains Incomplete.
#     """
#     status = raw_status.strip().casefold() if raw_status else ""
#     if status == "complete":
#         status = "completed"
#     if status not in {"", "completed", "incomplete", "unknown"}:
#         return None, "Unknown", "assessment_status must be completed, incomplete, or unknown."
#     if status == "incomplete":
#         if raw_scores:
#             try:
#                 _validate_score_array(json.loads(raw_scores))
#             except (json.JSONDecodeError, ValueError) as exc:
#                 return None, "Incomplete", f"Assessment scores could not be validated: {exc}"
#         return None, "Incomplete", None
#     if not raw_scores:
#         return None, "Unknown", None
#     try:
#         values = _validate_score_array(json.loads(raw_scores))
#     except (json.JSONDecodeError, ValueError) as exc:
#         return None, "Unknown", f"Invalid assessment_scores: {exc}"
#     if status == "unknown":
#         return None, "Unknown", None
#     # A populated score list without a status is not assumed to be complete.
#     if status != "completed":
#         return None, "Unknown", "Scores were supplied without assessment_status=completed; no final score was calculated."
#     return sum(values) / len(values), "Scored", None


# def _validate_score_array(values: Any) -> list[float]:
#     """Validate that every provided assessment score is a percentage in the 0–100 range."""
#     if not isinstance(values, list) or not values:
#         raise ValueError("expected a non-empty JSON array, for example [90, 94, 92].")
#     clean: list[float] = []
#     for value in values:
#         if isinstance(value, bool) or not isinstance(value, (int, float)):
#             raise ValueError("every assessment score must be a number.")
#         if not 0 <= value <= 100:
#             raise ValueError("assessment scores must be between 0 and 100.")
#         clean.append(float(value))
#     return clean


# def validate_candidate_row(row: dict[str, str], reference_date: date, config: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
#     """Validate one candidate; return a processed input record or warnings for exclusion."""
#     warnings: list[str] = []
#     row_number = row.get("_row_number", "?")
#     name = row.get("candidate_name", "").strip()
#     stage = row.get("current_stage", "").strip()
#     raw_date = row.get("stage_start_date", "").strip()
#     if not name:
#         warnings.append(f"CSV row {row_number}: candidate_name is missing; record excluded.")
#     if not stage:
#         warnings.append(f"CSV row {row_number}: current_stage is missing; record excluded.")
#     if not raw_date:
#         warnings.append(f"CSV row {row_number}: stage_start_date is missing; record excluded.")
#     parsed_date = None
#     # if raw_date:
#     #     try:
#     #         # Enforce the documented YYYY-MM-DD shape; fromisoformat accepts other ISO forms too.
#     #         if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw_date):
#     #             raise ValueError("date must use YYYY-MM-DD")
#     #         parsed_date = date.fromisoformat(raw_date)
#     #     except ValueError:
#     #         warnings.append(f"CSV row {row_number}: invalid stage_start_date {raw_date!r}; use YYYY-MM-DD. Record excluded.")

#     # UPDATED: Accept ISO dates and common US-style dates from CSV imports.
#     # Supported examples: 2026-10-01, 10/1/2026, and 9/25/2026.
#     parsed_date = None

#     if raw_date:
#         for date_format in ("%Y-%m-%d", "%m/%d/%Y"):
#             try:
#                 parsed_date = datetime.strptime(
#                     raw_date,
#                     date_format,
#                 ).date()
#                 break
#             except ValueError:
#                 # Try the next supported date format.
#                 continue

#         # Keep genuinely invalid dates excluded and explain why.
#         if parsed_date is None:
#             warnings.append(
#                 f"CSV row {row_number}: invalid stage_start_date "
#                 f"{raw_date!r}; use YYYY-MM-DD or M/D/YYYY. "
#                 "Record excluded."
#             )

#     if parsed_date and parsed_date > reference_date:
#         warnings.append(f"CSV row {row_number}: stage_start_date is in the future; record excluded.")
#     stage_settings = None
#     if stage:
#         from .config import get_stage_settings
#         stage_settings = get_stage_settings(config, stage)
#         if stage_settings is None:
#             warnings.append(f"CSV row {row_number}: unknown hiring stage {stage!r}; add it to company settings. Record excluded.")
#     score, assessment_status, assessment_warning = parse_assessments(
#         row.get("assessment_scores", ""), row.get("assessment_status", "")
#     )
#     if assessment_warning:
#         warnings.append(f"CSV row {row_number}: {assessment_warning}")
#     # Invalid assessment data does not invalidate the candidate's stage-priority calculations.
#     if not name or not stage or not parsed_date or parsed_date > reference_date or stage_settings is None:
#         return None, warnings
#     return {
#         "candidate_name": name,
#         "current_stage": stage_settings["configured_stage_name"],
#         "stage_start_date": parsed_date,
#         "allowed_days": stage_settings["allowed_days"],
#         "stage_weight": stage_settings["weight"],
#         "recommended_action": stage_settings["recommended_action"],
#         "candidate_assessment_score": score,
#         "assessment_display_status": assessment_status,
#         "_row_number": row_number,
#     }, warnings


# def exclude_duplicate_candidates(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
#     """Exclude every row for a repeated candidate name instead of guessing which is correct."""
#     counts: dict[str, int] = {}
#     for record in records:
#         key = record["candidate_name"].strip().casefold()
#         counts[key] = counts.get(key, 0) + 1
#     duplicates = {name for name, count in counts.items() if count > 1}
#     kept = [record for record in records if record["candidate_name"].strip().casefold() not in duplicates]
#     warnings = [
#         f"Duplicate candidate name {record['candidate_name']!r} appears more than once; all matching records excluded."
#         for record in records if record["candidate_name"].strip().casefold() in duplicates
#     ]
#     # Emit one warning per duplicated name, not one warning per row.
#     warnings = list(dict.fromkeys(warnings))
#     return kept, warnings
"""Validate candidate rows, assessment data, and duplicate email addresses.

Missing or invalid email addresses produce warnings but do not exclude a
candidate. Duplicate valid email addresses exclude all matching records.
Assessment data problems do not invalidate stage-priority calculations.
"""

import json
import re
from datetime import date, datetime
from typing import Any


def validate_email(raw_email: str) -> tuple[str, str | None]:
    """Normalize an email and return a warning if it is missing or malformed."""
    email = (raw_email or "").strip().casefold()

    if not email:
        return "", "Email is missing. The candidate is retained, but HR should provide a contact email."

    # Basic format check for common email addresses.
    email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    if not re.fullmatch(email_pattern, email):
        return email, (
            f"Email {raw_email.strip()!r} does not appear to be valid. "
            "The candidate is retained; HR can check the email or use another contact method."
        )

    return email, None


def _validate_score_array(values: Any) -> list[float]:
    """Validate a non-empty list of assessment percentages from 0 to 100."""
    if not isinstance(values, list) or not values:
        raise ValueError(
            "expected a non-empty JSON array, for example [90, 94, 92]."
        )

    clean_scores: list[float] = []

    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("every assessment score must be a number.")

        if not 0 <= value <= 100:
            raise ValueError("assessment scores must be between 0 and 100.")

        clean_scores.append(float(value))

    return clean_scores


def parse_assessments(
    raw_scores: str,
    raw_status: str,
) -> tuple[float | None, str, str | None]:
    """Return (average score, display status, warning).

    A score is calculated only when assessment_status is completed and
    assessment_scores contains a valid, non-empty JSON array.

    Missing, unknown, incomplete, or invalid assessment data does not
    exclude a candidate from stage-priority calculations.
    """
    status = (raw_status or "").strip().casefold()
    scores_text = (raw_scores or "").strip()

    # Accept common status variations from HR spreadsheets.
    if status == "complete":
        status = "completed"

    if status not in {"", "completed", "incomplete", "unknown"}:
        return (
            None,
            "Unknown",
            "assessment_status must be completed, incomplete, or unknown. "
            "No assessment score was calculated.",
        )

    # Incomplete assessments must never be treated as final scores.
    if status == "incomplete":
        if not scores_text:
            return None, "Incomplete", None

        try:
            _validate_score_array(json.loads(scores_text))
        except (json.JSONDecodeError, ValueError) as exc:
            return (
                None,
                "Incomplete",
                f"Assessment scores could not be validated: {exc}",
            )

        return None, "Incomplete", None

    # Unknown status means we cannot confirm whether the scores are final.
    if status == "unknown":
        if not scores_text:
            return None, "Unknown", None

        try:
            _validate_score_array(json.loads(scores_text))
        except (json.JSONDecodeError, ValueError) as exc:
            return None, "Unknown", f"Invalid assessment_scores: {exc}"

        return None, "Unknown", None

    if not scores_text:
        if status == "completed":
            return (
                None,
                "Unknown",
                "assessment_status is completed, but assessment_scores is missing.",
            )

        return None, "Unknown", None

    try:
        values = _validate_score_array(json.loads(scores_text))
    except (json.JSONDecodeError, ValueError) as exc:
        return None, "Unknown", f"Invalid assessment_scores: {exc}"

    # Scores without an explicit completed status are not assumed final.
    if status != "completed":
        return (
            None,
            "Unknown",
            "Scores were supplied without assessment_status=completed; "
            "no final score was calculated.",
        )

    return sum(values) / len(values), "Scored", None


def validate_candidate_row(
    row: dict[str, str],
    reference_date: date,
    config: dict[str, Any],
) -> tuple[dict[str, Any] | None, list[str]]:
    """Validate one CSV row and return its processed record and warnings."""
    warnings: list[str] = []
    row_number = row.get("_row_number", "?")

    name = (row.get("candidate_name") or "").strip()
    stage = (row.get("current_stage") or "").strip()
    raw_date = (row.get("stage_start_date") or "").strip()

    # Candidate name, stage, and stage start date are needed for ranking.
    if not name:
        warnings.append(
            f"CSV row {row_number}: candidate_name is missing; record excluded."
        )

    if not stage:
        warnings.append(
            f"CSV row {row_number}: current_stage is missing; record excluded."
        )

    if not raw_date:
        warnings.append(
            f"CSV row {row_number}: stage_start_date is missing; record excluded."
        )

    # Validate the date while accepting ISO and common US-style date formats.
    parsed_date = None

    if raw_date:
        for date_format in ("%Y-%m-%d", "%m/%d/%Y"):
            try:
                parsed_date = datetime.strptime(
                    raw_date, date_format
                ).date()
                break
            except ValueError:
                continue

        if parsed_date is None:
            warnings.append(
                f"CSV row {row_number}: invalid stage_start_date "
                f"{raw_date!r}; use YYYY-MM-DD or M/D/YYYY. Record excluded."
            )
        elif parsed_date > reference_date:
            warnings.append(
                f"CSV row {row_number}: stage_start_date is in the future; "
                "record excluded."
            )

    # Email problems are warnings, not reasons to exclude a candidate.
    email, email_warning = validate_email(row.get("email", ""))

    if email_warning:
        warnings.append(f"CSV row {row_number}: {email_warning}")

    # Confirm that the stage exists in this company's configuration.
    stage_settings = None

    if stage:
        from .config import get_stage_settings

        stage_settings = get_stage_settings(config, stage)

        if stage_settings is None:
            warnings.append(
                f"CSV row {row_number}: unknown hiring stage {stage!r}; "
                "add it to company settings. Record excluded."
            )

    # Assessment problems affect the assessment score only, not stage priority.
    score, assessment_status, assessment_warning = parse_assessments(
        row.get("assessment_scores", ""),
        row.get("assessment_status", ""),
    )

    if assessment_warning:
        warnings.append(
            f"CSV row {row_number}: {assessment_warning}"
        )

    # Exclude only when required ranking information is unusable.
    if (
        not name
        or not stage
        or parsed_date is None
        or parsed_date > reference_date
        or stage_settings is None
    ):
        return None, warnings

    return {
        "candidate_name": name,
        "email": email,
        "current_stage": stage_settings["configured_stage_name"],
        "stage_start_date": parsed_date,
        "allowed_days": stage_settings["allowed_days"],
        "stage_weight": stage_settings["weight"],
        "recommended_action": stage_settings["recommended_action"],
        "candidate_assessment_score": score,
        "assessment_display_status": assessment_status,
        "_row_number": row_number,
    }, warnings


def exclude_duplicate_candidates(
    records: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Exclude every candidate with a repeated, valid email address.

    Names are not used to identify duplicates. Candidates with the same
    name but different valid email addresses remain in the results.

    Missing or malformed emails do not identify a person reliably, so
    they are not used for duplicate exclusion.
    """
    email_rows: dict[str, list[int]] = {}

    for index, record in enumerate(records):
        email = (record.get("email") or "").strip().casefold()

        if not email:
            continue

        # Only valid addresses can be used as reliable duplicate identifiers.
        if not re.fullmatch(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            continue

        email_rows.setdefault(email, []).append(index)

    duplicate_emails = {
        email: indices
        for email, indices in email_rows.items()
        if len(indices) > 1
    }

    duplicate_indices = {
        index
        for indices in duplicate_emails.values()
        for index in indices
    }

    kept_records = [
        record
        for index, record in enumerate(records)
        if index not in duplicate_indices
    ]

    warnings = []

    for email, indices in duplicate_emails.items():
        row_numbers = [
            str(records[index].get("_row_number", "?"))
            for index in indices
        ]

        warnings.append(
            f"Duplicate email {email!r} appears in CSV rows "
            f"{', '.join(row_numbers)}; all matching records excluded."
        )

    return kept_records, warnings