## Stall Alerter — Two-Day Engineering Log

Scope: Product discovery, prompt iteration, implementation, testing, raising the load, debugging, and validation.

- This log records engineering work and outcomes; the separate unlearning reflection is documented elsewhere.

---

Day 1 — Research, Product Decisions, Prompt Design, and Core Build

Objective

Turn the hiring-stage follow-up problem into a focused MVP that ranks candidates by follow-up urgency, explains what action to take, and keeps recruitment assessment performance separate from urgency.

Research and Back-and-Forth Product Discovery

- Investigated the problem from the recruiter’s point of view and iterated with AI on what the tool should prioritize, what information it needed, and how a recruiter would use the output.
- Compared possible prioritization approaches instead of accepting the first proposed scoring idea. Refined the requirements around two distinct questions: Who needs follow-up first? and How did the candidate perform in assessments?
- Rejected combining assessment performance with the follow-up priority calculation. A high assessment score should not hide a candidate who is overdue, and a low or missing assessment score should not automatically make an otherwise valid candidate disappear from the follow-up queue.
- Settled on a separate Stage Priority Score and Candidate Assessment Score. The priority score is calculated as "overdue_days × stage_weight"; the assessment score is displayed separately to support the recruiter’s decision about whether the candidate is worth retaining.
- Refined the stage logic so each company can configure the number of days allowed at each hiring stage, its stage weight, and the recommended action. This avoids hard-coding one company’s recruitment policy for every employer.
- Worked through the requirements and prompt iteratively before implementation, narrowing the scope to a useful, testable MVP rather than adding features that did not directly support the hiring follow-up workflow.

Prompt and Implementation Plan

- Wrote and refined a detailed implementation directive covering the data model, company stage settings, calculations, candidate ranking, report output, validation, and expected edge cases.
- Broke the work into phases so the implementation could be reviewed against a defined scope instead of letting the AI make broad, unreviewed changes.
- Chose a Python implementation with CSV candidate input, JSON company settings, and a reusable processing flow for validation, calculations, ranking, and reporting.
- Reviewed AI-generated suggestions against the product rules and explicitly constrained the implementation to preserve the separation between urgency and assessment performance.

Core Implementation

- Built the candidate-processing workflow around candidate name, current hiring stage, stage start date, assessment scores, and assessment status.
- Added configurable stage deadlines, weights, and recommended actions.
- Implemented days-in-stage, overdue days, on-track/stalled status, Stage Priority Score, and candidate ranking.
- Established ranking rules that place stalled candidates ahead of on-track candidates, order stalled candidates by priority, and use overdue days and candidate name to resolve ties. On-track candidates are ordered alphabetically.
- Added assessment parsing and validation for numeric scores in a JSON array, with each score constrained to the 0–100 range.
- Kept assessment status distinct from assessment score. Completed assessments can produce an average from valid scores, while incomplete, unknown, or missing assessment data does not become an invented zero.
- Added report generation so the recruiter can review ranked candidates and their recommended follow-up actions.

Initial Verification

- Ran the initial sample workflow and inspected the output rather than treating successful execution alone as proof of correctness.
- The initial sample run reported eight candidate records: five stalled and three on track.
- Used the output as a baseline before expanding the test cases.

Day 1 Outcome

- Established the product rules, refined the implementation prompt through multiple iterations, and produced the core candidate-validation, prioritization, ranking, and reporting workflow.

---

Day 2 — Streamlit UI, Raised Test Load, Data Quality, and Debugging

Objective

Make the tool usable through a Streamlit dashboard, test it with messier and more realistic data, fix observed failures, and check that the results agree with the intended rules.

Added the Streamlit Interface

- Extended the existing Python workflow with a Streamlit interface instead of replacing the underlying validation, calculation, ranking, and reporting logic.
- Added a hiring-pipeline overview with candidate counts, stalled/on-track counts, highest priority, and data-quality warnings.
- Added candidate-management and CSV import workflows, along with company stage settings and report access.
- Kept the candidate board empty by default and removed dummy candidate/report data so the interface would not present sample records as real hiring-board data.
- Added a hiring-board reset action and checked the interaction with Streamlit’s session state behavior.
- Expanded the interface to support searching and filtering candidates, reviewing assessment information, importing candidate records, downloading a sample CSV, managing configured stages, and accessing the generated report.

Raised the Load

- Expanded testing beyond the original small sample by preparing and importing larger CSV datasets containing different hiring stages, assessment statuses, scores, missing values, and deliberately problematic records.
- Tested with multiple CSV files rather than relying on one sample dataset. The test data covered the five hiring stages: Screening, Technical Interview, HR Interview, Executive Interview, and Offer.
- Included records with missing candidate names, missing or unknown stages, missing stage start dates, invalid dates, different date formats, unknown values, incomplete assessments, missing scores, malformed score arrays, out-of-range scores, and duplicate candidate information.
- Used these datasets to check not only whether valid records were ranked correctly, but also whether the application handled imperfect data transparently and consistently.
- Compared the uploaded records with the ranked results and reviewed the data-quality warnings to understand why some records appeared in the follow-up queue while others did not.
- Checked that missing assessment scores and incomplete assessment information did not automatically invalidate an otherwise eligible candidate’s stage-priority calculation.
- Used the larger datasets to expose cases that a small, clean sample would not reveal, particularly differences between missing optional information and missing information essential to calculating a reliable priority score.

Validation and Warnings

- Implemented row-level data-quality warnings that identify the CSV row and explain why a record was rejected or why an assessment score could not be calculated.
- Refined the validation rules so that candidate name, a recognised configured hiring stage, and a valid stage start date are essential for ranking.
- Records with missing names, missing stages, unknown stage names, missing or invalid stage start dates, and future start dates are excluded because the application cannot reliably calculate their stage priority.
- Separated assessment validation from essential candidate validation. Missing or malformed assessment information can produce a warning or an unavailable assessment score without automatically excluding an otherwise eligible candidate from the follow-up queue.
- Introduced email-based duplicate detection. Normalised valid email addresses before comparing them and excluded records sharing a duplicate valid email address. Duplicate candidate names alone should not be treated as proof that two records represent the same person. Missing or malformed email addresses generate warnings but do not automatically exclude otherwise valid records.
- Normalised common assessment-status labels such as Complete to the internal value completed, while preserving the distinction between completed, incomplete, and unknown assessments.
- Validated imported assessment-score fields as JSON arrays containing valid numeric scores between 0 and 100. Identified that arrays containing commas must be quoted in CSV, for example ""[50,60]"", or the CSV reader can split one logical value across columns.
- Reviewed the difference between a record being ineligible for ranking and a record having incomplete assessment information. This distinction prevents optional assessment fields from becoming an unintended barrier to follow-up prioritisation.

Failures Encountered and Corrections Made

Assessment Status Mismatch

Imported values such as Complete did not match the application’s internal completed value. Traced the mismatch to the difference between the labels supplied in CSV files and the application’s expected status values. Updated import handling to normalise recognised labels and handle incomplete or unknown statuses separately.

Assessment Scores Not Appearing

Investigated why assessment scores were not consistently appearing after CSV import. Found that some test records had blank score cells and that JSON arrays containing commas needed correct CSV quoting. Corrected the sample CSV data and strengthened validation so malformed score data could be identified instead of silently being treated as a valid assessment.

All Dashboard Metrics Showed Zero

The expanded CSV included dates such as "10/1/2026", while the validator initially accepted only "YYYY-MM-DD". Traced the problem to "src/stall_alerter/validation.py" rather than assuming the dashboard calculations were incorrect. Updated the date parser to accept both "YYYY-MM-DD" and "M/D/YYYY" formats while continuing to reject missing, invalid, and future dates.

CSV Columns and Sample Data Did Not Align

Reviewed the sample import data after observing that values were not appearing under the expected fields. Found that blank email cells had been omitted from some rows, shifting subsequent values into the wrong columns. Corrected the CSV examples to preserve the header-to-value alignment and supplied valid example email addresses where appropriate.

Duplicate Handling Did Not Match the Intended Rule

Revisited the duplicate-record policy instead of treating repeated candidate names as conclusive evidence of duplicate identities. Refined the active validation logic to use normalised valid email addresses for duplicate detection, with warnings for missing or malformed email addresses. This makes the exclusion rule more precise and avoids automatically removing different candidates who share a name.

Stage-Name Mismatches During CSV Import

Identified that a stage name in a CSV must match a stage configured for that company. For example, Technical Interview Stage and Technical Interview are not automatically interchangeable. The validator uses the company’s configured stage settings, so an unrecognised stage cannot be assigned a reliable deadline or weight. This highlighted the need to check imported stage names against the selected company configuration rather than assuming that similar labels are equivalent.

Missing Required Fields and Unexplained Differences in Counts

Compared the original CSV rows with the ranked candidates and examined the row-level warnings. Confirmed that some candidates were excluded because essential data was missing or invalid, including names, recognised stages, and valid stage start dates. Kept these exclusions separate from assessment warnings so that optional assessment problems would not unnecessarily remove valid candidates from the follow-up queue.

Streamlit Dataframe Width Error

Corrected the misspelled width value "stretch" to "stretch".

Reset Checkbox Session-State Error

The first reset implementation attempted to change a checkbox’s state after its widget had already been instantiated. Changed the flow to process a separate reset flag before creating the checkbox, then rerun the app after clearing candidate rows.

Deprecated Streamlit Width Argument

Where applicable, replaced deprecated use of "use_container_width" with the supported "width="stretch"" or "width="content"" form.

Automated Tests Exposed Areas Needing Verification

Ran the automated test suite after making changes to the validation and ranking logic. Used the test results to check the actual behaviour of calculations, configuration loading, date and field validation, assessment handling, duplicate processing, and ranking. Reviewed the test expectations against the intended business rules rather than treating a passing test result as sufficient proof that the rules were correct.

Duplicate-Name Test Expectation

Re-examined the duplicate-handling rule in the context of the broader email-based identity policy. The expected behaviour is that duplicate names alone must not cause records to be excluded; exclusion is based on repeated valid email addresses. This remains an important test assertion to verify against the current test implementation, because a test can pass while still encoding an outdated requirement.

Final Validation and Data-Quality Handling

- Re-ran the application after the import and date-validation fixes and checked the dashboard’s data-quality warnings and candidate counts.
- Tested the application with multiple CSV datasets containing both valid and deliberately problematic records. Some candidates were ranked, while others were excluded because their records did not contain the essential information required for reliable prioritisation.
- Reviewed cases involving missing candidate names, missing stage dates, invalid date formats, unrecognised stage names, and other missing or invalid required values. Also checked that missing or invalid assessment data was handled separately from the fields required to calculate a Stage Priority Score.
- Used the Streamlit data-quality warnings to identify affected rows and explain why records were excluded or why an assessment score could not be calculated. This makes the difference between imported records and ranked candidates traceable to specific data-quality issues instead of leaving the recruiter with unexplained results.
- Checked that the reference date was applied consistently when calculating days in stage and overdue days, and that a candidate who had reached the allowed deadline exactly remained on track.
- Verified that assessment performance did not influence stage-priority status or ranking. Candidates with missing assessment scores were not assigned an invented score of zero, and assessment information remained separate from urgency.
- Reviewed the configurable stage rules to ensure that allowed days, stage weights, and recommended actions came from company settings rather than being treated as universal values.
- Ran the automated test suite:

$env:PYTHONPATH="$PWD\src"
python -m unittest discover -s tests -v

- The latest recorded test run completed 34 tests successfully, with the result "OK". The tests covered assessment parsing, calculation rules, company configuration, CSV validation, integration from CSV input to report output, and ranking behaviour.
- The automated tests were used alongside manual CSV testing. The 34 passing tests verify the scenarios represented in the test suite; the multiple CSV imports provided additional practical checks with larger and less predictable datasets.

Day 2 Outcome

- Added the Streamlit dashboard and candidate-management workflow, increased the test load, strengthened CSV and row-level validation, improved data-quality feedback, and corrected several issues discovered through actual use.
- Resolved the assessment-status normalisation and date-format problems, corrected sample CSV alignment issues, and refined duplicate handling to use valid email addresses rather than names alone.
- Tested with multiple CSV datasets and reviewed the reasons some records were excluded from ranking. Confirmed that the dashboard ranks eligible candidates, keeps assessment performance separate from stage urgency, and uses data-quality warnings to explain why some incomplete or invalid records cannot be ranked.
- Completed a recorded automated test run with 34 passing tests and used the results to verify the core calculations, validation, configuration, assessment handling, and ranking rules.

---

Overall Status

Completed During the Two-Day Work

- Refined the product requirements and implementation prompt through iterative AI-assisted planning.
- Compared alternative prioritisation approaches and kept stage urgency separate from candidate assessment performance.
- Implemented configurable stage deadlines, weights, priority scoring, ranking, and recommended actions.
- Added assessment-score parsing, status handling, and validation without making assessment completion a requirement for stage-priority ranking.
- Added the Streamlit interface on top of the existing processing workflow.
- Added candidate management, CSV import, sample CSV download, company stage settings, search and filtering, and report access.
- Added missing-field checks, date validation, duplicate-email handling, and row-level data-quality warnings.
- Tested multiple CSV datasets containing valid records and deliberately problematic data.
- Investigated and corrected issues involving assessment-status normalisation, CSV score array formatting, misaligned CSV values, accepted date formats, dataframe width, and reset-checkbox behaviour.
- Ran the automated test suite, with the latest recorded run completing 34 tests successfully.
- Reviewed the application’s observed behaviour against the intended product rules rather than relying solely on AI-generated implementation suggestions or successful execution.

Validation Behaviour Confirmed

- The dashboard distinguishes between imported records and eligible ranked candidates.
- Records missing essential information or containing invalid required values are excluded from ranking and reported through data-quality warnings. Examples include missing candidate names, missing or invalid stage start dates, future dates, and hiring stages that do not match the company’s configuration.
- Missing, incomplete, or invalid assessment data is handled separately from essential ranking data. An otherwise eligible candidate should not be excluded merely because assessment information is unavailable.
- Duplicate valid email addresses are used to identify duplicate records. Duplicate names alone should not result in exclusion.
- Stage-priority calculations and ranking remain independent of assessment performance. This prevents assessment scores from distorting follow-up urgency.
- These validation rules prevent unreliable priority calculations and give users actionable feedback about which records need correction.

Notes on Evidence and Timing

- This log describes the development sequence, debugging decisions, and observed outcomes. It does not assign invented hour counts to individual tasks. The project history shows iterative planning, implementation, testing, and debugging, but does not provide a reliable stopwatch measurement for the total work time.
- The 34-test result refers to the latest recorded automated test run. The manual testing involved multiple CSV datasets with different combinations of valid, incomplete, and invalid records; no single candidate-count result is presented as a summary of all those experiments.
- The work also reinforced the importance of checking both the implementation and its test expectations against the product requirements. Passing tests and a functioning interface are useful evidence, but neither replaces examining real import results, investigating unexpected behaviour, and confirming that validation rules reflect the intended workflow.