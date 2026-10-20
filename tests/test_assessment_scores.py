"""Tests for assessment average calculation and availability states."""

import unittest
from stall_alerter.validation import parse_assessments


class AssessmentTests(unittest.TestCase):
    def test_average_completed_scores(self):
        score, status, warning = parse_assessments("[90,94,92]", "completed")
        self.assertEqual(score, 92)
        self.assertEqual(status, "Scored")
        self.assertIsNone(warning)

    def test_complete_status_alias_calculates_score(self):
        score, status, warning = parse_assessments("[80,90]", "Complete")
        self.assertEqual(score, 85)
        self.assertEqual(status, "Scored")
        self.assertIsNone(warning)

    def test_missing_score_is_unknown_not_zero(self):
        score, status, _ = parse_assessments("", "")
        self.assertIsNone(score)
        self.assertEqual(status, "Unknown")

    def test_incomplete_is_not_averaged_as_final(self):
        score, status, _ = parse_assessments("[80,90]", "incomplete")
        self.assertIsNone(score)
        self.assertEqual(status, "Incomplete")

    def test_out_of_range_score_is_rejected(self):
        score, status, warning = parse_assessments("[80,101]", "completed")
        self.assertIsNone(score)
        self.assertEqual(status, "Unknown")
        self.assertIn("between 0 and 100", warning)

    def test_malformed_scores_are_reported(self):
        score, status, warning = parse_assessments("not-json", "completed")
        self.assertIsNone(score)
        self.assertIsNotNone(warning)


if __name__ == "__main__":
    unittest.main()
