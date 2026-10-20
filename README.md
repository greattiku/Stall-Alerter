# Stall Alerter

Stall Alerter helps recruiters identify candidates who have spent longer than the configured allowance in a hiring stage. It provides a local Streamlit interface for maintaining candidate records and company stage settings, plus the original command-line workflow. Both interfaces use the same validation, calculation, ranking, and report modules.

## Requirements

- Python 3.10 or newer.
- Streamlit and pandas for the UI; the business logic remains in `src/stall_alerter/`.

## Setup (Windows PowerShell)

Run from the project root (`stall-alerter/`):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Start the Streamlit app

```powershell
python -m streamlit run app.py
```

The app opens in your browser. Start in **Company settings** and add the hiring stages your company actually uses. For each stage, configure allowed days, a weight from 1–5, and a recommended action. No candidate records or company-specific stage values are pre-populated.

Then open **Manage candidates** to add records or import a CSV. Add/edit/delete actions persist to `data/hiring_board.csv`. Stage settings persist to `config/company_settings.json`. The dashboard uses the saved files, supports a reference date, search and filters, explains ranking, and can generate/download a CSV report.

## Candidate CSV format

The CSV must contain these columns:

- `candidate_name` — required.
- `current_stage` — required and must match a stage configured in Company settings.
- `stage_start_date` — required, `YYYY-MM-DD`.
- `assessment_scores` — optional JSON array of percentage values from 0 to 100, e.g. `[82, 91]` stored as a CSV cell.
- `assessment_status` — optional `completed`, `incomplete`, or `unknown`; `complete` is also accepted as an alias for `completed`.

Use **Manage candidates → Download sample candidate CSV** to get a ready-to-import example covering scored completed assessments, incomplete/unknown assessments, and missing or invalid candidate details. Import it with **Import a hiring-board CSV** to test the workflow; valid rows use the configured sample stage names, so update the stages in the sample if your configuration differs. Import appends by default; check the replace option only when you intend to replace the current board. The app validates required columns before importing. Review data-quality warnings on the dashboard, especially missing dates and unknown stages.

## Command-line workflow

The CLI remains available and shares the same calculation and ranking logic. It reads `data/hiring_board.csv`, `config/company_settings.json`, and writes `reports/priority_report.csv` by default. Configure at least one stage and add candidate records before running it.

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m stall_alerter.main --input data/hiring_board.csv --config config/company_settings.json --output reports/priority_report.csv --as-of 2026-10-19
```

Omit `--as-of` to use today's local date. The CLI requires at least one candidate row and a valid non-empty stage configuration.

## Business rules

- Days in stage = reference date minus stage start date in calendar days.
- Days overdue = `max(0, days_in_stage - allowed_days)`.
- Status is `Stalled` only when overdue days are greater than zero.
- Stage Priority Score = `days_overdue * stage_weight`.
- Candidate Assessment Score is an independent metric. A score is displayed only when assessment status is explicitly `completed` and valid scores exist. Missing scores are `Unknown`; incomplete results are `Incomplete`.
- Ranking order: stalled first; among stalled candidates, Stage Priority Score descending, then days overdue descending, then candidate name alphabetically. On-track candidates follow alphabetically.
- Assessment score never affects urgency, status, priority score, or ranking.
- Duplicate candidate names are treated as ambiguous and excluded from the ranked output with a warning. They are not silently merged.
- Recommended actions are configured suggestions only. The app does not contact, reject, or retain candidates automatically.

## Files and persistence

- `app.py` — Streamlit presentation layer and local CRUD/settings UI.
- `src/stall_alerter/` — shared CLI/business logic.
- `data/hiring_board.csv` — real candidate input data; starts empty.
- `config/company_settings.json` — company settings; starts unconfigured.
- `reports/priority_report.csv` — generated output, ignored by Git so candidate information is not accidentally committed.
- `tests/` — automated tests, with candidate examples created temporarily during tests rather than stored as production sample data.
- `intent.md`, `Final directive.md`, `log.md`, and `logs/` — product constraints and development records.

## Tests

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m unittest discover -s tests -v
```

The tests use temporary files and do not require a real hiring board. Install dependencies with `python -m pip install -r requirements.txt` before starting Streamlit. The UI itself can be syntax-checked with `python -m py_compile app.py`; run it with `python -m streamlit run app.py` to verify the interactive experience in a browser.

## Privacy and scope

Candidate records and company settings stay in local files in the project directory. No database, cloud service, external ATS connection, paid AI API, or automatic communication is used. Protect the project directory and generated reports because they may contain candidate information.
