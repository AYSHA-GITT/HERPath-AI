# HERPath AI — Verification & Testing Documentation
## recHERsion 2026 | PS1: Women's Healthcare

Automated testing is a foundational pillar of HERPath AI, ensuring medical safety rules, statistical algorithms, input validators, UI state flows, and database transactions operate reliably without regressions.

---

## 1. Test Suite Summary

All **40 automated test cases** execute using `pytest` and test both backend services and frontend Streamlit rendering flows.

```bash
python -m pytest -v tests/
```

### Execution Results:
```text
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0
collected 40 items

tests/test_backend_e2e.py::test_backend_complete_profile_lifecycle PASSED [  2%]
tests/test_backend_e2e.py::test_backend_multi_profile_data_isolation PASSED [  5%]
tests/test_backend_e2e.py::test_backend_analytics_engine_math_and_charts PASSED [  7%]
tests/test_backend_e2e.py::test_backend_safety_navigator_rule_hierarchy PASSED [ 10%]
tests/test_backend_e2e.py::test_backend_report_generator_pdf_validation PASSED [ 12%]
tests/test_database.py::test_profile_creation_and_retrieval PASSED       [ 15%]
tests/test_database.py::test_symptom_add_and_persistence PASSED          [ 17%]
tests/test_database.py::test_profile_scoped_isolation PASSED             [ 20%]
tests/test_database.py::test_update_symptom PASSED                       [ 22%]
tests/test_database.py::test_delete_symptom PASSED                       [ 25%]
tests/test_database.py::test_cascade_delete_profile PASSED               [ 27%]
tests/test_database.py::test_foreign_key_enforcement PASSED              [ 30%]
tests/test_frontend_e2e.py::test_frontend_home_dashboard PASSED          [ 32%]
tests/test_frontend_e2e.py::test_frontend_symptom_journal_navigation PASSED [ 35%]
tests/test_frontend_e2e.py::test_frontend_health_insights_view PASSED    [ 37%]
tests/test_frontend_e2e.py::test_frontend_care_navigator_triage PASSED   [ 40%]
tests/test_frontend_e2e.py::test_frontend_health_library_search PASSED   [ 42%]
tests/test_frontend_e2e.py::test_frontend_report_preview_and_download PASSED [ 45%]
tests/test_frontend_e2e.py::test_frontend_privacy_settings_and_profile_switch PASSED [ 47%]
tests/test_insights.py::test_empty_entries_metrics PASSED                [ 50%]
tests/test_insights.py::test_single_entry_metrics PASSED                 [ 52%]
tests/test_insights.py::test_multiple_entries_and_missing_duration PASSED [ 55%]
tests/test_insights.py::test_explainable_insights_non_diagnostic PASSED  [ 57%]
tests/test_reports.py::test_empty_report_generation PASSED               [ 60%]
tests/test_reports.py::test_single_entry_report_generation PASSED        [ 62%]
tests/test_reports.py::test_multiple_entries_report_generation PASSED    [ 65%]
tests/test_safety.py::test_routine_mild_scenario PASSED                  [ 67%]
tests/test_safety.py::test_routine_moderate_consultation_scenario PASSED [ 70%]
tests/test_safety.py::test_prompt_evaluation_scenario PASSED             [ 72%]
tests/test_safety.py::test_emergency_evaluation_scenario PASSED          [ 75%]
tests/test_safety.py::test_emergency_flag_selected PASSED                [ 77%]
tests/test_safety.py::test_no_diagnostic_claims PASSED                   [ 80%]
tests/test_validators.py::test_severity_valid_range PASSED               [ 82%]
tests/test_validators.py::test_severity_out_of_bounds PASSED             [ 85%]
tests/test_validators.py::test_missing_symptom_name PASSED               [ 87%]
tests/test_validators.py::test_valid_symptom_name PASSED                 [ 90%]
tests/test_validators.py::test_onset_date_validation PASSED              [ 92%]
tests/test_duration_validation PASSED                                     [ 95%]
tests/test_validators.py::test_full_payload_validation PASSED            [ 97%]
tests/test_validators.py::test_display_name_validation PASSED            [100%]

============================= 40 passed in 5.36s ==============================
```

---

## 2. Test Coverage by Module

### A. Frontend End-to-End (`tests/test_frontend_e2e.py`)
- **Home Dashboard:** Header banner, quick action buttons, KPI cards, timeline figure.
- **Symptom Journal:** Form input fields, slider boundaries, category options, submit buttons.
- **Health Insights:** Metric cards calculation, explainable observation statements.
- **Care Navigator Triage:** Form submission, emergency warning evaluation, red banner rendering.
- **Women's Health Library:** Live search query filtering and verified card display.
- **My Health Report:** Period selector, report preview metrics, PDF download button.
- **Privacy & Settings:** Local privacy documentation, profile customization controls.

### B. Backend End-to-End (`tests/test_backend_e2e.py`)
- **Profile Lifecycle:** Creation, listing, preference updates, cascade deletion.
- **Multi-Profile Isolation:** Zero cross-profile data leakage between independent users.
- **Analytics Engine:** Mathematical precision, duration null handling, Plotly figures.
- **Safety Navigator Triage:** Full 4-tier triage priority hierarchy evaluation.
- **PDF Report Validation:** ReportLab document compilation and `%PDF` byte validation.

### C. Unit Test Modules
- **`tests/test_database.py`:** Profile CRUD, symptom CRUD, cascade deletion, foreign key enforcement.
- **`tests/test_validators.py`:** Input sanitization, severity 1-10 range, duration 0-720h, date validation.
- **`tests/test_insights.py`:** Metric calculations, null handling, non-diagnostic constraints.
- **`tests/test_safety.py`:** Rule priorities, emergency overrides, non-diagnostic boundaries.
- **`tests/test_reports.py`:** Empty, single, and multi-entry ReportLab PDF generation.
