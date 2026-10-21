## Stall Alerter — Product Intent

## 1. Project Overview

Stall Alerter is a hiring-stage follow-up prioritisation tool designed to help recruiters identify candidates who have spent longer than the allowed time at a particular stage of the recruitment process.

The project was developed as part of MUST Company's Re-born AI Native Engineer task. The goal was to build a useful, working solution while demonstrating deliberate product thinking, effective AI-assisted engineering, structured implementation, and responsibility for the quality of the final result.

The initial version is a Python-based application that accepts candidate information from a CSV file, evaluates how long candidates have spent in their current hiring stages, calculates follow-up urgency, and produces a prioritised report with recommended actions.

The application is intended to support recruiters in making follow-up decisions. It is not intended to replace human judgement or make hiring decisions automatically.

## 2. The Problem

Recruitment processes typically involve multiple stages, including screening, technical interviews, HR interviews, executive interviews, and offers.

Candidates may remain at a particular stage longer than the organisation intends. When recruiters manage several candidates across different stages, it can become difficult to determine which candidates need attention first.

A candidate who has been waiting too long may require an immediate follow-up, while another candidate who is still within the expected timeframe may not require the same level of urgency.

Without a consistent way to assess this urgency, recruiters may have to manually review candidate records, calculate delays, and decide which follow-up tasks should receive attention first.

Stall Alerter addresses this problem by applying configurable rules to candidate data and presenting the results in a clear, prioritised format.

## 3. Intended Users

The primary users are recruiters, recruitment coordinators, and hiring teams responsible for monitoring candidates throughout the hiring process.

The application is particularly relevant to teams that:

- Manage multiple candidates across different recruitment stages.
- Need to identify candidates who have exceeded expected stage timelines.
- Want a consistent way to prioritise follow-up activities.
- Track recruitment information in spreadsheets or CSV files.
- Have different hiring processes, deadlines, and priorities depending on their organisation.

## 4. Product Goal

The goal is to provide a practical tool that answers three important questions:

1. Which candidates have exceeded the expected time for their current hiring stage?
2. Which stalled candidates should receive attention first?
3. What action should the recruiter consider taking next?

The application should reduce the effort required to review hiring-stage delays and help recruiters focus their attention where it is most needed.

## 5. Intended Solution

Stall Alerter accepts candidate information through a CSV file and evaluates each eligible record against a company's recruitment configuration.

The intended workflow is:

1. A user selects or prepares a CSV file containing candidate information.
2. The application validates the input and identifies records that cannot be evaluated reliably.
3. The application loads the applicable company configuration.
4. It calculates the number of calendar days each eligible candidate has spent in their current stage.
5. It compares the elapsed time with the allowed duration for that stage.
6. It calculates the number of overdue days and the Stage Priority Score.
7. It determines whether the candidate is on track or stalled.
8. It ranks eligible candidates according to follow-up urgency.
9. It provides recommended actions and explanations for the ranking.
10. It produces a report that can be viewed and used in spreadsheet software.

The application should make its results understandable rather than presenting unexplained scores.

## 6. Configurable Recruitment Processes

Different companies do not necessarily use the same recruitment stages, deadlines, or follow-up procedures.

One company may have a screening stage followed by technical and HR interviews. Another may include an executive interview or additional stages.

For this reason, the application is designed around company-specific configuration rather than assuming that every organisation follows one fixed hiring process.

Each company's configuration should define:

- The recruitment stages used by that company.
- The allowed number of calendar days for each stage.
- The weight assigned to each stage.
- The recommended action associated with each stage.

The configuration is maintained separately from the core application logic.

This approach is intended to make it possible to support additional companies by supplying their own valid configuration instead of rewriting the scoring and ranking logic for each organisation.

The initial configuration uses JSON. Each configuration must follow the structure expected by the application and contain valid stage definitions, deadlines, weights, and recommended actions.

## 7. Product Logic and Scoring Decisions

## 7.1 Days in Stage

The application calculates how many calendar days have elapsed between a candidate's stage start date and the reference date used for the evaluation.

The reference date can be supplied during execution so that the calculations can be reproduced and tested consistently.

## 7.2 Days Overdue

The number of overdue days is calculated as:

"Days Overdue = max(0, Days in Stage - Allowed Days)"

A candidate is considered stalled only when the number of overdue days is greater than zero.

A candidate who has reached the allowed duration exactly is still considered on track.

## 7.3 Stage Priority Score

The Stage Priority Score measures the urgency of following up with a candidate.

"Stage Priority Score = Days Overdue × Stage Weight"

The stage weight represents the relative importance assigned to delays at that recruitment stage.

A higher score indicates greater follow-up priority under the configured rules. It does not indicate that a candidate is more qualified or more suitable for the role.

## 7.4 Candidate Ranking

Eligible candidates should be ranked using the following order:

1. Stalled candidates appear before candidates who are still on track.
2. Higher Stage Priority Scores appear first.
3. Greater numbers of overdue days take precedence when priority scores are equal.
4. Candidate name is used alphabetically as the final tie-breaker.

The ranking should be deterministic: the same valid input, configuration, and reference date should produce the same results.

## 7.5 Candidate Assessment Score

Candidate Assessment Score is kept separate from Stage Priority Score.

Where valid assessment scores are available, the application may calculate an average using valid scores associated with completed assessments.

Assessment information must be handled carefully:

- A completed assessment with valid scores can contribute to the assessment average.
- An incomplete assessment must not be treated as a completed assessment.
- An unknown assessment status must remain distinguishable from a known status.
- Missing assessment scores must not be treated as zero.
- Invalid or unavailable assessment information must not be presented as a valid numerical score.

Assessment performance must not affect the candidate's follow-up ranking.

This separation is a deliberate product decision. The purpose of the priority ranking is to identify who needs attention first, not to rank candidates by performance.

## 8. Data Validation and Error Handling

The application should not silently produce misleading rankings from records that cannot be evaluated reliably.

The validation process should account for:

- Missing required CSV columns.
- Missing or blank candidate names.
- Missing, invalid, or future stage start dates.
- Missing or blank current hiring stages.
- Hiring stages that do not exist in the selected company configuration.
- Duplicate candidate records, using valid email information where available.
- Missing or malformed email values.
- Missing, invalid, or incomplete assessment information.
- Empty CSV files.
- Invalid company configuration files.
- Missing required configuration fields or invalid configuration values.

Records that lack essential information for determining follow-up urgency, such as a valid candidate name, recognised stage, or valid stage start date, should be excluded from ranking and reported appropriately.

Missing or malformed email information should generate an appropriate warning where relevant, rather than automatically disqualifying an otherwise valid candidate record.

Assessment data problems should not automatically exclude an otherwise eligible candidate from follow-up prioritisation. The application should preserve the distinction between missing assessment information and an actual score.

Validation warnings should explain what went wrong and help the user correct the source data.

The application should distinguish between records that can be ranked, records that require attention because of data-quality issues, and errors that prevent the file or configuration from being processed.

## 9. Recommended Actions and Explainability

The application should provide a recommended action based on the candidate's current hiring stage and the configured recruitment rules.

These recommendations are intended to guide the recruiter, not to perform the action automatically.

The report should also explain the basis of the ranking by presenting relevant information such as:

- Current stage.
- Days spent in the stage.
- Allowed days.
- Days overdue.
- Stage weight.
- Stage Priority Score.
- Candidate status.
- Candidate Assessment Score, where valid and available.
- Recommended action.
- Explanation of the ranking.

This allows users to understand why a candidate appears at a particular position in the report.

## 10. Scope and Boundaries

The initial scope is a focused, deterministic MVP.

It includes:

- CSV-based candidate input.
- Company-specific recruitment configuration.
- Stage-duration calculations.
- Overdue calculations.
- Stage Priority Score calculations.
- Candidate ranking.
- Assessment-score handling that is independent of follow-up priority.
- Data validation and warnings.
- Recommended actions.
- A spreadsheet-friendly report.
- A user interface for interacting with the application.
- Automated tests for core calculations, ranking, validation, and important edge cases.

The core prioritisation logic should not depend on an external AI service. This makes the results predictable, testable, and explainable.

AI is used primarily to support the engineering workflow, including requirements development, implementation assistance, and iterative refinement. Any future AI-generated recruiter assistance, such as drafting a follow-up message, would be an optional enhancement and should not change the deterministic ranking rules.

The application must not automatically contact candidates, reject candidates, decide whom to retain, or predict candidate withdrawal as part of the core MVP.

## 11. Success Criteria

The project is considered successful when:

- A valid CSV can be processed using a valid company configuration.
- Days in stage, days overdue, and priority scores are calculated correctly.
- Candidates are ranked according to the documented rules.
- Candidates at the exact allowed duration remain on track.
- Assessment scores do not influence follow-up priority.
- Missing assessment information is not silently converted to zero.
- Invalid records are handled with appropriate warnings or exclusions.
- Different company configurations can define different recruitment processes.
- Recommended actions and ranking explanations are understandable.
- The report is usable in spreadsheet software.
- Automated tests cover the principal calculations and relevant edge cases.
- The application can be run and understood using the project documentation.

## 12. Guiding Principle

Stall Alerter is built around one central principle:

Make follow-up urgency visible, explainable, configurable, and separate from candidate performance.

The application should help recruiters make better-informed decisions by turning recruitment-stage data into a clear picture of where attention is needed, while leaving the final decisions and actions to people.