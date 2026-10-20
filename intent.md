# Stall Alerter — Product Intent

## Problem
Recruiters can lose track of candidates who have spent too long in their current hiring stage. Stall Alerter turns a company's candidate-stage records into a transparent, ranked follow-up queue.

## Intended users
Recruiters and hiring operations teams who maintain candidate-stage data in a CSV export or enter it through the local Streamlit interface.

## Goals
- Maintain candidate records with create, edit, delete, and CSV import actions.
- Configure company-specific stage deadlines, weights, and recommended actions.
- Calculate calendar days in each candidate's current stage.
- Identify stalled candidates using configured allowed durations.
- Calculate Stage Priority Score as overdue days multiplied by stage weight.
- Calculate a separate assessment average only from explicitly completed, valid 0–100 assessment results.
- Rank candidates deterministically and explain each ranking.
- Filter the dashboard, generate a CSV report, and retain a compatible CLI.
- Warn about data problems without silently merging ambiguous candidate records.

## Non-goals
No database, accounts, external ATS integration, automatic emails, automated hiring decisions, withdrawal predictions, or mandatory AI service. The MVP does not decide whether a candidate should be retained or rejected.

## Design decisions
- Streamlit is the presentation layer; the existing tested Python modules remain the single source of truth for validation, calculations, ranking, and CSV report generation.
- Candidate data is stored in `data/hiring_board.csv`; company stage settings are stored in `config/company_settings.json`.
- New candidate and settings writes use temporary files before replacement to reduce the risk of partial writes.
- The repository starts with an empty candidate board and an unconfigured stage list; no synthetic candidate data or generated sample report is shipped.
- ISO dates (`YYYY-MM-DD`) and calendar-day differences are used.
- Stage names are matched without case sensitivity or surrounding whitespace.
- Unknown stages and invalid dates are excluded from ranking with warnings.
- Repeated candidate names are treated as ambiguous; all matching rows are excluded instead of choosing or merging records silently.
- Missing assessment data is `Unknown`; explicitly incomplete assessments are `Incomplete`; a final average is shown only when status is `completed` and valid scores are provided.
- Assessment results never influence stalled status, priority score, or ranking.
- Recommended actions are suggestions only and have no side effects.

## Assumptions
- Assessment scores use a common percentage scale from 0 through 100.
- `assessment_scores` is a JSON array stored inside a CSV cell.
- `assessment_status` is `completed`, `incomplete`, or `unknown`; an absent status does not imply completion.
- Each candidate should have one current row in the hiring board.
- A company configures an action for every stage it uses before adding candidates to that stage.

## Future ideas (not in current scope)
Optional ATS import connectors, multi-user access, deadline notifications, named assessment components, and an optional AI-generated internal follow-up draft. AI must remain separate from all deterministic calculations and must never invent missing facts.
