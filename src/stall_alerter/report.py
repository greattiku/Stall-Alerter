"""Write ranked results to a spreadsheet-friendly CSV report."""

import csv
from pathlib import Path
from typing import Any

from .calculations import format_assessment_score

REPORT_COLUMNS = [
    "Priority rank", "Candidate name", "Email", "Current stage", "Days in stage", "Allowed days",
    "Days overdue", "Stage weight", "Stage Priority Score", "Status",
    "Candidate Assessment Score", "Recommended action", "Ranking explanation",
]


def write_report(records: list[dict[str, Any]], output_path: str | Path) -> Path:
    """Create the report directory if needed and write only the agreed report columns."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        for record in records:
            writer.writerow({
                "Priority rank": record["priority_rank"],
                "Candidate name": record["candidate_name"],
                "Email": record.get("email", ""),
                "Current stage": record["current_stage"],
                "Days in stage": record["days_in_stage"],
                "Allowed days": record["allowed_days"],
                "Days overdue": record["overdue_days"],
                "Stage weight": f"{record['stage_weight']}/5",
                "Stage Priority Score": record["stage_priority_score"],
                "Status": record["status"],
                "Candidate Assessment Score": format_assessment_score(record),
                "Recommended action": record["recommended_action"],
                "Ranking explanation": record["ranking_explanation"],
            })
    return path
