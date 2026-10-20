"""Apply the agreed stable ranking rules and explain each queue position."""

from typing import Any


def rank_candidates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank stalled candidates first; assessment score is deliberately absent from the key."""
    ranked = sorted(
        records,
        key=lambda item: (
            0 if item["status"] == "Stalled" else 1,
            -item["stage_priority_score"] if item["status"] == "Stalled" else 0,
            -item["overdue_days"] if item["status"] == "Stalled" else 0,
            item["candidate_name"].casefold(),
        ),
    )
    for rank, record in enumerate(ranked, start=1):
        record["priority_rank"] = rank
        record["ranking_explanation"] = explain_ranking(record)
    return ranked


def explain_ranking(record: dict[str, Any]) -> str:
    """Explain the calculated urgency using underlying business-rule values."""
    name = record["candidate_name"]
    if record["status"] == "Stalled":
        return (
            f"{name} is {record['overdue_days']} day(s) overdue in a stage with a weight of "
            f"{record['stage_weight']}, giving a Stage Priority Score of {record['stage_priority_score']}."
        )
    return (
        f"{name} is on track because {record['days_in_stage']} day(s) in the current stage "
        f"is within the allowed duration of {record['allowed_days']} day(s); priority score is 0."
    )
