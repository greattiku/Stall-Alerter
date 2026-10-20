"""Load and validate company-specific hiring-stage settings."""

import json
from pathlib import Path
from typing import Any


class ConfigurationError(ValueError):
    """Raised when settings cannot be used safely."""


def load_config(path: str | Path) -> dict[str, Any]:
    """Load JSON settings and validate every configured stage."""
    config_path = Path(path)
    if not config_path.is_file():
        raise ConfigurationError(f"Configuration file not found: {config_path}")
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ConfigurationError(f"Could not read valid JSON from {config_path}: {exc}") from exc

    if not isinstance(config, dict) or not isinstance(config.get("stages"), dict) or not config["stages"]:
        raise ConfigurationError("Configuration must contain a non-empty 'stages' object.")

    # Stage names are matched case-insensitively, but their original display names are preserved.
    seen_names: set[str] = set()
    for name, settings in config["stages"].items():
        if not isinstance(name, str) or not name.strip():
            raise ConfigurationError("Every configured stage must have a non-empty name.")
        if name.strip().casefold() in seen_names:
            raise ConfigurationError(f"Duplicate stage name after normalisation: {name!r}.")
        seen_names.add(name.strip().casefold())
        if not isinstance(settings, dict):
            raise ConfigurationError(f"Settings for stage {name!r} must be an object.")
        allowed = settings.get("allowed_days")
        weight = settings.get("weight")
        action = settings.get("recommended_action")
        # bool is a subclass of int in Python, so explicitly reject it for numeric settings.
        if isinstance(allowed, bool) or not isinstance(allowed, int) or allowed < 0:
            raise ConfigurationError(f"Stage {name!r}: allowed_days must be a non-negative integer.")
        if isinstance(weight, bool) or not isinstance(weight, int) or not 1 <= weight <= 5:
            raise ConfigurationError(f"Stage {name!r}: weight must be an integer from 1 to 5.")
        if not isinstance(action, str) or not action.strip():
            raise ConfigurationError(f"Stage {name!r}: recommended_action must be a non-empty string.")
    return config


def get_stage_settings(config: dict[str, Any], stage_name: str) -> dict[str, Any] | None:
    """Find a stage without depending on letter case or surrounding spaces."""
    wanted = stage_name.strip().casefold()
    for name, settings in config["stages"].items():
        if name.strip().casefold() == wanted:
            return {**settings, "configured_stage_name": name}
    return None
