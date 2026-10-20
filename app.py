"""Streamlit interface for Stall Alerter.

This file is the presentation layer only. Candidate validation, calculations,
ranking, and CSV report generation reuse the existing tested package modules.
"""

from __future__ import annotations

import csv
import json
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

# Make the existing src-layout package importable when launched with `streamlit run app.py`.
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from stall_alerter.calculations import calculate_candidate, format_assessment_score
from stall_alerter.config import ConfigurationError, load_config
from stall_alerter.data_loader import CANDIDATE_COLUMNS, DataFileError, load_candidates
from stall_alerter.ranking import rank_candidates
from stall_alerter.report import REPORT_COLUMNS, write_report
from stall_alerter.validation import exclude_duplicate_candidates, validate_candidate_row

DATA_PATH = PROJECT_ROOT / "data" / "hiring_board.csv"
CONFIG_PATH = PROJECT_ROOT / "config" / "company_settings.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "priority_report.csv"
SAMPLE_CSV_PATH = PROJECT_ROOT / "data" / "sample_candidate_import.csv"

st.set_page_config(page_title="Stall Alerter", page_icon="⏱️", layout="wide")


def ensure_storage_files() -> None:
    """Create empty, real-data-ready files without inserting sample candidates."""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        with DATA_PATH.open("w", encoding="utf-8-sig", newline="") as file:
            csv.DictWriter(file, fieldnames=CANDIDATE_COLUMNS).writeheader()
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps({"company_name": "", "stages": {}}, indent=2) + "\n", encoding="utf-8")


def read_candidate_rows() -> list[dict[str, str]]:
    """Read persisted candidate inputs; an empty header-only file is valid in the UI."""
    if not DATA_PATH.exists():
        return []
    with DATA_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise DataFileError("The hiring-board CSV needs a header row.")
        headers = [item.strip() for item in reader.fieldnames if item]
        missing = set(CANDIDATE_COLUMNS[:3]) - set(headers)
        if missing:
            raise DataFileError("Hiring-board CSV is missing required columns: " + ", ".join(sorted(missing)))
        rows = []
        for row in reader:
            clean = {column: (row.get(column) or "").strip() for column in CANDIDATE_COLUMNS}
            if any(clean.values()):
                rows.append(clean)
        return rows


def write_candidate_rows(rows: list[dict[str, str]]) -> None:
    """Persist CRUD changes atomically so interrupted writes do not truncate the board."""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8-sig", newline="", dir=DATA_PATH.parent, delete=False) as temp_file:
        temp_path = Path(temp_file.name)
        writer = csv.DictWriter(temp_file, fieldnames=CANDIDATE_COLUMNS)
        writer.writeheader()
        writer.writerows({column: row.get(column, "") for column in CANDIDATE_COLUMNS} for row in rows)
    temp_path.replace(DATA_PATH)


def read_settings_for_editor() -> dict[str, Any]:
    """Read raw settings so the UI can recover from an unconfigured empty stage list."""
    try:
        payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("The settings root must be a JSON object.")
        payload.setdefault("company_name", "")
        payload.setdefault("stages", {})
        return payload
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        st.error(f"Company settings could not be read: {exc}")
        return {"company_name": "", "stages": {}}


def save_settings(payload: dict[str, Any]) -> None:
    """Validate new settings with the existing config validator before replacing the file."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", dir=CONFIG_PATH.parent, delete=False) as temp_file:
            json.dump(payload, temp_file, indent=2, ensure_ascii=False)
            temp_file.write("\n")
            temp_path = Path(temp_file.name)
        load_config(temp_path)  # Reuse the CLI's rules and reject invalid settings before saving.
        temp_path.replace(CONFIG_PATH)
    except (OSError, ConfigurationError) as exc:
        if temp_path and temp_path.exists():
            temp_path.unlink()
        raise ValueError(str(exc)) from exc


def build_ranked_board(rows: list[dict[str, str]], reference_date: date, config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Run the same validation, duplicate exclusion, calculation, and ranking as the CLI."""
    valid_rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for row_number, row in enumerate(rows, start=2):
        record, row_warnings = validate_candidate_row({**row, "_row_number": str(row_number)}, reference_date, config)
        warnings.extend(row_warnings)
        if record is not None:
            valid_rows.append(record)
    unique_rows, duplicate_warnings = exclude_duplicate_candidates(valid_rows)
    warnings.extend(duplicate_warnings)
    return rank_candidates([calculate_candidate(record, reference_date) for record in unique_rows]), warnings


def assessment_input(scores_text: str, status: str) -> str:
    """Normalize the editable score field to the JSON-array format expected by the core."""
    if not scores_text.strip():
        if status == "completed":
            raise ValueError("A completed assessment needs at least one score.")
        return ""
    try:
        values = json.loads(scores_text)
        if not isinstance(values, list):
            raise ValueError("Enter a JSON array, for example [82, 91].")
        if status != "completed":
            return json.dumps(values)
        if not values:
            raise ValueError("A completed assessment needs at least one score.")
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 100 for value in values):
            raise ValueError("Each assessment score must be a number from 0 to 100.")
        return json.dumps(values)
    except json.JSONDecodeError as exc:
        raise ValueError("Scores must be a JSON array, for example [82, 91].") from exc


def render_settings(candidate_rows: list[dict[str, str]]) -> dict[str, Any]:
    """Render the company/stage settings editor and save only validated values."""
    st.subheader("Company and stage settings")
    payload = read_settings_for_editor()
    with st.form("company_settings_form"):
        company_name = st.text_input("Company name (optional)", value=str(payload.get("company_name", "")))
        stages: dict[str, dict[str, Any]] = {}
        for index, (stage_name, values) in enumerate(payload.get("stages", {}).items()):
            st.markdown(f"**Stage {index + 1}: {stage_name}**")
            left, middle, right = st.columns([2, 1, 1])
            new_name = left.text_input("Stage name", value=stage_name, key=f"stage_name_{index}").strip()
            allowed_days = middle.number_input("Allowed days", min_value=0, step=1, value=int(values.get("allowed_days", 0)), key=f"allowed_{index}")
            weight = right.number_input("Weight (1–5)", min_value=1, max_value=5, step=1, value=int(values.get("weight", 1)), key=f"weight_{index}")
            action = st.text_input("Recommended action", value=str(values.get("recommended_action", "")), key=f"action_{index}").strip()
            if new_name:
                stages[new_name] = {"allowed_days": int(allowed_days), "weight": int(weight), "recommended_action": action}
        st.markdown("**Add a stage**")
        add_left, add_days, add_weight = st.columns([2, 1, 1])
        added_name = add_left.text_input("New stage name")
        added_days = add_days.number_input("New stage allowed days", min_value=0, step=1, value=3)
        added_weight = add_weight.number_input("New stage weight", min_value=1, max_value=5, step=1, value=1)
        added_action = st.text_input("New stage recommended action")
        submitted = st.form_submit_button("Validate and save settings", type="primary")
    if submitted:
        if added_name.strip():
            if added_name.strip().casefold() in {name.casefold() for name in stages}:
                st.error("That stage already exists. Use the existing stage row to edit it.")
                return payload
            if not added_action.strip():
                st.error("A recommended action is required for the new stage.")
                return payload
            stages[added_name.strip()] = {"allowed_days": int(added_days), "weight": int(added_weight), "recommended_action": added_action.strip()}
        if not stages:
            st.error("Add at least one stage before saving settings.")
            return payload
        # Prevent removing or renaming stages that current candidate rows still use.
        removed_stages = {name.casefold() for name in payload.get("stages", {})} - {name.casefold() for name in stages}
        used_removed_stages = sorted({row.get("current_stage", "") for row in candidate_rows if row.get("current_stage", "").casefold() in removed_stages})
        if used_removed_stages:
            st.error("These stages are used by saved candidates and cannot be removed/renamed until those candidates are moved: " + ", ".join(used_removed_stages))
            return payload
        if any(not values["recommended_action"] for values in stages.values()):
            st.error("Every configured stage needs a recommended action.")
            return payload
        try:
            save_settings({"company_name": company_name.strip(), "stages": stages})
            st.success("Company settings saved.")
            st.rerun()
        except ValueError as exc:
            st.error(f"Settings were not saved: {exc}")
    return payload


def main() -> None:
    """Build the dashboard, candidate CRUD, and configuration screens."""
    ensure_storage_files()
    st.title("Stall Alerter")
    st.caption("A transparent follow-up queue for candidates waiting too long at a hiring stage.")
    page = st.sidebar.radio("Workspace", ["Dashboard", "Manage candidates", "Company settings"])
    reference_date = st.sidebar.date_input("Calculate as of", value=date.today())
    st.sidebar.caption("All changes are saved to local CSV/JSON files in this project.")

    try:
        rows = read_candidate_rows()
    except DataFileError as exc:
        st.error(str(exc))
        st.stop()
    raw_settings = read_settings_for_editor()
    try:
        config = load_config(CONFIG_PATH)
    except ConfigurationError as exc:
        config = None
        if page != "Company settings":
            st.warning(f"Configure at least one hiring stage before using the dashboard: {exc}")
            st.info("Open **Company settings** in the sidebar to set each stage deadline, weight, and recommended action.")
            if page == "Manage candidates":
                st.stop()

    if page == "Company settings":
        render_settings(rows)
        return

    if page == "Manage candidates":
        st.subheader("Candidate records")
        st.caption(f"Source file: `{DATA_PATH.relative_to(PROJECT_ROOT)}`")
        
       
        st.markdown("### Reset hiring board")

        st.warning(
            "This action permanently deletes ALL candidate records from this "
            "hiring board. Your company settings and generated reports will "
            "not be deleted."
        )

        
        if st.session_state.get("reset_confirmation_checkbox", False):
            st.session_state["confirm_reset_hiring_board"] = False
            st.session_state["reset_confirmation_checkbox"] = False

        
        confirm_reset = st.checkbox(
            "I understand that all candidates on this hiring board will be deleted.",
            key="confirm_reset_hiring_board",
        )

        # NEW: Delete candidate records only after the user confirms.
        if st.button(
            "Delete all candidates from this hiring board",
            type="secondary",
            disabled=not confirm_reset,
            key="delete_all_hiring_board_candidates",
            width="stretch",
        ):
            try:
                # Clear all candidate records while preserving the CSV headers.
                write_candidate_rows([])

                # NEW: Use a separate flag to request that the checkbox
                # be reset on the next Streamlit run.
                st.session_state["reset_confirmation_checkbox"] = True

                # Inform the user that the hiring board was cleared.
                st.success("All candidate records have been deleted.")

                # Refresh the page to show the empty hiring board.
                st.rerun()

            except OSError as exc:
                # Show a helpful message if the CSV cannot be updated.
                st.error(f"Could not reset the hiring board: {exc}")
        
        if rows:
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        else:
            st.info("No candidate records yet. Add your real hiring-board records below or import a CSV.")

        st.markdown("### Import a hiring-board CSV")
        st.download_button(
            "Download sample candidate CSV",
            data=SAMPLE_CSV_PATH.read_bytes(),
            file_name=SAMPLE_CSV_PATH.name,
            mime="text/csv",
            help="Includes completed assessments with scores, incomplete and unknown assessments, and rows with missing or invalid candidate details.",
        )
        uploaded = st.file_uploader("Choose a CSV with candidate_name, email, current_stage, asseessment_scores, assessment_status and stage_start_date", type=["csv"])
        replace_import = st.checkbox("Replace all current candidates with the uploaded file", value=False, disabled=uploaded is None)
        if st.button("Import CSV", disabled=uploaded is None):
            try:
                decoded = uploaded.getvalue().decode("utf-8-sig")
                reader = csv.DictReader(decoded.splitlines())
                if not reader.fieldnames or not set(CANDIDATE_COLUMNS[:3]).issubset({name.strip() for name in reader.fieldnames}):
                    raise ValueError("CSV needs candidate_name, email, current_stage, asseessment_scores, assessment_status and stage_start_date columns.")
                # imported = [{column: (record.get(column) or "").strip() for column in CANDIDATE_COLUMNS} for record in reader]
                
                # FIX: Normalize imported assessment statuses so values such
                # as "Complete" are recognized as "completed" by the app.
                imported = []

                for record in reader:
                    candidate = {
                        column: (record.get(column) or "").strip()
                        for column in CANDIDATE_COLUMNS
                    }

                    # Convert common CSV status labels to the values used
                    # internally by the Streamlit form and core package.
                    raw_status = candidate["assessment_status"].casefold()

                    status_mapping = {
                        "complete": "completed",
                        "completed": "completed",
                        "incomplete": "incomplete",
                        "unknown": "unknown",
                        "": "unknown",
                    }

                    if raw_status not in status_mapping:
                        raise ValueError(
                            f"Invalid assessment status '{candidate['assessment_status']}' "
                            f"for candidate '{candidate['candidate_name']}'. "
                            "Use Complete, Incomplete, or Unknown."
                        )

                    candidate["assessment_status"] = status_mapping[raw_status]

                    # FIX: Check that a supplied score is a valid JSON array.
                    # This also catches score fields accidentally split by commas.
                    scores_text = candidate["assessment_scores"]

                    if scores_text:
                        try:
                            parsed_scores = json.loads(scores_text)
                        except json.JSONDecodeError as exc:
                            raise ValueError(
                                f"Invalid assessment_scores for "
                                f"'{candidate['candidate_name']}'. "
                                'Use a JSON array such as [50,60].'
                            ) from exc

                        if not isinstance(parsed_scores, list):
                            raise ValueError(
                                f"Assessment scores for '{candidate['candidate_name']}' "
                                'must be a JSON array such as [50,60].'
                            )

                    imported.append(candidate)

                if not imported:
                    raise ValueError("The uploaded CSV contains no candidate rows.")
                write_candidate_rows(imported if replace_import else rows + imported)
                st.success(f"Imported {len(imported)} candidate row(s).")
                st.rerun()
            except (UnicodeDecodeError, csv.Error, ValueError) as exc:
                st.error(f"Import failed: {exc}")

        st.markdown("### Add candidate")
        stage_names = list(config["stages"].keys()) if config else []
        if not stage_names:
            st.warning("Configure hiring stages before adding candidates.")
        else:
            with st.form("add_candidate_form", clear_on_submit=True):
                name = st.text_input("Candidate name")
                email = st.text_input("Candidate email (optional)")
                stage = st.selectbox("Current stage", stage_names)
                start_date = st.date_input("Stage start date", value=reference_date, max_value=reference_date, key="new_start_date")
                assessment_status = st.selectbox("Assessment status", ["unknown", "incomplete", "completed"])
                scores = st.text_input("Assessment scores (optional JSON array)", placeholder='[82, 91]')
                add_clicked = st.form_submit_button("Add candidate", type="primary")
            if add_clicked:
                if not name.strip():
                    st.error("Candidate name is required.")
                
                else:
                    try:
                        score_json = assessment_input(scores, assessment_status)
                        candidate = {"candidate_name": name.strip(),"email": email.strip(), "current_stage": stage, "stage_start_date": start_date.isoformat(), "assessment_scores": score_json, "assessment_status": assessment_status}
                        # Validate the same business rules before saving, not only when the report is generated.
                        valid, warnings = validate_candidate_row({**candidate, "_row_number": "new"}, reference_date, config)
                        if valid is None or warnings:
                            st.error("Candidate was not saved: " + " ".join(warnings or ["Please review the candidate details."]))
                        else:
                            for warning in warnings:
                                st.warning(warning)
                            write_candidate_rows(rows + [candidate])
                            st.success("Candidate added.")
                            st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))

        if rows:
            st.markdown("### Edit or delete candidate")
            selected_index = st.selectbox("Select candidate", options=list(range(len(rows))), format_func=lambda index: f"{rows[index]['candidate_name']} — {rows[index]['current_stage']} (CSV row {index + 2})")
            selected = rows[selected_index]
            with st.form("edit_candidate_form"):
                edit_name = st.text_input("Candidate name", value=selected["candidate_name"])
                edit_email = st.text_input(
                    "Candidate email (optional)",
                    value=selected.get("email", ""),
                )
                edit_stage = st.selectbox("Current stage", stage_names or [selected["current_stage"]], index=(stage_names.index(selected["current_stage"]) if selected["current_stage"] in stage_names else 0))
                try:
                    default_date = date.fromisoformat(selected["stage_start_date"])
                    if default_date > reference_date:
                        default_date = reference_date
                except ValueError:
                    default_date = reference_date
                edit_date = st.date_input("Stage start date", value=default_date, max_value=reference_date, key=f"edit_date_{selected_index}")
                selected_status = selected["assessment_status"].casefold()
                if selected_status == "complete":
                    selected_status = "completed"
                edit_status = st.selectbox("Assessment status", ["unknown", "incomplete", "completed"], index=["unknown", "incomplete", "completed"].index(selected_status if selected_status in {"unknown", "incomplete", "completed"} else "unknown"))
                edit_scores = st.text_input("Assessment scores (optional JSON array)", value=selected["assessment_scores"], placeholder='[82, 91]')
                edit_clicked = st.form_submit_button("Save candidate changes", type="primary")
            if edit_clicked:
                if not edit_name.strip():
                    st.error("Candidate name is required.")
                else:
                    try:
                        score_json = assessment_input(edit_scores, edit_status)
                        updated = {"candidate_name": edit_name.strip(),"email": edit_email.strip(), "current_stage": edit_stage, "stage_start_date": edit_date.isoformat(), "assessment_scores": score_json, "assessment_status": edit_status}
                        valid, warnings = validate_candidate_row({**updated, "_row_number": "edited"}, reference_date, config) if config else (None, ["Configure company stages before editing candidates."])
                        if valid is None or warnings:
                            st.error("Changes were not saved: " + " ".join(warnings or ["Review candidate details."]))
                        else:
                            for warning in warnings:
                                st.warning(warning)
                            updated_rows = list(rows)
                            updated_rows[selected_index] = updated
                            write_candidate_rows(updated_rows)
                            st.success("Candidate changes saved.")
                            st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
            confirm_delete = st.checkbox(f"I confirm deletion of {selected['candidate_name']}", key=f"confirm_delete_{selected_index}")
            if st.button("Delete selected candidate", type="secondary", disabled=not confirm_delete):
                write_candidate_rows([item for index, item in enumerate(rows) if index != selected_index])
                st.success("Candidate deleted.")
                st.rerun()
        return

    st.subheader("Hiring pipeline overview")
    st.caption(f"Reference date: {reference_date.isoformat()} · Candidate input rows: {len(rows)}")
    if not rows:
        st.info("No candidate data has been added yet. Open **Manage candidates** to add records or import your CSV.")
        return
    if config is None:
        st.stop()
    ranked, warnings = build_ranked_board(rows, reference_date, config)
    stalled_count = sum(item["status"] == "Stalled" for item in ranked)
    on_track_count = sum(item["status"] == "On track" for item in ranked)
    highest_priority_score = max((item["stage_priority_score"] for item in ranked), default=0)
    first, second, third, fourth = st.columns(4)
    first.metric("Candidates ranked", len(ranked))
    second.metric("Stalled", stalled_count)
    third.metric("On track", on_track_count)
    fourth.metric("Highest priority score", highest_priority_score)

    if warnings:
        with st.expander(f"Data-quality warnings ({len(warnings)})", expanded=True):
            for warning in warnings:
                st.warning(warning)
    if not ranked:
        st.warning("No candidate records passed validation. Check stage settings and data-quality warnings.")
        return

    table_rows = []
    for record in ranked:
        table_rows.append({
            "Rank": record["priority_rank"], "Candidate": record["candidate_name"], "Stage": record["current_stage"],
            "Days in stage": record["days_in_stage"], "Allowed days": record["allowed_days"], "Days overdue": record["overdue_days"],
            "Stage weight": f"{record['stage_weight']}/5", "Priority score": record["stage_priority_score"],
            "Status": record["status"], "Assessment": format_assessment_score(record), "Recommended action": record["recommended_action"],
        })
    display_df = pd.DataFrame(table_rows)
    search = st.text_input("Search candidates or stages")
    status_filter = st.multiselect("Filter by status", ["Stalled", "On track"], default=["Stalled", "On track"])
    # stage_filter = st.multiselect("Filter by stage", sorted({item["Stage"] for item in table_rows}), default=sorted({item["Stage"] for item in table_rows}))
    all_stages = sorted(config["stages"].keys())

    stage_filter = st.multiselect(
        "Filter by stage",
        all_stages,
        default=all_stages,
    )
    filtered_df = display_df[display_df["Status"].isin(status_filter) & display_df["Stage"].isin(stage_filter)]
    if search.strip():
        query = search.strip().casefold()
        filtered_df = filtered_df[filtered_df.apply(lambda row: query in " ".join(str(value) for value in row.values).casefold(), axis=1)]
    st.dataframe(filtered_df, width="stretch", hide_index=True)

    st.markdown("### Candidate ranking explanations")
    for record in ranked:
        with st.expander(f"#{record['priority_rank']} · {record['candidate_name']} · {record['status']} · Score {record['stage_priority_score']}"):
            st.write(record["ranking_explanation"])
            st.write(f"**Recommended action:** {record['recommended_action']}")
            st.write(f"**Assessment:** {format_assessment_score(record)} (does not affect priority or ranking).")

    if st.button("Generate and prepare CSV report", type="primary"):
        report_path = write_report(ranked, REPORT_PATH)
        st.success(f"Report generated at {report_path.relative_to(PROJECT_ROOT)}")
    if REPORT_PATH.exists():
        st.download_button("Download latest CSV report", data=REPORT_PATH.read_bytes(), file_name="priority_report.csv", mime="text/csv")


if __name__ == "__main__":
    main()
