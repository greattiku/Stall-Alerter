"""Integration test for the CSV-to-report workflow using isolated temporary data."""

import csv
import json
from datetime import date
from pathlib import Path
import tempfile
import unittest

from stall_alerter.main import run


class IntegrationTests(unittest.TestCase):
    def test_input_produces_report_without_committed_sample_candidates(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            input_path = root / "hiring_board.csv"
            config_path = root / "settings.json"
            output_path = root / "report.csv"
            # The candidate below exists only in this test and is never shipped as product data.
            with input_path.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=["candidate_name", "email", "current_stage", "stage_start_date", "assessment_scores", "assessment_status"])
                writer.writeheader()
                writer.writerow({"candidate_name": "Test Candidate", "email": "test.candidate@example.com", "current_stage": "Interview", "stage_start_date": "2026-10-10", "assessment_scores": "[80, 90]", "assessment_status": "completed"})
            config_path.write_text(json.dumps({"stages": {"Interview": {"allowed_days": 4, "weight": 5, "recommended_action": "Request feedback."}}}), encoding="utf-8")
            result = run(str(input_path), str(config_path), str(output_path), date(2026, 10, 19))
            self.assertEqual(result, 0)
            self.assertTrue(output_path.exists())
            content = output_path.read_text(encoding="utf-8-sig")
            self.assertIn("Stage Priority Score", content)
            self.assertIn("Candidate Assessment Score", content)
            self.assertIn("Test Candidate", content)


if __name__ == "__main__":
    unittest.main()
