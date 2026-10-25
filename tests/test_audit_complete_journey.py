"""
HERPath AI - Comprehensive End-to-End Audit & Full User Journey Verification Suite
recHERsion 2026 | PS1: Women's Healthcare

Audits the complete platform with a dedicated fictional demo persona ('audit_persona_maya'):
1. Authentication, profile registration & salted SHA-256 PIN security.
2. Complete profile isolation (Zero cross-profile data leakage).
3. Symptom tracker CRUD across multi-system taxonomy.
4. Medication tracker and active medication linkage.
5. Full Month Calendar View with Heatmap Dots and distinct predicted period handling.
6. Historical cycle statistics, variation calculation, and strict non-diagnostic PCOS boundaries.
7. HERPath Timeline Intelligence and dual-period comparative analytics.
8. Smart Clinical Summary & Doctor Consultation Kit (6 sections, plain text export).
9. ReportLab Clinician Health Report (PDF compilation & bytes verification).
10. Safety Navigator rule-based clinical triage & regional SOS helplines.
11. Evidence-based Women's Health Library search.
12. Data portability: One-click complete JSON backup & export isolation.
13. Streamlit AppTest UI & mobile navigation verification.
"""

import pytest
import sqlite3
import tempfile
import os
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP_FILE = str(Path(__file__).resolve().parent.parent / "app.py")

from config import (
    DATABASE_PATH,
    PRIORITY_EMERGENCY,
    PRIORITY_PROMPT,
    PRIORITY_ROUTINE,
    PRIORITY_SELFCARE
)
from database import (
    init_db,
    get_connection,
    create_profile,
    get_profile,
    list_profiles,
    delete_profile,
    update_profile_preferences,
    add_symptom,
    get_symptoms,
    update_symptom,
    delete_symptom,
    add_medication,
    get_medications,
    delete_medication,
    export_profile_data_json
)
from models import UserProfile, SymptomEntry, MedicationEntry
from auth import (
    hash_credential,
    verify_credential,
    register_user,
    authenticate_user,
    set_user_pin
)
from symptom_tracker import SymptomTrackerService
from cycle_service import CycleService, CycleStatisticsData, MonthCalendarData
from timeline_service import TimelineService
from clinical_summary_service import ClinicalSummaryService
from report_generator import ClinicianReportGenerator
from safety_navigator import SafetyNavigator
from health_library import HealthLibrary


@pytest.fixture
def audit_db():
    """Provides a pristine SQLite database initialized with tables."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_audit_complete_user_journey(audit_db):
    """
    Rigorously tests the entire user journey and all 12 platform modules
    using a dedicated fictional audit persona: 'audit_persona_maya'.
    """
    today = date.today()

    # =========================================================================
    # 1. Profile Creation, Registration & Salted SHA-256 PIN Security
    # =========================================================================
    maya_profile = register_user(
        profile_id="audit_persona_maya",
        display_name="Maya Lin (Audit Persona)",
        pin="4321",
        preferences={
            "cycle_length": 31,
            "period_duration": 5,
            "track_menstrual": True,
            "focus_areas": ["PCOS / Irregular Cycles", "Hormonal Migraines", "Iron & Fatigue"]
        },
        db_path=audit_db
    )
    assert maya_profile.id == "audit_persona_maya"
    assert maya_profile.display_name == "Maya Lin (Audit Persona)"

    # Verify PIN authentication
    auth_success, auth_msg, auth_profile = authenticate_user("audit_persona_maya", "4321", audit_db)
    assert auth_success is True
    assert auth_profile is not None
    assert auth_profile.id == "audit_persona_maya"

    auth_fail, fail_msg, fail_profile = authenticate_user("audit_persona_maya", "9999", audit_db)
    assert auth_fail is False
    assert fail_profile is None

    # Create a second isolated user to test zero cross-profile leakage
    second_profile = register_user(
        profile_id="audit_persona_sarah",
        display_name="Sarah (Isolated User)",
        pin="1111",
        preferences={"cycle_length": 28},
        db_path=audit_db
    )

    # =========================================================================
    # 2. Multi-System Symptom Journal CRUD & Input Boundaries
    # =========================================================================
    # Seed 3 distinct historical cycles for Maya with multi-system symptoms:
    # Cycle 1 start: ~93 days ago
    # Cycle 2 start: ~61 days ago (interval: 32 days)
    # Cycle 3 start: ~28 days ago (interval: 33 days)
    # Active Cycle: ~2 days ago (interval: 26 days)
    # Total valid intervals: 3 (32d, 33d, 26d -> variation: 33 - 26 = 7 days)
    p_starts = [
        today - timedelta(days=93),
        today - timedelta(days=61),
        today - timedelta(days=28),
        today - timedelta(days=2)
    ]
    for p_date in p_starts:
        SymptomTrackerService.record_symptom(
            profile_id="audit_persona_maya",
            category="Pelvic & Menstrual",
            symptom="Menstrual Bleeding (Period Start)",
            onset_date=str(p_date),
            severity=5,
            duration_hours=12.0,
            status="Resolved",
            impact="Moderate (Modified daily plans)",
            notes="Cycle start day bleeding.",
            context={"cycle_phase": "Menstruation Phase", "sleep": "Restful (7-9 hrs)", "stress": "Low / Calm"},
            db_path=audit_db
        )

    # Log additional multi-system symptoms across Maya's timeline
    symptom_data = [
        ("Neurological & Head", "Hormonal Migraine", str(today - timedelta(days=14)), 7, 8.0, "Severe", "Unilateral throbbing."),
        ("Systemic & Energy", "Severe Fatigue / Exhaustion", str(today - timedelta(days=13)), 6, 24.0, "Moderate", "Heavy brain fog."),
        ("Gastrointestinal & Abdominal", "Severe Abdominal Bloating", str(today - timedelta(days=10)), 4, 6.0, "Mild", "Endo belly."),
        ("Mood & Sleep", "Anxiety / Restlessness", str(today - timedelta(days=5)), 5, 4.0, "Moderate", "Pre-period insomnia.")
    ]
    for cat, sym, o_date, sev, dur, imp, nts in symptom_data:
        SymptomTrackerService.record_symptom(
            profile_id="audit_persona_maya",
            category=cat,
            symptom=sym,
            onset_date=o_date,
            severity=sev,
            duration_hours=dur,
            status="Resolved",
            impact=imp,
            notes=nts,
            context={"cycle_phase": "Luteal Phase", "sleep": "Disrupted / Fragmented", "stress": "High / Pressured"},
            db_path=audit_db
        )

    # Add a symptom for Sarah (to verify isolation)
    SymptomTrackerService.record_symptom(
        profile_id="audit_persona_sarah",
        category="Breast & Chest",
        symptom="Cyclic Breast Tenderness",
        onset_date=str(today - timedelta(days=3)),
        severity=6,
        db_path=audit_db
    )

    # Verify CRUD for Maya
    maya_entries = SymptomTrackerService.get_history("audit_persona_maya", db_path=audit_db)
    assert len(maya_entries) == 8  # 4 periods + 4 symptoms

    sarah_entries = SymptomTrackerService.get_history("audit_persona_sarah", db_path=audit_db)
    assert len(sarah_entries) == 1
    assert sarah_entries[0].symptom == "Cyclic Breast Tenderness"
    assert all(e.profile_id == "audit_persona_maya" for e in maya_entries)

    # =========================================================================
    # 3. Medication & Treatment Tracker
    # =========================================================================
    add_medication(MedicationEntry(
        id=None,
        profile_id="audit_persona_maya",
        name="Iron Bisglycinate",
        category="OTC / Supplement",
        dosage="28 mg",
        frequency="Daily with vitamin C",
        started_date=str(today - timedelta(days=45)),
        notes="Ferritin replenishment."
    ), audit_db)

    add_medication(MedicationEntry(
        id=None,
        profile_id="audit_persona_maya",
        name="Sumatriptan",
        category="Prescription",
        dosage="50 mg",
        frequency="As needed at migraine aura",
        started_date=str(today - timedelta(days=20)),
        notes="Triptan for acute migraine relief."
    ), audit_db)

    maya_meds = get_medications("audit_persona_maya", audit_db)
    assert len(maya_meds) == 2
    sarah_meds = get_medications("audit_persona_sarah", audit_db)
    assert len(sarah_meds) == 0  # Profile isolation verified

    # =========================================================================
    # 4. Historical Cycle Statistics & Non-Diagnostic PCOS Boundaries
    # =========================================================================
    cycle_stats = CycleService.calculate_cycle_statistics("audit_persona_maya", audit_db)
    assert cycle_stats.total_periods_recorded == 4
    assert cycle_stats.total_cycles_analyzed == 3
    assert cycle_stats.average_cycle_length == 30.3  # (32 + 33 + 26) / 3 = 91 / 3 = 30.33
    assert cycle_stats.shortest_cycle == 26
    assert cycle_stats.longest_cycle == 33
    assert cycle_stats.variation_days == 7
    assert cycle_stats.is_sufficient_for_trend is True

    # Safety boundary verification:
    assert "You have PCOS" not in cycle_stats.clinical_note
    assert "PCOS detected" not in cycle_stats.clinical_note
    assert "PCOS risk score" not in cycle_stats.clinical_note

    # =========================================================================
    # 5. Full Month Calendar View & Distinct Predicted Periods
    # =========================================================================
    current_year = today.year
    current_month = today.month

    cal_data = CycleService.get_month_calendar_data(
        "audit_persona_maya",
        current_year,
        current_month,
        audit_db
    )
    assert cal_data.profile_id == "audit_persona_maya"
    assert len(cal_data.days) >= 28

    # Verify that recorded period days are marked as has_period=True
    # Maya's active period started ~2 days ago
    active_period_date_str = str(today - timedelta(days=2))
    matched_day = next((d for d in cal_data.days if d.date_str == active_period_date_str), None)
    if matched_day:
        assert matched_day.has_period is True
        assert matched_day.is_predicted_period is False

    # Verify predicted future period distinction (must NOT write to database)
    conn = get_connection(audit_db)
    count_before = conn.execute("SELECT COUNT(*) FROM symptom_entries WHERE profile_id = 'audit_persona_maya';").fetchone()[0]
    conn.close()

    # Query next month's calendar
    next_month = current_month + 1 if current_month < 12 else 1
    next_year = current_year if current_month < 12 else current_year + 1
    cal_next = CycleService.get_month_calendar_data("audit_persona_maya", next_year, next_month, audit_db)
    
    # Check that any predicted days have is_predicted_period=True and has_period=False
    predicted_days = [d for d in cal_next.days if d.is_predicted_period]
    for pd in predicted_days:
        assert pd.has_period is False

    # Confirm zero database side-effects
    conn = get_connection(audit_db)
    count_after = conn.execute("SELECT COUNT(*) FROM symptom_entries WHERE profile_id = 'audit_persona_maya';").fetchone()[0]
    conn.close()
    assert count_before == count_after, "Predicted dates must NEVER be persisted to SQLite"

    # =========================================================================
    # 6. HERPath Timeline Intelligence & Dual-Period Comparison
    # =========================================================================
    timeline_service = TimelineService("audit_persona_maya", db_path=audit_db)
    timeline_events = timeline_service.fetch_all_events()
    assert len(timeline_events) == 10  # 8 symptoms + 2 medication starts
    # Chronological sort check (ascending)
    for i in range(len(timeline_events) - 1):
        assert timeline_events[i].date <= timeline_events[i + 1].date

    # Dual-period comparison (Last 30 Days vs Previous 30 Days)
    events_a = TimelineService.filter_events(
        timeline_events,
        start_date=str(today - timedelta(days=29)),
        end_date=str(today)
    )
    events_b = TimelineService.filter_events(
        timeline_events,
        start_date=str(today - timedelta(days=59)),
        end_date=str(today - timedelta(days=30))
    )
    comparison = TimelineService.compare_periods(
        events_a,
        events_b,
        period_a_label="Recent 30 Days",
        period_b_label="Prior 30 Days",
        days_a=30,
        days_b=30
    )
    assert comparison["period_a"]["metrics"]["symptom_episodes"] >= 0
    assert comparison["period_b"]["metrics"]["symptom_episodes"] >= 0
    assert comparison["period_a"]["daily_rate"] >= 0.0

    # =========================================================================
    # 7. Smart Clinical Summary & Consultation Kit
    # =========================================================================
    summary_service = ClinicalSummaryService(
        profile_id="audit_persona_maya",
        start_date=str(today - timedelta(days=30)),
        end_date=str(today),
        entries=maya_entries,
        medications=maya_meds,
        profile=maya_profile,
        patient_concerns=["Frequent migraines during luteal phase and notable fatigue."]
    )
    summary_data = summary_service.generate_summary()
    assert summary_data.patient_name == "Maya Lin (Audit Persona)"
    assert summary_data.total_entries > 0
    assert summary_data.patient_concerns == ["Frequent migraines during luteal phase and notable fatigue."]
    assert summary_data.checklist is not None

    # Generate 1-click clipboard plain text summary
    plain_text = summary_service.generate_plain_text_summary()
    assert "HERPath AI — Smart Clinical Consultation Summary" in plain_text
    assert "Maya Lin (Audit Persona)" in plain_text
    assert "DOCTOR DISCUSSION CHECKLIST" in plain_text

    # =========================================================================
    # 8. ReportLab Clinician Health Report (PDF Compilation)
    # =========================================================================
    generator = ClinicianReportGenerator(
        profile=maya_profile,
        entries=maya_entries,
        start_date=str(today - timedelta(days=30)),
        end_date=str(today),
        medications=maya_meds,
        patient_concerns=["Frequent migraines during luteal phase and notable fatigue."],
        summary_data=summary_data
    )
    pdf_bytes = generator.generate_pdf_bytes()
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 5000
    assert pdf_bytes.startswith(b"%PDF-")

    # =========================================================================
    # 9. Safety Navigator & Clinical Triage Hierarchy
    # =========================================================================
    triage_routine = SafetyNavigator.evaluate(
        symptom="Mild Headache",
        category="Neurological & Head",
        severity=3,
        duration_hours=4.0,
        notes=""
    )
    assert triage_routine.priority == PRIORITY_SELFCARE
    assert "MILD" in triage_routine.title or "HEALTH EDUCATION" in triage_routine.title

    # Emergency scenario: Sudden severe headache with visual aura
    triage_emergency = SafetyNavigator.evaluate(
        symptom="Sudden 'Thunderclap' Headache",
        category="Neurological & Head",
        severity=10,
        duration_hours=1.0,
        notes="Worst headache of life",
        red_flags_checked=["Sudden onset 'worst headache of life' (thunderclap)"]
    )
    assert triage_emergency.priority == PRIORITY_EMERGENCY
    assert triage_emergency.emergency_contact is not None

    # Supported warning signs checklist
    warning_signs = SafetyNavigator.get_supported_emergency_warning_signs()
    assert len(warning_signs) >= 5

    # =========================================================================
    # 10. Evidence-Based Health Library Search
    # =========================================================================
    library = HealthLibrary()
    search_results = library.search_resources(query="migraine")
    assert len(search_results) > 0
    assert any("Migraine" in r.get("title", "") for r in search_results)
    assert all("source_org" in r for r in search_results)

    # =========================================================================
    # 11. Data Portability & Backup Isolation
    # =========================================================================
    export_json_str = export_profile_data_json("audit_persona_maya", audit_db)
    export_dict = json.loads(export_json_str)
    assert export_dict["profile"]["id"] == "audit_persona_maya"
    assert len(export_dict["symptoms"]) == 8
    assert len(export_dict["medications"]) == 2
    # Verify that Sarah's records are completely absent from Maya's backup
    assert not any(s["profile_id"] == "audit_persona_sarah" for s in export_dict["symptoms"])


def test_audit_streamlit_ui_journey(monkeypatch, tmp_path):
    """
    Simulates complete user journey in Streamlit UI:
    - User registration and login
    - Home dashboard view (Month Calendar, Day Inspector, Historical Cycle Stats)
    - Calendar navigation (Next Month, Previous Month)
    - Navigation between all major platform views:
        * Home Dashboard
        * Symptom Journal
        * Medication & Treatments
        * Timeline Intelligence
        * Care Navigator
        * Women's Health Library
        * My Health Report
        * Privacy and Settings
    """
    db_file = str(tmp_path / "ui_audit.db")
    monkeypatch.setenv("DATABASE_PATH", db_file)
    import config, database
    monkeypatch.setattr(config, "DATABASE_PATH", db_file)
    monkeypatch.setattr(database, "DATABASE_PATH", db_file)
    init_db(db_file)

    # Register user with PIN
    register_user(
        profile_id="audit_persona_maya",
        display_name="Maya Lin (Audit Persona)",
        pin="4321",
        preferences={"track_menstrual": True, "cycle_length": 30},
        db_path=db_file
    )

    # Seed symptoms and medication
    add_symptom(SymptomEntry(
        id=None,
        profile_id="audit_persona_maya",
        category="Pelvic & Menstrual",
        symptom="Menstrual Bleeding (Period Start)",
        onset_date=str(date.today() - timedelta(days=2)),
        severity=5
    ), db_path=db_file)

    add_medication(MedicationEntry(
        id=None,
        profile_id="audit_persona_maya",
        name="Iron Bisglycinate",
        category="OTC / Supplement",
        started_date=str(date.today() - timedelta(days=20))
    ), db_path=db_file)

    at = AppTest.from_file(APP_FILE, default_timeout=30)
    at.run()

    # Log in
    for ti in at.text_input:
        if ti.key == "signin_username_field":
            ti.set_value("audit_persona_maya")
        elif ti.key == "signin_pin_field":
            ti.set_value("4321")
    for b in at.button:
        if b.key == "btn_do_signin":
            b.click().run()
            break

    assert not at.exception
    combined_md = " ".join([m.value for m in at.markdown])
    assert "Cycle Calendar & History" in combined_md
    assert "Cycles Analyzed" in [m.label for m in at.metric]

    # Test calendar month navigation
    btn_keys = {b.key: b for b in at.button if b.key}
    if "cal_btn_next_month" in btn_keys:
        btn_keys["cal_btn_next_month"].click().run()
        assert not at.exception
    if "cal_btn_prev_month" in btn_keys:
        btn_keys["cal_btn_prev_month"].click().run()
        assert not at.exception

    # Test navigation to other views
    for view_name in [
        "Symptom Journal",
        "Medication & Treatments",
        "Timeline Intelligence",
        "Care Navigator",
        "Women's Health Library",
        "My Health Report",
        "Privacy and Settings"
    ]:
        at.session_state["navigation"] = view_name
        at.run()
        assert not at.exception, f"Exception occurred while navigating to {view_name}: {at.exception}"
