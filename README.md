## Stall Alerter

Stall Alerter helps recruiters identify candidates who have spent longer than the configured allowance in a hiring stage. It provides a local Streamlit interface for maintaining candidate records and company stage settings, alongside a command-line interface (CLI).

Both interfaces use the same validation, calculation, ranking, and reporting modules, helping maintain consistent behaviour across the application.

## Features

- Configurable hiring stages: Define your company's stages, allowed days, stage weights, and recommended actions.
- Candidate management: Add, edit, delete, and import candidate records.
- Follow-up prioritisation: Identify stalled candidates and rank them according to documented business rules.
- Assessment separation: Keep Candidate Assessment Score independent from follow-up urgency.
- Data validation: Identify missing or invalid candidate information and explain exclusions.
- Ranking explanations: Understand why candidates appear in a particular order.
- CSV reports: Generate and download spreadsheet-friendly reports.
- Local persistence: Store candidate records and company settings in local project files.
- Automated tests: Verify the core calculations, ranking rules, and validation behaviour.



## 1. Requirements

- Python 3.10 or newer.
- Streamlit and pandas for the user interface.
- The dependencies listed in "requirements.txt".

The core business logic lives in "src/stall_alerter/".



## 2. Installation

Run the commands from the project root, "stall-alerter/".

## --Windows PowerShell

Create a virtual environment:

```
python -m venv .venv
```

Activate it:

```
.venv\Scripts\Activate.ps1
```
Install the dependencies:

```
python -m pip install -r requirements.txt
```

If PowerShell prevents activation because of its execution policy, consult the official Python documentation for virtual environments and your organisation's security guidance rather than changing system-wide security settings unnecessarily.

## --macOS and Linux

Create a virtual environment:
```
python3 -m venv .venv
```

Activate it:

```
source .venv/bin/activate
```

Install the dependencies:

```
python -m pip install -r requirements.txt
```

## --Verify Python

Check the Python version:

Windows:

```
python --version
```

macOS/Linux:

```
python3 --version
```
The project requires Python 3.10 or newer.


## 3. Start the Streamlit App

After installing the dependencies and activating the virtual environment, run:

```
python -m streamlit run app.py
```

This command works in Windows PowerShell, macOS, and Linux.

Streamlit normally opens the application in your default browser. If it does not, follow the local URL printed in the terminal.

- First-Time Setup

Start in Company settings and add the hiring stages your company actually uses.

For each stage, configure:

- Stage name.
- Allowed number of days.
- Stage weight from 1 to 5.
- Recommended action.

No candidate records or company-specific stage values are pre-populated.

After configuring the stages, open Manage candidates to add candidate records or import a CSV file.

The application persists candidate records in:

"data/hiring_board.csv"

Company settings are saved in:

"config/company_settings.json"

The dashboard uses the saved files, supports a reference date, search and filters, explains ranking, and can generate and download a CSV report.

## 3b. Candidate CSV Format

The CSV must contain the following required columns:
(see https://github.com/greattiku/Stall-Alerter/blob/main/data/sample_candidate_import.csv for sample sheet)


Column| Required?| Description

"candidate_name"| Yes| Candidate's name.

"email" | No | Candidate's Email Address.

"current_stage"| Yes| Current hiring stage; it must match a stage configured in Company settings.

"stage_start_date"| Yes| Date the candidate entered the current stage, using "YYYY-MM-DD".

"assessment_scores"| No| JSON array of percentage scores from 0 to 100, such as "[82, 91]", stored as a CSV cell.

"assessment_status"| No| Assessment status: "completed", "incomplete", or "unknown". The alias "complete" is also accepted for "completed".

## 3c. Getting Sample Data

Use Manage candidates → Download sample candidate CSV to download an example containing:

- Completed assessments with scores.
- Incomplete assessments.
- Unknown assessment statuses.
- Missing or invalid candidate information.

The sample provides a way to exercise the application's validation and reporting workflow.

Valid sample rows use the configured sample stage names. If your company uses different stages, update the sample values to match your configuration before importing.

## 3d. Import Behaviour

Use Import a hiring-board CSV to import candidate records.

Importing appends records by default. Enable the replace option only when you intend to replace the existing hiring board.

The application validates required columns before importing. Review data-quality warnings on the dashboard, particularly those relating to missing dates, unknown stages, and other invalid candidate details.



## 4. Business Rules

## --Days in Stage

The application calculates the calendar-day difference between the reference date and the candidate's stage start date.

"Days in Stage = Reference Date - Stage Start Date"

## --Days Overdue

"Days Overdue = max(0, Days in Stage - Allowed Days)"

## --Candidate Status

- Stalled: The candidate has exceeded the allowed duration; overdue days are greater than zero.
- On track: The candidate has not exceeded the allowed duration. Reaching the allowed duration exactly still counts as on track.

## --Stage Priority Score

"Stage Priority Score = Days Overdue × Stage Weight"

The stage weight is configured by the company and must be between 1 and 5.

## --Candidate Assessment Score

Candidate Assessment Score is an independent metric.

A score is displayed only when the assessment status is explicitly "completed" and valid assessment scores exist.

- Missing assessment scores are represented as "Unknown".
- Incomplete assessment results are represented as "Incomplete".
- Unknown or missing assessment information is not treated as a score of zero.

Assessment scores do not affect candidate urgency, status, priority score, or ranking.

## --Ranking Order

Candidates are ranked according to these rules:

1. Stalled candidates appear before on-track candidates.
2. Among stalled candidates, higher Stage Priority Scores appear first.
3. Candidates with equal priority scores are ordered by days overdue, descending.
4. Candidate name is the final alphabetical tie-breaker for stalled candidates.
5. On-track candidates follow alphabetically.

The ranking is deterministic for the same input data, configuration, and reference date.

## Duplicate Candidate Validation

- Duplicate candidate records are identified using the candidate's email address rather than their name.
- Candidates with the same name but different email addresses are treated as separate candidates.
- Duplicate email records are flagged during validation to prevent the same candidate from appearing multiple times in the ranked results.
- Records with missing or invalid required fields, such as candidate name, current stage, or stage start date, are excluded from ranking and reported with validation warnings.
- Missing assessment scores do not automatically exclude an otherwise valid candidate. Assessment results are handled separately from follow-up priority.

## Recommended Actions

Recommended actions are configured suggestions intended to help recruiters decide what to do next.

The application does not automatically contact, reject, or retain candidates.



## 5. Command-Line Workflow

The CLI remains available and shares the same calculation and ranking logic as the Streamlit interface.

By default, it uses:

- Input: "data/hiring_board.csv"
- Configuration: "config/company_settings.json"
- Output: "reports/priority_report.csv"

Configure at least one hiring stage and add candidate records before running the CLI. The CLI requires a valid, non-empty stage configuration and at least one candidate row.

## Windows PowerShell

Set "PYTHONPATH" and run the CLI:

```
$env:PYTHONPATH = "$PWD\src"

python -m stall_alerter.main `
  --input data/hiring_board.csv `
  --config config/company_settings.json `
  --output reports/priority_report.csv `
  --as-of 2026-10-19
```

## macOS and Linux

```
PYTHONPATH=src python -m stall_alerter.main \
  --input data/hiring_board.csv \
  --config config/company_settings.json \
  --output reports/priority_report.csv \
  --as-of 2026-10-19
```

The example reference date makes the calculation reproducible. Replace it with your intended evaluation date.

Omit "--as-of" to use today's local date.



## 6. Running the Tests

The tests use temporary files and do not require a real hiring board.

Run the tests from the project root with the project dependencies installed.

## Windows PowerShell

```
$env:PYTHONPATH = "$PWD\src"
python -m unittest discover -s tests -v
```

## macOS and Linux
```
PYTHONPATH=src python -m unittest discover -s tests -v
```

The automated tests cover core application behaviour, including calculations, ranking, assessment handling, and validation scenarios.

To check the Streamlit entry point for Python syntax errors:

```
python -m py_compile app.py
```

This command checks syntax; it does not replace running the application and testing the interactive workflow in a browser.


## 7. Project Structure

stall-alerter/
├── app.py
├── config/
│   └── company_settings.json
├── data/
│   └── hiring_board.csv
├── reports/
│   └── priority_report.csv
├── src/
│   └── stall_alerter/
│       └── ...
├── tests/
│   └── ...
├── requirements.txt
├── intent.md
├── Final directive.md
├── log.md
└── README.md

The structure above summarises the main project files. The exact contents of the source and test directories depend on the implementation.


## 8. Important Files

File or directory| Purpose
"app.py"| Streamlit presentation layer and local candidate-management and settings interface.
"src/stall_alerter/"| Shared business logic and CLI implementation.
"data/hiring_board.csv"| Candidate input data; starts empty.
"config/company_settings.json"| Company-specific hiring-stage settings; starts unconfigured.
"reports/priority_report.csv"| Generated report output.
"tests/"| Automated tests using temporary test data.
"intent.md"| Product problem, goals, intended users, and guiding principles.
"Final directive.md"| Detailed implementation requirements and expected behaviour.
"log.md" and "logs/"| Development records and project logs.

The generated report is ignored by Git so candidate information is not accidentally committed. Confirm that your ".gitignore" also excludes any real candidate input files and other sensitive data.


## 9. Privacy and Scope

Stall Alerter stores candidate records and company settings in local files within the project directory.

The application does not require a database, cloud service, external applicant tracking system (ATS) connection, paid AI API, or automatic candidate communication.

Local storage does not automatically encrypt candidate information. Protect the project directory, backups, and generated reports because they may contain personal candidate data.

Do not commit real candidate information to a public or shared repository.

## --Current Scope

Stall Alerter is a focused MVP for recruitment-stage follow-up prioritisation.

It provides configurable hiring rules, deterministic calculations, ranking explanations, data validation, candidate management, CSV reporting, and a Streamlit interface.

The application supports human decision-making. It does not automatically make hiring decisions or contact candidates.

The central principle is to make follow-up urgency visible, explainable, configurable, and separate from candidate assessment performance.
