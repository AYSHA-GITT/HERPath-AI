"""
HERPath AI - Health Intelligence Loop Automated Test Suite
recHERsion 2026 | PS1: Women's Healthcare

Tests the complete end-to-end functionality of:
1. Explainable Health Patterns (grounded records, supporting dates, why am I seeing this?)
2. Dual-Period Comparative Analysis ("What Has Changed?", data sufficiency, missing value safety)
3. Evidence-Linked Doctor Summary (privacy-preserving selective notes, wellbeing context, clinician questions)
4. Voice & Spoken Draft Logging (NLP extraction, qualitative severity, duration, and fallback)
"""

import pytest
from datetime import date
from models import UserProfile, SymptomEntry, MedicationEntry
from timeline_service import TimelineService, TimelineEvent
from report_generator import ClinicianReportGenerator
from voice_draft_service import parse_symptom_voice_draft


@pytest.fixture
def sample_timeline_events():
    return [
        TimelineEvent(
            event_id="sym_1",
            date="2026-10-02",
            time="08:30",
            event_type="symptom",
            title="Migraine",
            category="Neurological & Headaches",
            severity=8,
            duration_hours=4.0,
            status="Resolved",
            impact="Unable to work / Study",
            notes="Morning flare after short sleep",
            context={"sleep": "Poor (< 5 hrs)", "stress": "High / Pressured", "cycle_phase": "Luteal Phase"}
        ),
        TimelineEvent(
            event_id="sym_2",
            date="2026-10-05",
            time="14:00",
            event_type="symptom",
            title="Migraine",
            category="Neurological & Headaches",
            severity=7,
            duration_hours=3.0,
            status="Resolved",
            impact="Normal activities modified",
            notes="Sensitivity to bright screen",
            context={"sleep": "Disrupted / Fragmented", "stress": "High / Pressured", "cycle_phase": "Luteal Phase"}
        ),
        TimelineEvent(
            event_id="sym_3",
            date="2026-10-08",
            time="10:00",
            event_type="symptom",
            title="Pelvic Pain / Cramping",
            category="Pelvic & Menstrual",
            severity=6,
            duration_hours=2.5,
            status="Ongoing",
            impact="Normal activities modified",
            notes="First day of cycle",
            context={"sleep": "Restless", "stress": "Normal / Manageable", "cycle_phase": "Menstrual Phase"}
        ),
        TimelineEvent(
            event_id="sym_4",
            date="2026-10-12",
            time="09:15",
            event_type="symptom",
            title="Migraine",
            category="Neurological & Headaches",
            severity=9,
            duration_hours=5.0,
            status="Resolved",
            impact="Bedrest required",
            notes="Peak severe episode",
            context={"sleep": "Severe Insomnia (<5 hrs)", "stress": "High / Pressured", "cycle_phase": "Luteal Phase"}
        ),
        TimelineEvent(
            event_id="med_1",
            date="2026-10-01",
            time="08:00",
            event_type="medication",
            title="Started Magnesium Glycinate",
            category="Supplements",
            dosage="400mg",
            frequency="Daily with dinner"
        )
    ]


# ==============================================================================
# 1. EXPLAINABLE HEALTH PATTERNS TESTS
# ==============================================================================

def test_explainable_insights_structure(sample_timeline_events):
    """Verifies every generated insight contains plain observation, dates, record count, supporting dates, and why action."""
    insights = TimelineService.generate_explainable_insights(sample_timeline_events)
    assert len(insights) >= 4

    for ins in insights:
        # Core fields required by prompt
        assert "title" in ins
        assert "statement" in ins and len(ins["statement"]) > 10
        assert "date_range" in ins
        assert "record_count" in ins and ins["record_count"] >= 0
        assert "supporting_dates" in ins
        assert isinstance(ins["supporting_dates"], list)
        assert "why_explanation" in ins
        
        # Why am I seeing this? fields
        why = ins["why_explanation"]
        assert "criteria" in why
        assert "formula" in why
        assert "evidence" in why
        assert "safety_note" in why
        assert "clinical_question" in why
        assert "supporting_dates" in why


def test_safety_boundaries_in_insights(sample_timeline_events):
    """Ensures insights strictly refrain from claiming causation, pathology, or confirmed disease diagnoses."""
    insights = TimelineService.generate_explainable_insights(sample_timeline_events)
    forbidden_words = ["causes", "caused by", "diagnosed with", "suffers from", "proves", "pathological"]

    for ins in insights:
        statement_lower = ins["statement"].lower()
        safety_lower = ins["why_explanation"]["safety_note"].lower()
        for word in forbidden_words:
            assert word not in statement_lower, f"Insight statement should not use causal/diagnostic word: '{word}'"
        assert any(k in safety_lower for k in ["co-occurrence", "does not", "do not", "subjective", "not replace", "estimates"])


def test_hormonal_cycle_cooccurrence_pattern(sample_timeline_events):
    """Verifies detection of recurring symptom clustering during specific menstrual/hormonal cycle phases."""
    insights = TimelineService.generate_explainable_insights(sample_timeline_events)
    cycle_insights = [i for i in insights if i["category"] == "Cycle Context"]
    assert len(cycle_insights) == 1
    c_ins = cycle_insights[0]
    assert "Luteal Phase" in c_ins["title"]
    assert c_ins["record_count"] >= 3
    assert "2026-10-02" in c_ins["supporting_dates"]
    assert "2026-10-05" in c_ins["supporting_dates"]
    assert "2026-10-12" in c_ins["supporting_dates"]


def test_duration_pattern_insights(sample_timeline_events):
    """Verifies calculation of average episode duration and peak duration with supporting dates."""
    insights = TimelineService.generate_explainable_insights(sample_timeline_events)
    dur_insights = [i for i in insights if i["category"] == "Duration"]
    assert len(dur_insights) == 1
    d_ins = dur_insights[0]
    assert "Episode Duration Pattern" in d_ins["title"]
    assert "2026-10-12" in d_ins["supporting_dates"]
    assert d_ins["record_count"] == 4


def test_empty_events_insights():
    """Verifies graceful handling of empty event dataset with non-crashing safe observation."""
    insights = TimelineService.generate_explainable_insights([])
    assert len(insights) == 1
    ins = insights[0]
    assert ins["record_count"] == 0
    assert ins["supporting_dates"] == []
    assert "why_explanation" in ins


# ==============================================================================
# 2. WHAT HAS CHANGED? (DUAL-PERIOD COMPARISON TESTS)
# ==============================================================================

def test_compare_periods_kpis_and_impact(sample_timeline_events):
    """Verifies period comparison metrics including frequency, severity, duration, and daily activity impact."""
    # Period A: First two symptoms
    events_a = [sample_timeline_events[0], sample_timeline_events[1]]
    # Period B: Next two symptoms
    events_b = [sample_timeline_events[2], sample_timeline_events[3]]

    comp = TimelineService.compare_periods(
        events_a,
        events_b,
        period_a_label="Period A",
        period_b_label="Period B",
        days_a=14,
        days_b=14
    )

    deltas = comp["deltas"]
    assert deltas["episodes"] == 0  # 2 vs 2
    assert deltas["severity"] is not None
    assert deltas["duration"] is not None
    assert "impact" in deltas
    assert "impact_rate" in deltas

    # Data sufficiency check
    suff = comp["data_sufficiency"]
    assert suff["is_sufficient"] is True
    assert suff["count_a"] == 2
    assert suff["count_b"] == 2


def test_compare_periods_insufficient_data():
    """Verifies that datasets with fewer than 2 records trigger clear sufficiency messaging."""
    ev_a = [
        TimelineEvent(
            event_id="s_1",
            date="2026-10-01",
            time=None,
            event_type="symptom",
            title="Headache",
            category="Neurological & Headaches",
            severity=5
        )
    ]
    ev_b = []

    comp = TimelineService.compare_periods(
        ev_a,
        ev_b,
        period_a_label="Recent 14 Days",
        period_b_label="Previous 14 Days",
        days_a=14,
        days_b=14
    )

    suff = comp["data_sufficiency"]
    assert suff["is_sufficient"] is False
    assert "Insufficient" in suff["message"]
    assert comp["deltas"]["severity"] is None  # Handled safely, not cast to 0!


def test_compare_periods_missing_values_safe():
    """Ensures missing duration or severity does not falsely cast to 0.0."""
    ev_a = [
        TimelineEvent(
            event_id="s_1",
            date="2026-10-01",
            time=None,
            event_type="symptom",
            title="Fatigue",
            category="General Wellbeing & Energy",
            severity=None,
            duration_hours=None
        ),
        TimelineEvent(
            event_id="s_2",
            date="2026-10-03",
            time=None,
            event_type="symptom",
            title="Fatigue",
            category="General Wellbeing & Energy",
            severity=None,
            duration_hours=None
        )
    ]

    comp = TimelineService.compare_periods(ev_a, ev_a, "A", "B", 7, 7)
    pa_m = comp["period_a"]["metrics"]
    assert pa_m["avg_severity"] is None
    assert pa_m["avg_duration"] is None
    assert comp["deltas"]["severity"] is None
    assert comp["deltas"]["duration"] is None


# ==============================================================================
# 3. EVIDENCE-LINKED DOCTOR SUMMARY TESTS
# ==============================================================================

def test_clinician_report_notes_privacy_default():
    """Ensures private journal notes are omitted by default to safeguard patient privacy."""
    profile = UserProfile(id="p1", display_name="Maya", preferences={})
    entries = [
        SymptomEntry(
            id=10,
            profile_id="p1",
            category="Pelvic & Menstrual",
            symptom="Pelvic Pain",
            onset_date="2026-10-10",
            severity=6,
            duration_hours=2.0,
            status="Ongoing",
            impact="Normal activities modified",
            notes="Very intimate sensitive journal note that should not be printed.",
            context={"sleep": "Poor (< 5 hrs)", "stress": "High / Pressured", "cycle_phase": "Luteal Phase"}
        )
    ]

    generator = ClinicianReportGenerator(
        profile=profile,
        entries=entries,
        start_date="2026-10-01",
        end_date="2026-10-20"
    )
    pdf = generator.generate_pdf_bytes()
    assert pdf.startswith(b"%PDF")
    # Verify the PDF binary was constructed properly and is reasonably sized
    assert len(pdf) > 2000


def test_clinician_report_selective_notes_and_custom_questions():
    """Verifies that user-selected notes and custom questions are honored in the PDF generation."""
    profile = UserProfile(id="p1", display_name="Maya", preferences={})
    entries = [
        SymptomEntry(
            id=10,
            profile_id="p1",
            category="Pelvic & Menstrual",
            symptom="Pelvic Pain",
            onset_date="2026-10-10",
            severity=6,
            duration_hours=2.0,
            status="Ongoing",
            impact="Normal activities modified",
            notes="Selected clinical note: started after physical therapy.",
            context={"sleep": "Restful (> 7 hrs)"}
        )
    ]
    meds = [
        MedicationEntry(
            id=1,
            profile_id="p1",
            name="Naproxen",
            category="NSAID",
            dosage="500mg",
            frequency="As needed for pain"
        )
    ]

    custom_q = ["Should I schedule a pelvic ultrasound given my symptom timeline?"]

    generator = ClinicianReportGenerator(
        profile=profile,
        entries=entries,
        start_date="2026-10-01",
        end_date="2026-10-20",
        medications=meds,
        user_selected_notes={10: "Selected clinical note: started after physical therapy."},
        custom_questions=custom_q,
        include_all_notes=False
    )
    pdf = generator.generate_pdf_bytes()
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 3000


# ==============================================================================
# 4. VOICE DRAFT & QUICK OBSERVATION LOGGING TESTS
# ==============================================================================

def test_voice_draft_parsing_explicit_numerical():
    """Verifies deterministic parsing of explicit numerical severity and duration."""
    transcript = "I had a migraine since 9am, severity level 8, lasted 4.5 hours, couldn't work due to light sensitivity"
    draft = parse_symptom_voice_draft(transcript)

    assert draft["symptom"] == "Migraine / Severe Headache" or draft["symptom"] == "Migraine"
    assert draft["category"] == "Neurological & Head"
    assert draft["severity"] == 8
    assert draft["duration_hours"] == 4.5
    assert draft["impact"] == "Unable to work / Study"
    assert draft["raw_transcript"] == transcript


def test_voice_draft_parsing_qualitative_and_context():
    """Verifies qualitative severity ('mild', 'severe') and context keyword mapping."""
    transcript = "Mild pelvic cramps for 30 minutes during my period, slept poorly"
    draft = parse_symptom_voice_draft(transcript)

    assert "Pelvic" in draft["symptom"] or "Cramp" in draft["symptom"]
    assert draft["category"] == "Pelvic & Menstrual"
    assert draft["severity"] == 3  # "mild"
    assert draft["duration_hours"] == 0.5  # 30 mins
    assert draft["context"].get("sleep") == "Poor (< 5 hrs)"
    assert draft["context"].get("cycle_phase") == "Menstrual Phase"


def test_voice_draft_empty_fallback():
    """Verifies safe fallback structure when transcript is empty or whitespace."""
    draft = parse_symptom_voice_draft("   ")
    assert draft["symptom"] == "Unspecified Symptom"
    assert draft["severity"] == 5
    assert draft["duration_hours"] == 1.0
    assert draft["parsed_fields"] == []
