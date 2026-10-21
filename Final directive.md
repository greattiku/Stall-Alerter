## Stall Alerter — Final Directive

## 1. Purpose

Build Stall Alerter, a configurable hiring-stage follow-up prioritisation application that helps recruiters identify candidates who have exceeded the expected time in their current recruitment stage.

The application must process candidate data from CSV files, apply company-specific recruitment rules, calculate follow-up urgency, rank eligible candidates, and produce an understandable report with recommended actions.

The solution must prioritise correctness, explainability, maintainability, and useful handling of imperfect data.

This directive defines the expected application behaviour and the implementation rules that must be followed.

## 2. Core Engineering Requirements

- Use Python for the application logic.
- Keep the core prioritisation logic deterministic and independent of external AI services.
- Separate responsibilities for configuration loading, data validation, calculations, ranking, reporting, and interface handling.
- Keep company-specific recruitment rules in configuration rather than hard-coding them into the core calculation logic.
- Make calculations and validation behaviour testable independently of the user interface.
- Provide clear error messages and actionable warnings.
- Do not silently substitute invented values for missing or invalid data.
- Preserve the distinction between follow-up urgency and candidate assessment performance.
- Keep the implementation straightforward and appropriate for an MVP. Avoid unnecessary complexity or infrastructure that does not support the product's current requirements.

## 3. Input CSV Requirements

The application must accept candidate information through a CSV file.

The expected fields are:

Field| Purpose
"candidate_name"| Candidate's name; required for ranking and reporting.
"current_stage"| Candidate's current recruitment stage; required.
"stage_start_date"| Date the candidate entered the current stage; required for calculations.
"assessment_scores"| Optional assessment score information.
"assessment_status"| Optional assessment status, such as complete, incomplete, or unknown.

If the application supports additional fields, such as email addresses, it must handle them consistently with the documented validation rules.

Column names must be interpreted consistently. If supported aliases or normalisation rules are used, they must be documented and tested rather than assumed.

## 4. Company-Specific Configuration

The application must support different companies with different hiring processes.

Each company should be able to supply a configuration file defining its own recruitment stages and rules.

The configuration must support:

- Stage names.
- Allowed days for each stage.
- Stage weights from 1 to 5.
- Recommended actions associated with each stage.

The initial implementation uses JSON configuration.

## Configuration rules

1. Every configured stage must have a valid name.
2. Allowed days must be valid non-negative integers.
3. Stage weights must be integers from 1 to 5.
4. Each stage must have an appropriate recommended action.
5. Invalid configuration must produce a clear error instead of silently falling back to invented rules.
6. An input record containing a stage that is not present in the selected configuration must not be ranked.
7. The configuration structure must be documented so that another company can create its own configuration correctly.

Adding another company should primarily involve supplying a valid configuration that follows the established schema. It should not require rewriting the core prioritisation formula or ranking logic.

## 5. Date Calculations

The application must use a reference date to calculate how long a candidate has remained in a stage.

The reference date must be injectable so calculations can be reproduced and tested using a fixed date.

## Days in stage

Calculate the calendar-day difference between the stage start date and the reference date.

"Days in Stage = Reference Date - Stage Start Date"

The implementation must use consistent date parsing and calendar-day calculations.

Days overdue

"Days Overdue = max(0, Days in Stage - Allowed Days)"

The application must not produce negative overdue days.

## Candidate status

- Stalled: The candidate has exceeded the allowed duration, meaning "Days Overdue > 0".
- On track: The candidate has not exceeded the allowed duration, including when the candidate has reached the allowed duration exactly.

A missing, invalid, or future stage start date must not be used to generate a normal ranking as if the date were valid.

## 6. Stage Priority Score

The Stage Priority Score measures follow-up urgency.

Use this formula:

"Stage Priority Score = Days Overdue × Stage Weight"

The score must be calculated from the number of overdue days and the configured stage weight.

Do not combine the Stage Priority Score with the Candidate Assessment Score.

Do not introduce extra scoring factors, arbitrary bonuses, or undocumented adjustments.

The same valid candidate data, company configuration, and reference date must produce the same score.

## 7. Candidate Assessment Score

Candidate Assessment Score must remain separate from follow-up priority.

Where valid scores are available for completed assessments, calculate the assessment average according to the application's documented score-parsing rules.

The application must distinguish between:

- A completed assessment with valid scores.
- An incomplete assessment.
- An unknown assessment status.
- A missing assessment status.
- A completed assessment with missing or invalid scores.
- Assessment information that cannot be evaluated reliably.

## Assessment rules

1. Missing assessment scores must not be converted to zero.
2. An incomplete assessment must not be treated as completed.
3. An unknown status must not be presented as a confirmed status.
4. Invalid scores must not be silently accepted as valid numerical results.
5. The report must not invent an assessment score when no valid score is available.
6. Assessment data problems must not automatically exclude an otherwise eligible candidate from follow-up prioritisation.
7. Assessment scores must never change a candidate's Stage Priority Score or ranking position.

The assessment score provides additional context about the candidate's assessment performance. It is not a measure of how urgently the recruiter needs to follow up.

## 8. Ranking Rules

Rank eligible candidate records using the following order:

1. Stalled candidates first.
2. Higher Stage Priority Score first.
3. Greater Days Overdue first when priority scores are equal.
4. Candidate name in alphabetical order as the final tie-breaker.

The ranking must be deterministic.

Candidate Assessment Score must not be used as a ranking criterion.

If candidates have identical values for the documented ranking criteria, any additional tie-breaking behaviour must be deterministic and documented.

## 9. Data Validation and Exclusions

The application must validate the input before calculating rankings.

Records that cannot be ranked reliably

Exclude a candidate record from ranking when essential information is missing or invalid, including:

- A missing or blank candidate name.
- A missing or blank current stage.
- A stage that is not recognised by the selected company configuration.
- A missing or invalid stage start date.
- A stage start date in the future relative to the reference date.

The application must explain why a record was excluded.

## --Duplicate records

Where valid email addresses are available and duplicate detection is part of the implementation, identify duplicate candidate records consistently.

Do not silently remove records without communicating the relevant validation issue.

The duplicate-handling policy must be deterministic and documented.

## --Email information

Missing or malformed email information should generate a warning where appropriate.

Email problems alone must not automatically exclude an otherwise eligible candidate from follow-up prioritisation.

## --Assessment information

Missing, incomplete, unknown, or invalid assessment information must be handled according to the assessment rules. It must not automatically disqualify a candidate whose core information is sufficient for ranking.

## --CSV and configuration errors

The application must handle:

- An empty CSV file.
- A CSV file missing required columns.
- Unreadable or malformed input.
- Missing configuration files.
- Invalid JSON.
- Missing required configuration fields.
- Invalid allowed-day or stage-weight values.
- An empty or unusable stage configuration.

Errors that prevent the application from processing the input must be reported clearly.

The application must not present a successful ranking when the underlying input or configuration could not be evaluated reliably.

## 10. Validation Feedback

The application must make validation outcomes understandable to the user.

Where applicable, communicate:

- The number of records read.
- The number of eligible records included in the ranking.
- The number of records excluded.
- The reasons for exclusions.
- Warnings about optional or malformed information.
- Whether assessment information was unavailable or could not be evaluated.

Validation messages should describe the actual issues found in the uploaded file.

Do not invent validation counts or claim that every record was ranked when some records were excluded.

Do not replace excluded records with fabricated candidates or placeholder scores.

## 11. Recommended Actions

The application must provide a recommended action based on the candidate's current stage and the selected company configuration.

The action should be appropriate to the stage and should help the recruiter determine a reasonable next step.

Recommended actions must be configuration-driven rather than embedded as fixed assumptions for every company.

The application must display recommendations for human consideration only.

It must not automatically send messages, contact candidates, reject candidates, or make hiring decisions.

## 12. Ranking Explanations

The application must explain why candidates appear at their respective positions in the ranking.

The explanation should be based on actual calculated values and documented ranking rules.

Where relevant, it should communicate:

- Whether the candidate is stalled or on track.
- How long the candidate has spent in the current stage.
- The allowed duration for that stage.
- The number of overdue days.
- The configured stage weight.
- The Stage Priority Score.
- The recommended action.
- The separate Candidate Assessment Score, if valid and available.

Do not generate explanations that contradict the calculations or imply that assessment performance determines follow-up urgency.

## 13. Report Requirements

Generate a spreadsheet-friendly CSV report containing the ranked candidate information.

The report should include these fields, using consistent names:

- Priority rank.
- Candidate name.
- Current stage.
- Days in stage.
- Allowed days.
- Days overdue.
- Stage weight.
- Stage Priority Score.
- Status.
- Candidate Assessment Score.
- Recommended action.
- Ranking explanation.

If the implementation uses different column names, the README and report behaviour must remain consistent.

Only eligible candidate records should appear as ranked candidates. Excluded records and their validation issues should be communicated through the application's validation feedback or a clearly documented validation report.

Missing assessment information must remain distinguishable from a numerical zero.

The report must not claim that excluded candidates have been ranked.

## 14. User Interface

Provide a usable Streamlit interface for working with the application.

The interface should allow the user to:

1. Upload a candidate CSV file.
2. Select or provide the applicable company configuration according to the implemented workflow.
3. Process the input.
4. View validation warnings and exclusions.
5. Inspect the prioritised candidate results.
6. Understand the ranking and recommended actions.
7. Download the generated CSV report.

The interface must communicate errors clearly and should not display misleading results when input processing fails.

Keep the interface focused on the MVP. Do not add unrelated functionality that increases complexity without improving the required workflow.

## 15. Testing Requirements

Provide automated tests for the core application behaviour.

Tests should cover the following areas.

## --Calculations

- Correct Days in Stage calculation.
- Correct Days Overdue calculation.
- Correct Stage Priority Score calculation.
- Zero overdue days when the candidate is within the allowed duration.
- On-track status at the exact allowed duration.
- Stalled status after the allowed duration is exceeded.
- Reproducible calculations using an injected reference date.

## --Ranking

- Stalled candidates appear before on-track candidates.
- Priority scores determine ordering among candidates.
- Overdue days provide the specified tie-breaker.
- Candidate name provides the alphabetical tie-breaker.
- Assessment scores do not influence priority ranking.
- Repeated execution with the same inputs produces consistent ordering.

## --Assessment handling

- Valid completed assessment scores.
- Incomplete assessment status.
- Unknown assessment status.
- Missing assessment status.
- Missing assessment scores.
- Invalid assessment scores.
- Assessment data issues that must not exclude an otherwise eligible candidate.

## --Validation

- Missing required CSV columns.
- Missing candidate name.
- Missing current stage.
- Missing stage start date.
- Invalid stage start date.
- Future stage start date.
- Unknown stage.
- Duplicate records according to the implemented policy.
- Missing or malformed email.
- Empty CSV input.
- Invalid or missing company configuration.
- Invalid stage weights and allowed-day values.

## --Reporting and interface

- Correct report columns.
- Correct representation of unavailable assessment scores.
- Correct handling of excluded records.
- Clear validation messages.
- Successful report generation for valid input.
- Appropriate error handling when processing fails.

Tests must verify actual behaviour rather than merely checking that functions execute without raising exceptions.

After changing code, rerun the relevant tests and, where appropriate, the full test suite.

## 16. Architecture and Maintainability

Maintain a clear separation of responsibilities.

The implementation should separate the following concerns where appropriate to the existing project structure:

- Configuration loading and validation.
- CSV reading and input validation.
- Date and priority calculations.
- Assessment-score handling.
- Candidate ranking.
- Recommended-action and explanation generation.
- Report generation.
- Streamlit interface and user interaction.
- Automated tests.

Avoid putting all application logic into the Streamlit interface file.

Keep core calculations independent of the interface so they can be tested without requiring a browser or user interaction.

Use clear function names, simple data flows, and appropriate error handling.

Do not introduce unnecessary dependencies, additional services, or complex abstractions that are not justified by the MVP.

## 17. AI Usage Boundaries

AI may assist with implementation, debugging, test development, documentation, and refinement.

However:

- Product rules must be defined explicitly.
- Generated code must be evaluated against those rules.
- AI must not introduce undocumented scoring formulas.
- AI must not merge assessment performance with follow-up urgency.
- AI must not invent candidate data or validation results.
- AI must not treat missing values as confirmed values.
- AI must not introduce automatic hiring decisions or candidate-contact actions.
- The deterministic ranking logic must remain independent of an external AI service.

Any optional future AI feature must have a clearly defined purpose and must not silently alter the core ranking behaviour.

## 18. Documentation Requirements

The project README must explain:

- What Stall Alerter does.
- The problem it solves.
- Prerequisites and installation.
- How to run the application.
- The expected CSV structure.
- How to create and select a company configuration.
- How the priority formula works.
- How assessment scores are handled.
- How records are validated and excluded.
- How to run automated tests.
- How to generate and download the report.
- Known limitations of the current MVP.

The project should also include:

- "intent.md" — the product problem, users, goals, and guiding principles.
- "Final directive.md" — the implementation requirements and rules.
- "log.md" — the development process, outcomes, and reflection.
- Example CSV data and a valid example configuration.
- Automated tests for the core logic.

Documentation must describe the implementation that actually exists. Do not claim that a feature is complete unless it has been implemented and verified.

## 19. Acceptance Criteria

The implementation is acceptable when the following conditions have been verified:

1. A valid CSV can be processed using a valid company configuration.
2. Stage durations, overdue days, and Stage Priority Scores are calculated correctly.
3. The candidate ranking follows the documented rules.
4. A candidate at the exact allowed duration remains on track.
5. Assessment performance does not influence follow-up priority.
6. Missing assessment scores are not converted to zero.
7. Invalid records are excluded from ranking with appropriate explanations.
8. Optional information problems are handled without unnecessary candidate exclusion.
9. Different companies can define their own recruitment stages and rules through configuration.
10. The report contains the required ranking information and explanations.
11. The Streamlit interface communicates processing outcomes and validation issues clearly.
12. Automated tests cover the principal calculations, ranking rules, validation scenarios, and relevant edge cases.
13. The setup instructions and README match the actual implementation.
14. The application does not automatically contact candidates or make hiring decisions.

Each criterion must be checked against the actual implementation before it is described as verified.

## 20. Final Instruction

Build Stall Alerter as a focused, explainable, configuration-driven hiring-stage prioritisation tool.

Prioritise correct calculations, deterministic ranking, useful validation, and maintainable code over unnecessary features.

Keep follow-up urgency separate from candidate assessment performance. Make company-specific recruitment rules configurable. Explain why candidates are ranked as they are. Handle invalid data honestly, and leave hiring decisions and candidate-contact actions to human users.

Use AI to accelerate implementation, but treat the requirements in this directive as the source of truth for expected behaviour.

The final result must be a working, understandable, and testable application whose behaviour matches these requirements.