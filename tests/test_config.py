"""Tests for company settings validation and configuration changes."""

import json
from pathlib import Path
import tempfile
import unittest

from stall_alerter.config import ConfigurationError, get_stage_settings, load_config

VALID = {"stages": {"Interview": {"allowed_days": 4, "weight": 5, "recommended_action": "Request feedback."}}}


class ConfigTests(unittest.TestCase):
    def write_config(self, folder, payload):
        path = Path(folder) / "settings.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_loads_valid_configuration_case_insensitively(self):
        with tempfile.TemporaryDirectory() as folder:
            config = load_config(self.write_config(folder, VALID))
            self.assertEqual(get_stage_settings(config, " interview ")["weight"], 5)

    def test_negative_duration_rejected(self):
        bad = {"stages": {"Interview": {**VALID["stages"]["Interview"], "allowed_days": -1}}}
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(ConfigurationError):
            load_config(self.write_config(folder, bad))

    def test_invalid_weight_rejected(self):
        bad = {"stages": {"Interview": {**VALID["stages"]["Interview"], "weight": 6}}}
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(ConfigurationError):
            load_config(self.write_config(folder, bad))

    def test_boolean_duration_rejected(self):
        bad = {"stages": {"Interview": {**VALID["stages"]["Interview"], "allowed_days": True}}}
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(ConfigurationError):
            load_config(self.write_config(folder, bad))

    def test_case_insensitive_duplicate_stage_names_rejected(self):
        settings = VALID["stages"]["Interview"]
        bad = {"stages": {"Interview": settings, " interview ": settings}}
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(ConfigurationError):
            load_config(self.write_config(folder, bad))

    def test_missing_file_rejected(self):
        with self.assertRaises(ConfigurationError):
            load_config("file-that-does-not-exist.json")

    def test_changed_deadline_is_used(self):
        changed = {"stages": {"Interview": {**VALID["stages"]["Interview"], "allowed_days": 9}}}
        with tempfile.TemporaryDirectory() as folder:
            config = load_config(self.write_config(folder, changed))
            self.assertEqual(get_stage_settings(config, "Interview")["allowed_days"], 9)


if __name__ == "__main__":
    unittest.main()
