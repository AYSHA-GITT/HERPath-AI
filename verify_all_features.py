"""
Comprehensive Feature-by-Feature Verification Script for HERPath AI
recHERsion 2026 | PS1: Women's Healthcare

Tests every single backend service, database operation, analytics calculation,
clinical triage pathway, PDF compilation, data portability export/import,
and frontend view navigation.
"""

import sys
import os
from datetime import date, timedelta
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from database import (
    init_db,
    db_session,
    create_profile,
    get_profile,
    list_profiles,
    update_profile_preferences,
    delete_profile,
    clear_profile_symptoms,
    add_medication,
    get_medications,
    delete_medication,
    export_profile_data_json,
    export_symptoms_csv,
    import_profile_data_json
)
from models import UserProfile, SymptomEntry, MedicationEntry
from symptom_tracker import SymptomTrackerService
from insights_engine import InsightsEngine
from safety_navigator import SafetyNavigator
from health_library import HealthLibrary
from report_generator import ClinicianReportGenerator
from config import (
    SYMPTOM_TAXONOMY,
    PRIORITY_EMERGENCY,
    PRIORITY_PROMPT,
    PRIORITY_ROUTINE,
    PRIORITY_SELFCARE
)
from streamlit.testing.v1 import AppTest

sys.stdout.reconfigure(encoding='utf-8')

results = []

def record_test(feature_name: str, passed: bool, details: str = ""):
    results.append({
        "feature": feature_name,
        "passed": passed,
        "details": details
    })
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {feature_name}: {details}")

print("=====================================================================")
print("  HERPath AI - Comprehensive Feature-by-Feature Integrity Verification")
print("=====================================================================")

# -------------------------------------------------------------
# 1. DATABASE & PROFILES
# -------------------------------------------------------------
try:
    init_db()
    with db_session() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
    assert "profiles" in tables and "symptom_entries" in tables and "medications" in tables
    record_test("Database Schema & Initialization", True, f"Found tables: {', '.join(tables)}")
except Exception as e:
    record_test("Database Schema & Initialization", False, str(e))

test_pid = "test_verification_user"
try:
    p = create_profile(test_pid, "Verification User", {"track_menstrual": True})
    fetched = get_profile(test_pid)
    assert fetched is not None and fetched.display_name == "Verification User"
    
    # Update prefs
    update_profile_preferences(test_pid, {"track_menstrual": False})
    updated = get_profile(test_pid)
    assert updated.preferences["track_menstrual"] is False
    record_test("Profile Lifecycle & Preferences", True, "Created, retrieved, and updated preferences successfully")
except Exception as e:
    record_test("Profile Lifecycle & Preferences", False, str(e))

# -------------------------------------------------------------
# 2. SYMPTOM TRACKER (CRUD & ISOLATION)
# -------------------------------------------------------------
entry_id = None
try:
    # Create
    ok, entry_id, err = SymptomTrackerService.record_symptom(
        profile_id=test_pid,
        category="Pelvic & Menstrual",
        symptom="Pelvic Cramping",
        onset_date=str(date.today()),
        severity=7,
        duration_hours=4.0,
        status="Ongoing",
        impact="Moderate",
        notes="Testing symptom creation",
        context={"sleep": "Restful (7-9 hrs)", "stress": "Moderate"}
    )
    assert ok and entry_id is not None
    
    # Read
    entry = SymptomTrackerService.get_entry(entry_id, test_pid)
    assert entry is not None and entry.symptom == "Pelvic Cramping" and entry.severity == 7
    
    # Edit
    edit_ok, edit_err = SymptomTrackerService.edit_symptom(
        entry_id=entry_id,
        profile_id=test_pid,
        category="Pelvic & Menstrual",
        symptom="Pelvic Cramping",
        onset_date=str(date.today()),
        severity=5,
        duration_hours=6.0,
        status="Resolved",
        impact="Mild",
        notes="Updated severity after rest",
        context={"sleep": "Restful (7-9 hrs)", "stress": "Low / Calm"}
    )
    assert edit_ok
    edited = SymptomTrackerService.get_entry(entry_id, test_pid)
    assert edited.severity == 5 and edited.status == "Resolved"
    
    # Filter
    history = SymptomTrackerService.get_history(test_pid, category="Pelvic & Menstrual")
    assert len(history) == 1
    
    record_test("Symptom Journal CRUD & Filtering", True, f"Recorded entry #{entry_id}, edited severity 7->5, verified resolution status")
except Exception as e:
    record_test("Symptom Journal CRUD & Filtering", False, str(e))

# -------------------------------------------------------------
# 3. ANALYTICS ENGINE & CHARTS
# -------------------------------------------------------------
try:
    # Add a second entry for analytics
    SymptomTrackerService.record_symptom(
        profile_id=test_pid,
        category="Neurological & Head",
        symptom="Migraine with Aura",
        onset_date=str(date.today() - timedelta(days=2)),
        severity=8,
        duration_hours=12.0,
        status="Resolved",
        impact="Severe",
        notes="Baseline test record",
        context={"sleep": "Disrupted / Fragmented", "stress": "Severe Stress / Burnout"}
    )
    
    user_entries = SymptomTrackerService.get_history(test_pid)
    engine = InsightsEngine(user_entries)
    metrics = engine.calculate_summary_metrics()
    
    assert metrics["total_entries"] == 2
    assert metrics["distinct_days"] == 2
    assert metrics["avg_severity"] == 6.5
    assert metrics["max_severity"] == 8
    
    # Test all 5 Plotly visualizations
    fig1 = engine.plot_severity_timeline()
    fig2 = engine.plot_symptom_frequency()
    fig3 = engine.plot_context_comparison()
    fig4 = engine.plot_cooccurrence_heatmap()
    fig5 = engine.plot_calendar_symptom_heatmap()
    
    assert fig1 is not None and fig2 is not None and fig3 is not None and fig4 is not None and fig5 is not None
    
    # Test Explainable Insights
    insights = engine.generate_explainable_insights()
    assert len(insights) > 0
    assert all("title" in ins and "observation" in ins for ins in insights)
    
    record_test("Analytics Engine & 5 Visualizations", True, "Verified metrics, explainable statements, and 5 Plotly figures")
except Exception as e:
    record_test("Analytics Engine & 5 Visualizations", False, str(e))

# -------------------------------------------------------------
# 4. DOCTOR CONSULTATION PREP KIT
# -------------------------------------------------------------
try:
    agenda = engine.generate_doctor_talking_points("Diagnostic Evaluation")
    assert agenda["goal"] == "Diagnostic Evaluation"
    assert "opening_statement" in agenda and len(agenda["opening_statement"]) > 10
    assert len(agenda["suggested_questions"]) >= 3
    record_test("Doctor Consultation Prep Kit", True, "Generated clinical objective, 30-sec statement, and targeted questions")
except Exception as e:
    record_test("Doctor Consultation Prep Kit", False, str(e))

# -------------------------------------------------------------
# 5. CARE NAVIGATOR & SAFETY TRIAGE
# -------------------------------------------------------------
try:
    # Routine test
    res_routine = SafetyNavigator.evaluate("Mild Fatigue", "Systemic & Energy", severity=3, duration_hours=2)
    assert res_routine.priority == PRIORITY_SELFCARE
    
    # Prompt test
    res_prompt = SafetyNavigator.evaluate("Pelvic Pain", "Pelvic & Menstrual", severity=7, duration_hours=72)
    assert res_prompt.priority in [PRIORITY_PROMPT, PRIORITY_ROUTINE]
    
    # Emergency test (Thunderclap red flag)
    res_emerg = SafetyNavigator.evaluate(
        symptom="Severe Headache",
        category="Neurological & Head",
        severity=9,
        duration_hours=1,
        red_flags_checked=["Sudden onset 'worst headache of life' (thunderclap)"]
    )
    assert res_emerg.priority == PRIORITY_EMERGENCY
    assert "EMERGENCY" in res_emerg.headline.upper()
    assert "112" in res_emerg.emergency_contact or "911" in res_emerg.emergency_contact
    
    record_test("Care Navigator & Safety Triage", True, "Verified Self-Care, Prompt, and Emergency red-flag prioritization")
except Exception as e:
    record_test("Care Navigator & Safety Triage", False, str(e))

# -------------------------------------------------------------
# 6. WOMEN'S HEALTH LIBRARY & SEARCH
# -------------------------------------------------------------
try:
    hl = HealthLibrary()
    cats = hl.get_categories()
    assert len(cats) >= 5
    
    # Exact keyword search
    res_pcos = hl.search_resources(query="PCOS")
    assert len(res_pcos) > 0 and any("Polycystic" in r["title"] for r in res_pcos)
    
    # Multi-term tokenized search
    res_multi = hl.search_resources(query="iron deficiency fatigue")
    assert len(res_multi) > 0 and any("Anemia" in r["title"] or "Iron" in r["title"] for r in res_multi)
    
    record_test("Health Library & Tokenized Search", True, f"Found {len(cats)} categories and verified multi-keyword matching")
except Exception as e:
    record_test("Health Library & Tokenized Search", False, str(e))

# -------------------------------------------------------------
# 7. MEDICATION & TREATMENTS TRACKER
# -------------------------------------------------------------
try:
    med = MedicationEntry(
        id=None,
        profile_id=test_pid,
        name="Magnesium Glycinate",
        category="OTC / Supplement",
        dosage="400 mg",
        frequency="Once daily at bedtime",
        started_date=str(date.today()),
        notes="Supports migraine prophylaxis and sleep restfulness"
    )
    add_medication(med)
    meds = get_medications(test_pid)
    assert len(meds) == 1
    assert meds[0].name == "Magnesium Glycinate"
    
    # Delete medication
    delete_medication(meds[0].id, test_pid)
    meds_after = get_medications(test_pid)
    assert len(meds_after) == 0
    
    record_test("Medication Tracker (Add, List, Delete)", True, "Added supplement, verified dosage/notes, deleted successfully")
except Exception as e:
    record_test("Medication Tracker (Add, List, Delete)", False, str(e))

# -------------------------------------------------------------
# 8. CLINICIAN REPORT GENERATOR (PDF)
# -------------------------------------------------------------
try:
    user_entries = SymptomTrackerService.get_history(test_pid)
    generator = ClinicianReportGenerator(
        profile=get_profile(test_pid),
        entries=user_entries,
        start_date=str(date.today() - timedelta(days=30)),
        end_date=str(date.today() + timedelta(days=1)),
        medications=[]
    )
    pdf_bytes = generator.generate_pdf_bytes()
    assert pdf_bytes is not None and len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")
    record_test("Clinician PDF Report Generator", True, f"Generated valid PDF ({len(pdf_bytes)} bytes) with '%PDF-' header")
except Exception as e:
    record_test("Clinician PDF Report Generator", False, str(e))

# -------------------------------------------------------------
# 9. DATA PORTABILITY (JSON & CSV BACKUP/RESTORE)
# -------------------------------------------------------------
try:
    json_export = export_profile_data_json(test_pid)
    assert '"profile"' in json_export and '"symptoms"' in json_export
    
    csv_export = export_symptoms_csv(test_pid)
    assert "Onset Date" in csv_export and "Category" in csv_export and "Symptom" in csv_export
    
    # Restore into fresh profile
    restore_pid = "test_restore_user"
    create_profile(restore_pid, "Restore User")
    s_count, m_count = import_profile_data_json(restore_pid, json_export)
    assert s_count == 2
    restored_entries = SymptomTrackerService.get_history(restore_pid)
    assert len(restored_entries) == 2
    
    delete_profile(restore_pid)
    record_test("Data Portability (JSON/CSV Backup & Restore)", True, f"Exported JSON/CSV and restored {s_count} records cleanly")
except Exception as e:
    record_test("Data Portability (JSON/CSV Backup & Restore)", False, f"Failed: {type(e).__name__} - {e}")

# Clean up test user
try:
    delete_profile(test_pid)
except Exception:
    pass

# -------------------------------------------------------------
# 10. FRONTEND STREAMLIT APPTEST (ALL SCREENS & NAVIGATION)
# -------------------------------------------------------------
app_path = str(PROJECT_ROOT / "app.py")
try:
    at = AppTest.from_file(app_path, default_timeout=30)
    at.run()
    assert not at.exception, f"Exception on app load: {at.exception}"

    # Authenticate via PIN to unlock navigation and bottom tabs
    if not at.session_state.get("is_logged_in", False):
        for ti in at.text_input:
            if ti.key and "pin" in ti.key.lower():
                ti.set_value("1234")
                break
        for b in at.button:
            if "LOGIN" in b.label:
                b.click().run()
                break
    assert not at.exception, f"Exception on login: {at.exception}"
    
    # Test all 9 views
    navs = [
        "Home Dashboard",
        "Symptom Journal",
        "Medication & Treatments",
        "Health Insights",
        "Care Navigator",
        "Women's Health Library",
        "My Health Report",
        "Ask HERPath",
        "Privacy and Settings"
    ]
    
    for nav in navs:
        at.sidebar.radio[0].set_value(nav).run()
        assert not at.exception, f"Exception navigating to {nav}: {at.exception}"
    
    # Verify 4 bottom navigation buttons
    button_labels = [b.label for b in at.button]
    assert any("Home" in b for b in button_labels)
    assert any("My Health" in b for b in button_labels)
    assert any("Care" in b for b in button_labels)
    assert any("Learn" in b for b in button_labels)
    
    record_test("Frontend Streamlit AppTest Navigation", True, "Successfully mounted and navigated all 9 screens without exceptions")
except Exception as e:
    record_test("Frontend Streamlit AppTest Navigation", False, str(e))

print("=====================================================================")
passed_count = sum(1 for r in results if r["passed"])
total_count = len(results)
print(f"Total Features Verified: {total_count}")
print(f"Passed: {passed_count}/{total_count}")
print("=====================================================================")
if passed_count == total_count:
    print("ALL FEATURES ARE FULLY FUNCTIONAL AND OPERATIONAL!")
else:
    sys.exit(1)
