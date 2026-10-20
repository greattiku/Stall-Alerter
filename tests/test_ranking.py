"""Unit tests for deterministic queue ordering and tie-breaking."""

import unittest
from stall_alerter.ranking import rank_candidates


def candidate(name, status, score, overdue, assessment=None):
    return {"candidate_name": name, "status": status, "stage_priority_score": score,
            "overdue_days": overdue, "stage_weight": 5, "days_in_stage": 2,
            "allowed_days": 2, "candidate_assessment_score": assessment}


class RankingTests(unittest.TestCase):
    def test_stalled_before_on_track_and_score_descending(self):
        result = rank_candidates([candidate("Zed", "On track", 0, 0), candidate("Ada", "Stalled", 10, 2), candidate("Ben", "Stalled", 15, 3)])
        self.assertEqual([item["candidate_name"] for item in result], ["Ben", "Ada", "Zed"])

    def test_equal_priority_uses_overdue_days_then_name(self):
        result = rank_candidates([candidate("Zoe", "Stalled", 10, 5), candidate("Ada", "Stalled", 10, 2), candidate("Ben", "Stalled", 10, 2)])
        self.assertEqual([item["candidate_name"] for item in result], ["Zoe", "Ada", "Ben"])

    def test_assessment_score_does_not_affect_ranking(self):
        result = rank_candidates([candidate("Ada", "Stalled", 10, 2, 100), candidate("Ben", "Stalled", 10, 2, 1)])
        self.assertEqual([item["candidate_name"] for item in result], ["Ada", "Ben"])
        self.assertIn("Stage Priority Score of 10", result[0]["ranking_explanation"])

    def test_on_track_candidates_are_alphabetical(self):
        result = rank_candidates([candidate("Zoe", "On track", 0, 0), candidate("Ada", "On track", 0, 0)])
        self.assertEqual([item["candidate_name"] for item in result], ["Ada", "Zoe"])


if __name__ == "__main__":
    unittest.main()
