"""Command-line entry point for the Stall Alerter workflow."""

import argparse
from datetime import date
import re
import sys
from pathlib import Path

from .calculations import calculate_candidate
from .config import ConfigurationError, load_config
from .data_loader import DataFileError, load_candidates
from .ranking import rank_candidates
from .report import write_report
from .validation import exclude_duplicate_candidates, validate_candidate_row


def build_parser() -> argparse.ArgumentParser:
    """Define the CLI options so recruiters can choose input, settings, date, and output."""
    parser = argparse.ArgumentParser(description="Rank stalled hiring candidates using company rules.")
    parser.add_argument("--input", default="data/hiring_board.csv", help="Path to hiring-board CSV.")
    parser.add_argument("--config", default="config/company_settings.json", help="Path to company JSON settings.")
    parser.add_argument("--output", default="reports/priority_report.csv", help="Path for generated CSV report.")
    parser.add_argument("--as-of", help="Reference date in YYYY-MM-DD format; defaults to today's local date.")
    return parser


def run(input_path: str, config_path: str, output_path: str, reference_date: date) -> int:
    """Run the end-to-end workflow and return a process exit code."""
    try:
        config = load_config(config_path)
        rows = load_candidates(input_path)
    except (ConfigurationError, DataFileError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    valid_inputs = []
    warnings: list[str] = []
    for row in rows:
        record, row_warnings = validate_candidate_row(row, reference_date, config)
        warnings.extend(row_warnings)
        if record is not None:
            valid_inputs.append(record)
    valid_inputs, duplicate_warnings = exclude_duplicate_candidates(valid_inputs)
    warnings.extend(duplicate_warnings)

    calculated = [calculate_candidate(record, reference_date) for record in valid_inputs]
    ranked = rank_candidates(calculated)
    try:
        report_path = write_report(ranked, output_path)
    except OSError as exc:
        print(f"Error: could not write report: {exc}", file=sys.stderr)
        return 2

    print(f"Reference date: {reference_date.isoformat()}")
    print(f"Candidate rows read: {len(rows)}")
    print(f"Candidates included in report: {len(ranked)}")
    print(f"Stalled: {sum(item['status'] == 'Stalled' for item in ranked)} | On track: {sum(item['status'] == 'On track' for item in ranked)}")
    print(f"Report written to: {report_path}")
    if warnings:
        print("\nData-quality warnings:")
        for warning in warnings:
            print(f"- {warning}")
    if not ranked:
        print("No candidates could be included. Review the warnings and source files.")
    return 0


def main() -> None:
    """Parse command-line arguments and execute the application."""
    args = build_parser().parse_args()
    try:
        # Keep the CLI date format consistent with the CSV contract.
        if args.as_of and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.as_of):
            raise ValueError("date must use YYYY-MM-DD")
        reference_date = date.fromisoformat(args.as_of) if args.as_of else date.today()
    except ValueError:
        print("Error: --as-of must use YYYY-MM-DD, for example 2026-10-19.", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(run(args.input, args.config, args.output, reference_date))


if __name__ == "__main__":
    main()
