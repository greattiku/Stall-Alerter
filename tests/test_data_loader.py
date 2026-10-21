"""Tests for CSV loading, missing columns, and duplicate policy."""

import csv
from datetime import date
from pathlib import Path
import tempfile
import unittest

from stall_alerter.data_loader import DataFileError, load_candidates
from stall_alerter.validation import exclude_duplicate_candidates, validate_candidate_row

CONFIG = {"stages": {"Screening": {"allowed_days": 3, "weight": 2, "recommended_action": "Schedule screening."}}}


class DataLoaderTests(unittest.TestCase):
    def test_downloadable_sample_csv_covers_assessment_and_missing_data_cases(self):
        sample_path = Path(__file__).resolve().parents[1] / "data" / "sample_candidate_import.csv"
        rows = load_candidates(sample_path)
        config = {
            "stages": {
                stage: {"allowed_days": 5, "weight": 1, "recommended_action": "Review candidate."}
                for stage in ("Screening", "Technical Interview", "HR Interview", "Executive Interview", "Offer")
            }
        }
        processed = {}
        warnings = []
        for row in rows:
            record, row_warnings = validate_candidate_row(row, date(2026, 10, 19), config)
            warnings.extend(row_warnings)
            if record:
                processed[record["candidate_name"]] = record

        self.assertEqual(processed["Sample Completed"]["candidate_assessment_score"], 87)
        self.assertEqual(processed["Sample Incomplete"]["assessment_display_status"], "Incomplete")
        self.assertEqual(processed["Sample Unknown"]["assessment_display_status"], "Unknown")
        self.assertEqual(processed["Sample Missing Scores"]["assessment_display_status"], "Unknown")
        self.assertTrue(any("stage_start_date is missing" in warning for warning in warnings))
        self.assertTrue(any("candidate_name is missing" in warning for warning in warnings))
        self.assertTrue(any("current_stage is missing" in warning for warning in warnings))
        self.assertTrue(any("invalid stage_start_date" in warning for warning in warnings))

    def test_empty_csv_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "empty.csv"
            path.write_text("", encoding="utf-8")
            with self.assertRaises(DataFileError):
                load_candidates(path)

    def test_missing_required_column_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.csv"
            path.write_text("candidate_name,current_stage\nAda,Screening\n", encoding="utf-8")
            with self.assertRaises(DataFileError):
                load_candidates(path)

    def test_duplicate_headers_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "duplicate_headers.csv"
            path.write_text("candidate_name,current_stage, stage_start_date,stage_start_date\nAda,Screening,2026-10-17,2026-10-18\n", encoding="utf-8")
            with self.assertRaisesRegex(DataFileError, "duplicate column names"):
                load_candidates(path)

    def test_blank_header_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "blank_header.csv"
            path.write_text("candidate_name,current_stage,stage_start_date,\nAda,Screening,2026-10-17,x\n", encoding="utf-8")
            with self.assertRaisesRegex(DataFileError, "blank column name"):
                load_candidates(path)

    def test_valid_rows_survive_other_invalid_rows(self):
        good = {"candidate_name": "Ada", "current_stage": "Screening", "stage_start_date": "2026-10-17", "assessment_scores": "", "assessment_status": "", "_row_number": "2"}
        bad = {**good, "candidate_name": "Ben", "stage_start_date": "tomorrow", "_row_number": "3"}
        valid, warnings = validate_candidate_row(good, date(2026, 10, 19), CONFIG)
        invalid, bad_warnings = validate_candidate_row(bad, date(2026, 10, 19), CONFIG)
        self.assertIsNotNone(valid)
        self.assertIsNone(invalid)
        self.assertTrue(bad_warnings)

    def test_invalid_date_is_excluded_with_warning(self):
        bad = {"candidate_name": "Ada", "current_stage": "Screening", "stage_start_date": "not-a-date", "assessment_scores": "", "assessment_status": "", "_row_number": "4"}
        record, warnings = validate_candidate_row(bad, date(2026, 10, 19), CONFIG)
        self.assertIsNone(record)
        self.assertTrue(any("invalid stage_start_date" in warning for warning in warnings))

    def test_non_padded_iso_date_is_rejected(self):
        row = {"candidate_name": "Ada", "current_stage": "Screening", "stage_start_date": "20261017", "assessment_scores": "", "assessment_status": "", "_row_number": "4"}
        record, warnings = validate_candidate_row(row, date(2026, 10, 19), CONFIG)
        self.assertIsNone(record)
        self.assertTrue(any("invalid stage_start_date" in warning for warning in warnings))

    def test_invalid_assessment_does_not_exclude_candidate(self):
        row = {"candidate_name": "Ada", "current_stage": "Screening", "stage_start_date": "2026-10-17", "assessment_scores": "[120]", "assessment_status": "completed", "_row_number": "4"}
        record, warnings = validate_candidate_row(row, date(2026, 10, 19), CONFIG)
        self.assertIsNotNone(record)
        self.assertIsNone(record["candidate_assessment_score"])
        self.assertTrue(any("Invalid assessment_scores" in warning for warning in warnings))

    def test_future_date_is_excluded_with_warning(self):
        future = {"candidate_name": "Ada", "current_stage": "Screening", "stage_start_date": "2026-10-20", "assessment_scores": "", "assessment_status": "", "_row_number": "5"}
        record, warnings = validate_candidate_row(future, date(2026, 10, 19), CONFIG)
        self.assertIsNone(record)
        self.assertTrue(any("in the future" in warning for warning in warnings))

    def test_unknown_stage_is_excluded_with_warning(self):
        unknown = {"candidate_name": "Ada", "current_stage": "Mystery Stage", "stage_start_date": "2026-10-17", "assessment_scores": "", "assessment_status": "", "_row_number": "6"}
        record, warnings = validate_candidate_row(unknown, date(2026, 10, 19), CONFIG)
        self.assertIsNone(record)
        self.assertTrue(any("unknown hiring stage" in warning for warning in warnings))

    def test_duplicate_names_excluded(self):
        rows = [
        {"candidate_name": "Ada", "email": "ada.one@example.com"},
        {"candidate_name": " ada ", "email": "ada.two@example.com"},
        {"candidate_name": "Ben", "email": "ben@example.com"},
        ]
        kept, warnings = exclude_duplicate_candidates(rows)
        self.assertEqual(
            [item["candidate_name"] for item in kept],
            ["Ada", " ada ", "Ben"],
        )
        self.assertFalse(warnings)


if __name__ == "__main__":
    unittest.main()
