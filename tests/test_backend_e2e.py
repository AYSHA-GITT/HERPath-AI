"""
HERPath AI - Comprehensive Backend End-to-End Test Suite
recHERsion 2026 | PS1: Women's Healthcare

Validates entire backend data lifecycle, services, rule-engine,
analytics calculations, and PDF generation without UI dependencies.
"""

import pytest
import tempfile
import os
import gc
from datetime import date, timedelta

from database import (
    init_db,
    create_profile,
    get_profile,
    list_profiles,
    delete_profile,
    update_profile_preferences,
    clear_profile_symptoms,
    add_medication,
    get_medications,
    delete_medication,
    export_profile_data_json,
    export_symptoms_csv,
    import_profile_data_json
)
from symptom_tracker import SymptomTrackerService
from insights_engine import InsightsEngine
from safety_navigator import (
    SafetyNavigator,
    PRIORITY_EMERGENCY,
    PRIORITY_PROMPT,
    PRIORITY_ROUTINE,
    PRIORITY_SELFCARE
)
from health_library import HealthLibrary
from report_generator import ClinicianReportGenerator
from models import UserProfile, SymptomEntry, MedicationEntry


@pytest.fixture
def isolated_db():
    """Sets up an isolated temporary database for full backend verification."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    gc.collect()
    try:
        if os.path.exists(path):
            os.remove(path)
    except PermissionError:
        pass


def test_backend_complete_profile_lifecycle(isolated_db):
    """Verifies profile creation, listing, preference updates, and cascade deletion."""
    # 1. Create Profile
    p1 = create_profile("doc_maya", "Dr. Maya", {"track_menstrual": False}, db_path=isolated_db)
    assert p1.id == "doc_maya"
    assert p1.display_name == "Dr. Maya"
    assert p1.preferences["track_menstrual"] is False

    # 2. Add symptoms for profile
    success, s_id, err = SymptomTrackerService.record_symptom(
        profile_id="doc_maya",
        category="Systemic & Energy",
        symptom="Severe Fatigue / Exhaustion",
        onset_date=str(date.today()),
        severity=5,
        db_path=isolated_db
    )
    assert success is True
    assert s_id is not None

    # 3. Update Preferences
    ok = update_profile_preferences("doc_maya", {"track_menstrual": True, "theme": "dark"}, db_path=isolated_db)
    assert ok is True
    updated = get_profile("doc_maya", db_path=isolated_db)
    assert updated.preferences["track_menstrual"] is True

    # 4. Cascade Delete
    del_ok = delete_profile("doc_maya", db_path=isolated_db)
    assert del_ok is True
    assert get_profile("doc_maya", db_path=isolated_db) is None
    assert len(SymptomTrackerService.get_history("doc_maya", db_path=isolated_db)) == 0


def test_backend_multi_profile_data_isolation(isolated_db):
    """Verifies that records for multiple profiles remain strictly segregated."""
    create_profile("prof_a", "Alice", db_path=isolated_db)
    create_profile("prof_b", "Bobbie", db_path=isolated_db)

    # Add 3 symptoms to Alice
    for i in range(3):
        SymptomTrackerService.record_symptom(
            profile_id="prof_a",
            category="Pelvic & Menstrual",
            symptom="Pelvic Pain",
            onset_date=f"2026-10-1{i}",
            severity=6,
            db_path=isolated_db
        )

    # Add 2 symptoms to Bobbie
    for i in range(2):
        SymptomTrackerService.record_symptom(
            profile_id="prof_b",
            category="Neurological & Head",
            symptom="Migraine",
            onset_date=f"2026-10-2{i}",
            severity=7,
            db_path=isolated_db
        )

    alice_logs = SymptomTrackerService.get_history("prof_a", db_path=isolated_db)
    bobbie_logs = SymptomTrackerService.get_history("prof_b", db_path=isolated_db)

    assert len(alice_logs) == 3
    assert len(bobbie_logs) == 2
    assert all(e.category == "Pelvic & Menstrual" for e in alice_logs)
    assert all(e.category == "Neurological & Head" for e in bobbie_logs)


def test_backend_analytics_engine_math_and_charts(isolated_db):
    """Verifies mathematical calculations and chart object generation in InsightsEngine."""
    create_profile("analyst_user", "Analyst", db_path=isolated_db)

    # Add 5 varied symptom entries
    entries_data = [
        ("Migraine", "Neurological & Head", "2026-10-01", 6, 4.0, "Disrupted / Fragmented"),
        ("Migraine", "Neurological & Head", "2026-10-05", 8, 6.0, "Disrupted / Fragmented"),
        ("Severe Fatigue / Exhaustion", "Systemic & Energy", "2026-10-10", 4, None, "Restful (7-9 hrs)"),
        ("Migraine", "Neurological & Head", "2026-10-15", 7, 5.0, "Disrupted / Fragmented"),
        ("Pelvic Pain / Cramping", "Pelvic & Menstrual", "2026-10-20", 5, 2.0, "Moderate (5-7 hrs)")
    ]

    for sym, cat, dt, sev, dur, slp in entries_data:
        SymptomTrackerService.record_symptom(
            profile_id="analyst_user",
            category=cat,
            symptom=sym,
            onset_date=dt,
            severity=sev,
            duration_hours=dur,
            context={"sleep": slp},
            db_path=isolated_db
        )

    entries = SymptomTrackerService.get_history("analyst_user", db_path=isolated_db)
    engine = InsightsEngine(entries)
    metrics = engine.calculate_summary_metrics()

    # Total: 5
    assert metrics["total_entries"] == 5
    # Avg severity: (6 + 8 + 4 + 7 + 5) / 5 = 30 / 5 = 6.0
    assert metrics["avg_severity"] == 6.0
    # Peak severity: 8 (Migraine)
    assert metrics["max_severity"] == 8
    assert metrics["max_severity_symptom"] == "Migraine"
    # Top symptom: Migraine (3)
    assert metrics["top_symptom"] == "Migraine"
    assert metrics["top_symptom_count"] == 3
    # Duration: (4 + 6 + 5 + 2) / 4 = 17 / 4 = 4.25 -> rounded to 4.2 or 4.3 (null ignored!)
    assert metrics["avg_duration"] == 4.2

    # Check Plotly Figures
    fig_timeline = engine.plot_severity_timeline()
    assert fig_timeline is not None

    fig_freq = engine.plot_symptom_frequency()
    assert fig_freq is not None

    fig_ctx = engine.plot_context_comparison()
    assert fig_ctx is not None

    # Check Explainable Statements
    insights = engine.generate_explainable_insights()
    assert len(insights) >= 2
    assert any("Migraine" in ins["title"] for ins in insights)
    assert any("Sleep Quality" in ins["title"] for ins in insights)


def test_backend_safety_navigator_rule_hierarchy():
    """Verifies that SafetyNavigator correctly implements the 4-tier triage priority hierarchy."""
    # Tier 1: Emergency Warning
    em_eval = SafetyNavigator.evaluate(
        symptom="Severe Headache",
        category="Neurological & Head",
        severity=9,
        notes="Thunderclap worst headache of my entire life"
    )
    assert em_eval.priority == PRIORITY_EMERGENCY
    assert em_eval.emergency_contact is not None

    # Tier 2: Prompt Medical Evaluation (24-48h)
    pr_eval = SafetyNavigator.evaluate(
        symptom="Breast Health Concern",
        category="Breast Health",
        severity=4,
        notes="Noticed a new distinct breast lump"
    )
    assert pr_eval.priority == PRIORITY_PROMPT

    # Tier 3: Routine Consultation
    rt_eval = SafetyNavigator.evaluate(
        symptom="Pelvic Pain / Cramping",
        category="Pelvic & Menstrual",
        severity=5,
        duration_hours=12.0
    )
    assert rt_eval.priority == PRIORITY_ROUTINE

    # Tier 4: Supportive Self-Care
    sc_eval = SafetyNavigator.evaluate(
        symptom="Tension Headache",
        category="Neurological & Head",
        severity=2,
        duration_hours=1.0
    )
    assert sc_eval.priority == PRIORITY_SELFCARE


def test_backend_report_generator_pdf_validation(isolated_db):
    """Verifies that ReportLab compiles a valid, well-structured PDF document."""
    profile = UserProfile(id="rep_test_user", display_name="Elena Rostova")
    entries = [
        SymptomEntry(
            id=1,
            profile_id="rep_test_user",
            category="Pelvic & Menstrual",
            symptom="Pelvic Pain / Cramping",
            onset_date="2026-10-15",
            severity=7,
            duration_hours=8.0,
            status="Resolved",
            impact="Moderate",
            notes="Pain radiating to lower back.",
            context={"sleep": "Disrupted / Fragmented"}
        )
    ]

    generator = ClinicianReportGenerator(
        profile=profile,
        entries=entries,
        start_date="2026-10-01",
        end_date="2026-10-24"
    )
    pdf_bytes = generator.generate_pdf_bytes()

    assert pdf_bytes is not None
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
    assert b"HERPath AI" in pdf_bytes or len(pdf_bytes) > 2000


def test_backend_medication_crud(isolated_db):
    """Verifies adding, retrieving, and deleting medications."""
    create_profile("med_test_user", "Med User", db_path=isolated_db)
    med = MedicationEntry(
        id=None,
        profile_id="med_test_user",
        name="Sumatriptan",
        category="Prescription",
        dosage="50 mg",
        frequency="As needed at migraine onset",
        started_date="2026-06-01",
        notes="Take with plenty of water."
    )
    m_id = add_medication(med, db_path=isolated_db)
    assert m_id > 0

    meds = get_medications("med_test_user", db_path=isolated_db)
    assert len(meds) == 1
    assert meds[0].name == "Sumatriptan"
    assert meds[0].dosage == "50 mg"

    deleted = delete_medication(m_id, "med_test_user", db_path=isolated_db)
    assert deleted is True
    assert len(get_medications("med_test_user", db_path=isolated_db)) == 0


def test_backend_data_portability_export_import(isolated_db):
    """Verifies complete JSON and CSV data backup export and subsequent restoration."""
    create_profile("export_user", "Export User", db_path=isolated_db)
    SymptomTrackerService.record_symptom(
        profile_id="export_user",
        category="Neurological & Head",
        symptom="Migraine",
        onset_date="2026-10-20",
        severity=7,
        db_path=isolated_db
    )
    add_medication(MedicationEntry(
        id=None,
        profile_id="export_user",
        name="Naproxen",
        category="Prescription",
        dosage="550 mg"
    ), db_path=isolated_db)

    # Export to JSON
    json_str = export_profile_data_json("export_user", db_path=isolated_db)
    assert "Migraine" in json_str
    assert "Naproxen" in json_str

    # Export to CSV
    csv_str = export_symptoms_csv("export_user", db_path=isolated_db)
    assert "Migraine" in csv_str
    assert "Onset Date" in csv_str

    # Restore into a second profile
    create_profile("import_user", "Import User", db_path=isolated_db)
    syms_count, meds_count = import_profile_data_json("import_user", json_str, db_path=isolated_db)
    assert syms_count == 1
    assert meds_count == 1

    restored_syms = SymptomTrackerService.get_history("import_user", db_path=isolated_db)
    restored_meds = get_medications("import_user", db_path=isolated_db)
    assert len(restored_syms) == 1
    assert restored_syms[0].symptom == "Migraine"
    assert len(restored_meds) == 1
    assert restored_meds[0].name == "Naproxen"


def test_backend_doctor_agenda_builder(isolated_db):
    """Verifies that InsightsEngine generates tailored clinical consultation talking points."""
    create_profile("agenda_user", "Agenda User", db_path=isolated_db)
    for i in range(3):
        SymptomTrackerService.record_symptom(
            profile_id="agenda_user",
            category="Pelvic & Menstrual",
            symptom="Pelvic Pain",
            onset_date=f"2026-10-1{i}",
            severity=6 + i,
            db_path=isolated_db
        )

    entries = SymptomTrackerService.get_history("agenda_user", db_path=isolated_db)
    engine = InsightsEngine(entries)

    agenda = engine.generate_doctor_talking_points("Diagnostic Evaluation")
    assert agenda["goal"] == "Diagnostic Evaluation"
    assert "Pelvic Pain" in agenda["opening_statement"]
    assert len(agenda["suggested_questions"]) >= 3


def test_backend_cooccurrence_heatmap(isolated_db):
    """Verifies that plot_cooccurrence_heatmap produces a valid Plotly Figure."""
    create_profile("co_user", "Co User", db_path=isolated_db)
    # Add pairs on same date
    SymptomTrackerService.record_symptom(
        profile_id="co_user",
        category="Neurological & Head",
        symptom="Migraine",
        onset_date="2026-10-20",
        severity=7,
        db_path=isolated_db
    )
    SymptomTrackerService.record_symptom(
        profile_id="co_user",
        category="Systemic & Energy",
        symptom="Severe Fatigue",
        onset_date="2026-10-20",
        severity=5,
        db_path=isolated_db
    )

    entries = SymptomTrackerService.get_history("co_user", db_path=isolated_db)
    engine = InsightsEngine(entries)
    fig = engine.plot_cooccurrence_heatmap()
    assert fig is not None

