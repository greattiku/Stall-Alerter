"""Deterministic date, urgency, and assessment calculations."""

from datetime import date
from typing import Any


def calculate_candidate(record: dict[str, Any], reference_date: date) -> dict[str, Any]:
    """Add stage elapsed time, overdue days, status, and priority score to a record.

    Candidate assessment results are intentionally not used in any of these calculations.
    """
    days_in_stage = (reference_date - record["stage_start_date"]).days
    overdue_days = max(0, days_in_stage - record["allowed_days"])
    return {
        **record,
        "days_in_stage": days_in_stage,
        "overdue_days": overdue_days,
        "status": "Stalled" if overdue_days > 0 else "On track",
        "stage_priority_score": overdue_days * record["stage_weight"],
    }


def format_assessment_score(record: dict[str, Any]) -> str:
    """Display a valid percentage or the distinct Unknown/Incomplete availability states."""
    score = record.get("candidate_assessment_score")
    if score is not None:
        formatted = f"{score:.2f}".rstrip("0").rstrip(".")
        return f"{formatted}%"
    return record.get("assessment_display_status", "Unknown")
