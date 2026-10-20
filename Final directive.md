# Stall Alerter — Final Business Rules and Implementation Directive

<!-- This is the implementation contract; changes to these rules should be agreed before coding. -->

## Input and configuration
Required CSV columns: `candidate_name`, `current_stage`, `stage_start_date`. Optional columns: `assessment_scores`, `assessment_status`. Dates use `YYYY-MM-DD`. Assessment scores use a JSON array of percentages from 0 to 100, and a final average is calculated only when status is explicitly `completed`.

JSON configuration contains a non-empty `stages` object. Each stage must define a non-negative integer `allowed_days`, an integer `weight` from 1 through 5, and a non-empty `recommended_action`. Boolean values are not accepted as integers.

## Calculations
- `days_in_stage = (reference_date - stage_start_date).days`
- `overdue_days = max(0, days_in_stage - allowed_days)`
- `status = On track` when `overdue_days == 0`; otherwise `Stalled`.
- `stage_priority_score = overdue_days * stage_weight`
- `candidate_assessment_score = arithmetic mean of valid completed assessment scores`; no score is invented for missing or incomplete data.

The reference date is the local current date by default and can be supplied with `--as-of YYYY-MM-DD`. Dates in the future are invalid for the run and are excluded with a warning.

## Ranking
1. Stalled before On track.
2. Stalled records by Stage Priority Score descending.
3. Ties by overdue days descending.
4. Remaining ties alphabetically by candidate name, case-insensitively.
5. On-track records alphabetically by candidate name.

Candidate Assessment Score is not part of the ranking key.

## Error policy
Fatal errors: missing/unreadable input file, missing required CSV columns, empty CSV/no data rows, missing or malformed configuration, invalid configuration, and report write failures. These stop the run with an understandable message.

Recoverable row errors: blank name/stage/date, invalid date, future date, unknown stage, or ambiguous duplicate candidate name. Invalid rows are excluded and warnings are shown. All valid rows sharing a repeated candidate name are excluded; records are neither silently merged nor arbitrarily selected.

Invalid assessment values produce a warning and `Unknown` assessment display, but do not invalidate otherwise usable stage information. An explicit `incomplete` status displays `Incomplete`, even if partial scores are present.

## Output
The report includes rank, candidate, stage, days in stage, allowed days, overdue days, stage weight, Stage Priority Score, status, Candidate Assessment Score, recommended action, and ranking explanation. It is CSV for spreadsheet use.

## Streamlit and persistence
The Streamlit UI and CLI must use the same candidate CSV, company JSON settings, and shared validation/calculation/ranking/report modules. Candidate data and stage configuration start empty; no synthetic candidate board or sample output is shipped. UI CRUD and settings changes are persisted to local files.

## AI and future work
No AI API is required for the MVP. Calculations, classification, ranking, explanations, and stage actions are deterministic. A later optional AI feature may draft an internal follow-up message from known facts, but must not alter scores or make hiring decisions. Optional deadline warnings are also future scope.
