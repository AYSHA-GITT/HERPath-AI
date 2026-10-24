# HERPath AI — Verification & Testing Documentation
## recHERsion 2026 | PS1: Women's Healthcare

Automated testing is a foundational pillar of HERPath AI, ensuring medical safety rules, statistical algorithms, input validators, and database transactions operate reliably without regressions.

---

## 1. Test Suite Summary

All 28 automated test cases execute using `pytest` and run directly against isolated temporary databases and mock structures.

```bash
python -m pytest -v tests/
```

### Execution Results:
```text
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.1.1
collected 28 items

tests/test_database.py::test_profile_creation_and_retrieval PASSED       [  3%]
tests/test_database.py::test_symptom_add_and_persistence PASSED          [  7%]
tests/test_database.py::test_profile_scoped_isolation PASSED             [ 10%]
tests/test_database.py::test_update_symptom PASSED                       [ 14%]
tests/test_database.py::test_delete_symptom PASSED                       [ 17%]
tests/test_database.py::test_cascade_delete_profile PASSED               [ 21%]
tests/test_database.py::test_foreign_key_enforcement PASSED              [ 25%]
tests/test_insights.py::test_empty_entries_metrics PASSED                [ 28%]
tests/test_insights.py::test_single_entry_metrics PASSED                 [ 32%]
tests/test_insights.py::test_multiple_entries_and_missing_duration PASSED [ 35%]
tests/test_insights.py::test_explainable_insights_non_diagnostic PASSED  [ 39%]
tests/test_reports.py::test_empty_report_generation PASSED               [ 42%]
tests/test_reports.py::test_single_entry_report_generation PASSED        [ 46%]
tests/test_reports.py::test_multiple_entries_report_generation PASSED    [ 50%]
tests/test_safety.py::test_routine_mild_scenario PASSED                  [ 53%]
tests/test_safety.py::test_routine_moderate_consultation_scenario PASSED [ 57%]
tests/test_safety.py::test_prompt_evaluation_scenario PASSED             [ 60%]
tests/test_safety.py::test_emergency_evaluation_scenario PASSED          [ 64%]
tests/test_safety.py::test_emergency_flag_selected PASSED                [ 67%]
tests/test_safety.py::test_no_diagnostic_claims PASSED                   [ 71%]
tests/test_validators.py::test_severity_valid_range PASSED               [ 75%]
tests/test_validators.py::test_severity_out_of_bounds PASSED             [ 78%]
tests/test_validators.py::test_missing_symptom_name PASSED               [ 82%]
tests/test_validators.py::test_valid_symptom_name PASSED                 [ 85%]
tests/test_validators.py::test_onset_date_validation PASSED              [ 89%]
tests/test_validators.py::test_duration_validation PASSED                [ 92%]
tests/test_validators.py::test_full_payload_validation PASSED            [ 96%]
tests/test_validators.py::test_display_name_validation PASSED            [100%]

============================= 28 passed in 1.22s ==============================
```

---

## 2. Test Coverage by Module

### A. Database Persistence & Isolation (`tests/test_database.py`)
- **Profile Creation & Retrieval:** Verifies profile creation, default preferences, and lookup.
- **Symptom CRUD & Persistence:** Tests entry insertion, retrieving row by ID, and verify saved fields.
- **Profile-Scoped Data Isolation:** Confirms that records for User A are never exposed to User B.
- **Record Updates:** Tests updating severity, notes, and status while keeping profile scoping.
- **Record Deletion:** Tests safe removal of individual entries.
- **Cascade Deletion:** Validates that deleting a profile cascades and erases all corresponding symptom logs.
- **Foreign Key Constraints:** Validates SQLite rejects orphaned records if an invalid profile ID is provided.

### B. Input Validation (`tests/test_validators.py`)
- **Severity Boundaries:** Validates integer values 1 to 10 pass, while <=0 or >10 raise `ValidationError`.
- **Symptom Sanitization:** Verifies empty strings, whitespaces, and <2 char names are rejected.
- **Date Format & Future Checks:** Rejects invalid date formats and dates set far in the future.
- **Duration Checks:** Ensures positive numbers within 0-720 hours pass, while negative values or text fail.
- **Payload Sanitization:** Confirms default values are assigned to optional parameters.

### C. Insights & Analytics Engine (`tests/test_insights.py`)
- **Empty State Behavior:** Validates zero division is prevented when 0 entries exist.
- **Single-Entry Baseline:** Verifies metrics calculate accurately for single entries and flags insufficient data.
- **Null Value Handling:** Confirms missing durations are excluded from averages rather than coerced to 0.
- **Non-Diagnostic Constraints:** Validates that generated insight statements strictly avoid claiming disease diagnoses (e.g. no automated claims of PCOS or endometriosis).

### D. Safety Navigator & Triage Rules (`tests/test_safety.py`)
- **Supportive Self-Care (Mild):** Verifies severity 1-3 with no flags triggers self-care guidance.
- **Routine Clinical Consultation (Moderate):** Verifies severity 4-7 triggers routine provider consultation.
- **Prompt Medical Evaluation (24-48 Hours):** Confirms breast lumps or severe dysuria trigger prompt evaluation.
- **Emergency Priority Overrides:** Verifies "worst headache of life" or severe pelvic pain with syncope immediately escalate to emergency evaluation.
- **Explicit Red-Flag Checklist:** Validates user selection of emergency checklist triggers emergency priority.
- **Clinical Non-Diagnostic Boundaries:** Confirms outputs do not fabricate clinical diagnoses or prescribe drugs.

### E. Report Generation (`tests/test_reports.py`)
- **Empty Period Report:** Verifies ReportLab compiles a valid `%PDF` document even if no records exist in the timeframe.
- **Single-Entry Report:** Verifies clean PDF formatting and styling for single records.
- **Multi-Entry History:** Validates tables, word-wrapping for long notes, summary statistics, and physician discussion questions.

---

## 3. How to Run Tests

Ensure dependencies are installed and run from the project root:

```bash
# Run full suite with verbose reporting
python -m pytest -v tests/

# Run a specific test module
python -m pytest -v tests/test_safety.py

# Run with short test output
python -m pytest -q
```
