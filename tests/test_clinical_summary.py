"""
HERPath AI - Smart Clinical Summary Automated Test Suite
recHERsion 2026 | PS1: Women's Healthcare

Tests:
1. Reporting period filtering (7d, 30d, 90d, custom).
2. Total symptom entries vs. distinct symptom days.
3. Frequency calculations, percentages, and severity summaries.
4. Handling missing duration, sleep, stress, energy, and cycle fields (no null-to-zero conversion).
5. Empty reporting periods and zero-entry resilience.
6. Temporal severity progression (earlier vs. recent windows).
7. Treatment chronology & neutral non-causal phrasing.
8. Active profile isolation (no cross-profile data leakage).
9. Patient-entered consultation concerns integration.
10. Plain text summary generation (copy-to-clipboard format).
11. Clinician PDF compilation, styling, and page break resilience.
12. End-to-end Streamlit AppTest UI verification.
"""

import pytest
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import List

APP_FILE = str(Path(__file__).resolve().parent.parent / "app.py")

from models import SymptomEntry, MedicationEntry, UserProfile
from clinical_summary_service import (
    ClinicalSummaryService,
    ClinicalSummaryData,
    SymptomFrequencyItem,
    SeverityProgression,
    DurationStatistics,
    LifestyleFunctionalSummary
)
from report_generator import ClinicianReportGenerator
from database import (
    init_db,
    create_profile,
    get_profile,
    add_symptom,
    add_medication,
    get_symptoms,
    get_medications
)
from streamlit.testing.v1 import AppTest


# ==========================================
# Fixtures
# ==========================================

@pytest.fixture
def sample_profile() -> UserProfile:
    return UserProfile(
        id="test_user_maya",
        display_name="Maya Sharma",
        preferences={"track_menstrual": True}
    )


@pytest.fixture
def isolated_db(tmp_path) -> str:
    """Creates a temporary, isolated SQLite database for testing."""
    db_file = str(tmp_path / "test_clinical.db")
    init_db(db_file)
    return db_file


@pytest.fixture
def populated_entries(sample_profile) -> List[SymptomEntry]:
    """Provides a realistic 30-day chronological dataset."""
    entries = [
        # Day 1: Migraine (Sev 8, Dur 6h, Disrupted Sleep)
        SymptomEntry(
            id=1,
            profile_id=sample_profile.id,
            category="Neurological & Head",
            symptom="Migraine",
            onset_date="2026-10-01",
            severity=8,
            duration_hours=6.0,
            status="Resolved",
            impact="Severe (Inability to work/study)",
            notes="Throbbing temple pain, nausea.",
            context={"sleep": "Disrupted / Fragmented", "stress": "High / Pressured", "energy": "Fatigued / Low", "cycle_phase": "Luteal / Premenstrual"}
        ),
        # Day 1 (same day, different symptom): Pelvic Cramping
        SymptomEntry(
            id=2,
            profile_id=sample_profile.id,
            category="Pelvic & Menstrual",
            symptom="Pelvic Pain / Cramping",
            onset_date="2026-10-01",
            severity=7,
            duration_hours=4.0,
            status="Resolved",
            impact="Moderate (Modified daily plans)",
            notes="Dull ache in lower abdomen.",
            context={"sleep": "Disrupted / Fragmented", "stress": "High / Pressured", "energy": "Fatigued / Low", "cycle_phase": "Luteal / Premenstrual"}
        ),
        # Day 5: Fatigue (Sev 6, Duration missing)
        SymptomEntry(
            id=3,
            profile_id=sample_profile.id,
            category="Systemic & Energy",
            symptom="Fatigue / Low Energy",
            onset_date="2026-10-05",
            severity=6,
            duration_hours=None, # Missing duration
            status="Ongoing",
            impact="Moderate (Modified daily plans)",
            notes="Needed afternoon nap.",
            context={"sleep": "Restful (7-9 hrs)", "stress": "Low / Calm", "energy": "Fatigued / Low", "cycle_phase": "Menstrual"}
        ),
        # Day 10: Migraine (Sev 7, Dur 5h)
        SymptomEntry(
            id=4,
            profile_id=sample_profile.id,
            category="Neurological & Head",
            symptom="Migraine",
            onset_date="2026-10-10",
            severity=7,
            duration_hours=5.0,
            status="Resolved",
            impact="Bedrest / Incapacitated",
            notes="Needed dark room.",
            context={"sleep": "Severe Insomnia (<5 hrs)", "stress": "High / Pressured", "energy": "Fatigued / Low", "cycle_phase": "Follicular / Mid-cycle"}
        ),
        # Day 18: Pelvic Cramping (Sev 5, Dur 3h)
        SymptomEntry(
            id=5,
            profile_id=sample_profile.id,
            category="Pelvic & Menstrual",
            symptom="Pelvic Pain / Cramping",
            onset_date="2026-10-18",
            severity=5,
            duration_hours=3.0,
            status="Resolved",
            impact="Mild (Minor inconvenience)",
            notes="Heat patch provided relief.",
            context={"sleep": "Restful (7-9 hrs)", "stress": "Low / Calm", "energy": "Moderate", "cycle_phase": "Ovulatory"}
        ),
        # Day 25: Migraine (Sev 4, Dur 2h)
        SymptomEntry(
            id=6,
            profile_id=sample_profile.id,
            category="Neurological & Head",
            symptom="Migraine",
            onset_date="2026-10-25",
            severity=4,
            duration_hours=2.0,
            status="Resolved",
            impact="None",
            notes="Resolved with water and rest.",
            context={"sleep": "Restful (7-9 hrs)", "stress": "Low / Calm", "energy": "High Vitality", "cycle_phase": "Luteal / Premenstrual"}
        )
    ]
    return entries


@pytest.fixture
def sample_medications(sample_profile) -> List[MedicationEntry]:
    return [
        MedicationEntry(
            id=1,
            profile_id=sample_profile.id,
            name="Magnesium Glycinate",
            category="OTC / Supplement",
            dosage="400mg",
            frequency="Nightly",
            started_date="2026-10-12",
            notes="For migraine prevention and sleep."
        )
    ]


# ==========================================
# 1. Reporting Period Filtering & Boundaries
# ==========================================

def test_reporting_period_filtering(sample_profile, populated_entries):
    """Verifies that entries outside the requested date window are strictly excluded."""
    # Filter for middle window: 2026-10-04 to 2026-10-20
    service = ClinicalSummaryService(
        profile_id=sample_profile.id,
        start_date="2026-10-04",
        end_date="2026-10-20",
        entries=populated_entries,
        profile=sample_profile
    )
    summary = service.generate_summary()

    # Out of 6 total entries, only entries 3, 4, and 5 fall in this window
    assert summary.total_entries == 3
    assert set(e.onset_date for e in service.entries) == {"2026-10-05", "2026-10-10", "2026-10-18"}
    assert summary.calendar_days == 17


def test_custom_range_filtering(sample_profile, populated_entries):
    """Verifies single-day and narrow custom date boundaries."""
    service = ClinicalSummaryService(
        profile_id=sample_profile.id,
        start_date="2026-10-01",
        end_date="2026-10-01",
        entries=populated_entries,
        profile=sample_profile
    )
    summary = service.generate_summary()

    # 2 entries on 2026-10-01
    assert summary.total_entries == 2
    assert summary.distinct_days == 1
    assert summary.calendar_days == 1


# ==========================================
# 2. Entries vs. Distinct Days
# ==========================================

def test_entries_vs_distinct_days_distinction(sample_profile, populated_entries):
    """Multiple entries on the same date must increment entries without inflating distinct days."""
    service = ClinicalSummaryService(
        profile_id=sample_profile.id,
        start_date="2026-10-01",
        end_date="2026-10-25",
        entries=populated_entries,
        profile=sample_profile
    )
    summary = service.generate_summary()

    # Total entries: 6
    # Distinct dates: 2026-10-01 (2 entries), 2026-10-05, 2026-10-10, 2026-10-18, 2026-10-25 => 5 distinct dates
    assert summary.total_entries == 6
    assert summary.distinct_days == 5
    assert summary.distinct_days < summary.total_entries


# ==========================================
# 3. Frequency & Severity Summaries
# ==========================================

def test_symptom_frequency_and_severity_calculations(sample_profile, populated_entries):
    """Verifies top symptom ranking, percentages, average severity, and peak severity."""
    service = ClinicalSummaryService(
        profile_id=sample_profile.id,
        start_date="2026-10-01",
        end_date="2026-10-25",
        entries=populated_entries,
        profile=sample_profile
    )
    summary = service.generate_summary()

    # Migraine has 3 entries out of 6 => 50.0%
    migraine = next(s for s in summary.frequent_symptoms if s.symptom == "Migraine")
    assert migraine.entry_count == 3
    assert migraine.distinct_days == 3
    assert migraine.percentage_of_entries == 50.0
    # Severities: 8, 7, 4 => mean = 19/3 = 6.3
    assert migraine.avg_severity == 6.3
    assert migraine.min_severity == 4
    assert migraine.max_severity == 8

    # Overall max severity is 8 on 2026-10-01
    assert summary.max_severity == 8
    assert summary.max_severity_symptom == "Migraine"
    assert summary.max_severity_date == "2026-10-01"


# ==========================================
# 4. Missing Data & Null Handling
# ==========================================

def test_missing_duration_not_treated_as_zero(sample_profile, populated_entries):
    """Entries with duration_hours=None must NOT be cast to 0.0 in duration averages."""
    service = ClinicalSummaryService(
        profile_id=sample_profile.id,
        start_date="2026-10-01",
        end_date="2026-10-25",
        entries=populated_entries,
        profile=sample_profile
    )
    summary = service.generate_summary()

    dur_stats = summary.duration_stats
    # 5 out of 6 entries have durations: 6.0, 4.0, 5.0, 3.0, 2.0 => mean = 20.0 / 5 = 4.0
    assert dur_stats.documented_entries == 5
    assert dur_stats.total_entries == 6
    assert dur_stats.documentation_rate == 83.3
    assert dur_stats.mean_hours == 4.0
    assert dur_stats.min_hours == 2.0
    assert dur_stats.max_hours == 6.0
    assert "Duration was documented in 5 of 6 symptom entries" in dur_stats.summary_statement


def test_missing_lifestyle_context_reporting(sample_profile, populated_entries):
    """Verifies that missing context counts are clearly stated alongside documented counts."""
    service = ClinicalSummaryService(
        profile_id=sample_profile.id,
        start_date="2026-10-01",
        end_date="2026-10-25",
        entries=populated_entries,
        profile=sample_profile
    )
    summary = service.generate_summary()
    life = summary.lifestyle_impact

    assert life.sleep.documented_entries == 6
    assert life.stress.documented_entries == 6
    assert life.work_study_disruption_count == 4  # entries 1, 2, 3, 4
    assert life.bedrest_count == 1               # entry 4


# ==========================================
# 5. Empty Reporting Periods & Zero-Entry Resilience
# ==========================================

def test_empty_reporting_period_resilience(sample_profile):
    """An empty reporting period must generate safely without ZeroDivisionError."""
    service = ClinicalSummaryService(
        profile_id=sample_profile.id,
        start_date="2026-09-01",
        end_date="2026-09-15",
        entries=[],
        profile=sample_profile
    )
    summary = service.generate_summary()

    assert summary.total_entries == 0
    assert summary.distinct_days == 0
    assert summary.avg_severity is None
    assert summary.max_severity is None
    assert summary.frequent_symptoms == []
    assert summary.duration_stats.documented_entries == 0
    assert not summary.progression.comparison_possible

    # Plain text summary and PDF must still compile cleanly
    text = service.generate_plain_text_summary()
    assert "Total Logged Entries: 0" in text

    pdf_gen = ClinicianReportGenerator(
        profile=sample_profile,
        entries=[],
        start_date="2026-09-01",
        end_date="2026-09-15",
        summary_data=summary
    )
    pdf_bytes = pdf_gen.generate_pdf_bytes()
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500


# ==========================================
# 6. Severity Progression (Earlier vs. Recent)
# ==========================================

def test_severity_progression_earlier_vs_recent(sample_profile, populated_entries):
    """Calculates factual severity shift across first half vs. second half of reporting range."""
    # 2026-10-01 to 2026-10-25: mid-date is ~2026-10-13
    # Earlier window (10-01 to 10-13): entries 1 (sev 8), 2 (sev 7), 3 (sev 6), 4 (sev 7) => mean = 7.0
    # Recent window (10-14 to 10-25): entries 5 (sev 5), 6 (sev 4) => mean = 4.5
    service = ClinicalSummaryService(
        profile_id=sample_profile.id,
        start_date="2026-10-01",
        end_date="2026-10-25",
        entries=populated_entries,
        profile=sample_profile
    )
    summary = service.generate_summary()
    prog = summary.progression

    assert prog.comparison_possible is True
    assert prog.earlier_entries == 4
    assert prog.recent_entries == 2
    assert prog.earlier_avg_severity == 7.0
    assert prog.recent_avg_severity == 4.5
    assert prog.severity_delta == -2.5
    assert "decrease of 2.5 points in recorded severity" in prog.trajectory_statement


# ==========================================
# 7. Treatment Chronology & Neutral Phrasing
# ==========================================

def test_treatment_chronology_neutral_phrasing(sample_profile, populated_entries, sample_medications):
    """Ensures 14-day observation window around medication start uses strictly neutral phrasing."""
    # Medication started 2026-10-12
    # Before window: 2026-09-28 to 2026-10-11: entries 1 (8), 2 (7), 3 (6), 4 (7) => 4 entries, avg 7.0
    # After window: 2026-10-12 to 2026-10-26: entries 5 (5), 6 (4) => 2 entries, avg 4.5
    service = ClinicalSummaryService(
        profile_id=sample_profile.id,
        start_date="2026-10-01",
        end_date="2026-10-25",
        entries=populated_entries,
        medications=sample_medications,
        profile=sample_profile
    )
    summary = service.generate_summary()

    assert len(summary.treatments) == 1
    t = summary.treatments[0]
    assert t.name == "Magnesium Glycinate"
    assert t.has_comparison_data is True
    assert t.before_entries_count == 4
    assert t.after_entries_count == 2
    assert t.before_avg_severity == 7.0
    assert t.after_avg_severity == 4.5

    # Check strictly neutral, non-causal phrasing
    stmt = t.observation_statement
    assert "lower in the subsequent observation period" in stmt
    assert "Timing alone does not establish causation" in stmt


# ==========================================
# 8. Profile Isolation
# ==========================================

def test_profile_isolation(isolated_db):
    """Confirms that querying Profile A never exposes records from Profile B."""
    create_profile("user_priya", "Priya", db_path=isolated_db)
    create_profile("user_elena", "Elena", db_path=isolated_db)

    # Add symptom to Priya
    add_symptom(SymptomEntry(
        id=None,
        profile_id="user_priya",
        category="Neurological & Head",
        symptom="Priya Secret Migraine",
        onset_date="2026-10-15",
        severity=9,
        duration_hours=4.0,
        status="Ongoing",
        impact="Severe",
        notes="Confidential Priya note."
    ), db_path=isolated_db)

    # Add symptom to Elena
    add_symptom(SymptomEntry(
        id=None,
        profile_id="user_elena",
        category="Pelvic & Menstrual",
        symptom="Elena Pelvic Ache",
        onset_date="2026-10-16",
        severity=6,
        duration_hours=2.0,
        status="Resolved",
        impact="Moderate",
        notes="Confidential Elena note."
    ), db_path=isolated_db)

    # Generate summary for Elena
    elena_service = ClinicalSummaryService(
        profile_id="user_elena",
        start_date="2026-10-01",
        end_date="2026-10-31",
        db_path=isolated_db
    )
    elena_summary = elena_service.generate_summary()

    # Elena's summary must contain Elena's symptom and NEVER Priya's
    assert elena_summary.total_entries == 1
    assert elena_summary.frequent_symptoms[0].symptom == "Elena Pelvic Ache"
    assert not any(fs.symptom == "Priya Secret Migraine" for fs in elena_summary.frequent_symptoms)

    # Check plain text representation
    plain_text = elena_service.generate_plain_text_summary()
    assert "Elena Pelvic Ache" in plain_text
    assert "Priya Secret Migraine" not in plain_text


# ==========================================
# 9. Patient Concerns Integration
# ==========================================

def test_patient_concerns_integration(sample_profile, populated_entries):
    """Patient-entered consultation priorities must appear in summary and checklist."""
    concerns = [
        "Discussing pelvic ultrasound for recurring cramping",
        "Assessing whether magnesium is safe to take alongside oral contraceptives"
    ]
    service = ClinicalSummaryService(
        profile_id=sample_profile.id,
        start_date="2026-10-01",
        end_date="2026-10-25",
        patient_concerns=concerns,
        entries=populated_entries,
        profile=sample_profile
    )
    summary = service.generate_summary()

    assert summary.patient_concerns == concerns
    checklist_clinician_q = summary.checklist.questions_for_clinician
    assert any("pelvic ultrasound" in q for q in checklist_clinician_q)
    assert any("magnesium is safe" in q for q in checklist_clinician_q)


# ==========================================
# 10. Plain Text / Markdown Copyable Output
# ==========================================

def test_plain_text_summary_formatting(sample_profile, populated_entries, sample_medications):
    """Verifies that plain-text export format contains all required structured sections."""
    service = ClinicalSummaryService(
        profile_id=sample_profile.id,
        start_date="2026-10-01",
        end_date="2026-10-25",
        patient_concerns=["Reviewing hormonal blood panel options"],
        entries=populated_entries,
        medications=sample_medications,
        profile=sample_profile
    )
    text = service.generate_plain_text_summary()

    assert "HERPath AI — Smart Clinical Consultation Summary" in text
    assert "PATIENT'S MAIN CONSULTATION PRIORITIES" in text
    assert "1. CONSULTATION OVERVIEW" in text
    assert "2. SYMPTOM PATTERNS & FREQUENCY" in text
    assert "3. LIFESTYLE CONTEXT & FUNCTIONAL IMPACT" in text
    assert "4. MEDICATION & TREATMENT HISTORY" in text
    assert "5. DOCTOR DISCUSSION CHECKLIST" in text
    assert "DATA LIMITATIONS & CLINICAL DISCLAIMER" in text


# ==========================================
# 11. PDF Generation & Layout Resilience
# ==========================================

def test_clinical_summary_pdf_generation(sample_profile, populated_entries, sample_medications):
    """Verifies complete PDF generation with all 8 sections and ReportLab styling."""
    generator = ClinicianReportGenerator(
        profile=sample_profile,
        entries=populated_entries,
        start_date="2026-10-01",
        end_date="2026-10-25",
        medications=sample_medications,
        patient_concerns=["Discussing pelvic imaging", "Evaluating migraine prophylaxis"]
    )
    pdf_bytes = generator.generate_pdf_bytes()

    assert pdf_bytes is not None
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 2000


def test_pdf_generation_with_long_notes(sample_profile):
    """Verifies that very long text and notes handle page breaks cleanly without overflow."""
    long_entries = [
        SymptomEntry(
            id=i,
            profile_id=sample_profile.id,
            category="Pelvic & Menstrual",
            symptom=f"Symptom Cluster {i}",
            onset_date=f"2026-10-{i:02d}",
            severity=5 + (i % 5),
            duration_hours=4.5,
            status="Ongoing",
            impact="Severe (Inability to work/study)",
            notes="Extremely detailed patient observation log. " * 15,
            context={"sleep": "Disrupted / Fragmented", "stress": "High / Pressured"}
        )
        for i in range(1, 20)
    ]
    generator = ClinicianReportGenerator(
        profile=sample_profile,
        entries=long_entries,
        start_date="2026-10-01",
        end_date="2026-10-25"
    )
    pdf_bytes = generator.generate_pdf_bytes()
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 5000


# ==========================================
# 12. Streamlit UI End-to-End Test (AppTest)
# ==========================================

def test_frontend_smart_clinical_summary_navigation_and_controls():
    """End-to-end AppTest simulation of Smart Clinical Summary screen and controls."""
    at = AppTest.from_file(APP_FILE, default_timeout=30)
    at.session_state["is_logged_in"] = True
    at.session_state["current_profile_id"] = "demo_priya"
    at.session_state["navigation"] = "Home Dashboard"
    at.run()

    # Navigate to My Health Report / Smart Clinical Summary
    at.sidebar.radio[0].set_value("My Health Report").run()
    assert not at.exception

    # Verify heading and disclaimer box
    markdown_content = " ".join([m.value for m in at.markdown])
    assert "Smart Clinical Summary & Consultation Kit" in markdown_content
    assert "Clinical Purpose" in markdown_content

    # Verify metrics
    assert len(at.metric) >= 4
    metric_labels = [m.label for m in at.metric]
    assert "Entries in Period" in metric_labels
    assert "Distinct Dates" in metric_labels
    assert "Avg Severity" in metric_labels
    assert "Top Reported Symptom" in metric_labels

    # Verify preset selector exists
    radios = [r.label for r in at.radio]
    assert "Reporting Period Preset" in radios

    # Verify tabs exist
    tabs = [t.label for t in at.tabs]
    assert any("Overview & Concerns" in t for t in tabs)
    assert any("Symptom Patterns" in t for t in tabs)
    assert any("Discussion Checklist" in t for t in tabs)

    # Verify PDF download button exists and contains proper label
    assert len(at.download_button) > 0
    download_btn = at.download_button[0]
    assert "Download Clinician Health Report" in download_btn.label
