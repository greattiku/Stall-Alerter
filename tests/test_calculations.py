"""Unit tests for date handling, classification, and the urgency formula."""

from datetime import date
import unittest

from stall_alerter.calculations import calculate_candidate


class CalculationTests(unittest.TestCase):
    def setUp(self):
        self.reference_date = date(2026, 10, 19)

    def record(self, start, allowed=4, weight=5, score=99):
        return {"candidate_name": "Ada", "stage_start_date": date.fromisoformat(start),
                "allowed_days": allowed, "stage_weight": weight,
                "candidate_assessment_score": score}

    def test_within_allowed_duration_is_on_track(self):
        result = calculate_candidate(self.record("2026-10-17"), self.reference_date)
        self.assertEqual(result["days_in_stage"], 2)
        self.assertEqual(result["overdue_days"], 0)
        self.assertEqual(result["status"], "On track")

    def test_exact_deadline_is_on_track(self):
        result = calculate_candidate(self.record("2026-10-15"), self.reference_date)
        self.assertEqual(result["overdue_days"], 0)
        self.assertEqual(result["status"], "On track")

    def test_overdue_and_priority_score(self):
        result = calculate_candidate(self.record("2026-10-12", allowed=4, weight=5), self.reference_date)
        self.assertEqual(result["overdue_days"], 3)
        self.assertEqual(result["stage_priority_score"], 15)
        self.assertEqual(result["status"], "Stalled")

    def test_assessment_score_does_not_change_status_or_priority(self):
        low = calculate_candidate(self.record("2026-10-12", score=10), self.reference_date)
        high = calculate_candidate(self.record("2026-10-12", score=100), self.reference_date)
        self.assertEqual(low["status"], high["status"])
        self.assertEqual(low["stage_priority_score"], high["stage_priority_score"])


if __name__ == "__main__":
    unittest.main()
