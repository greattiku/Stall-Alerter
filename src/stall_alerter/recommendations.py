"""Return company-configured follow-up suggestions without contacting anyone."""

from typing import Any


def recommend_action(record: dict[str, Any]) -> str:
    """Use the action attached to the configured stage; this function has no side effects."""
    return record["recommended_action"]
