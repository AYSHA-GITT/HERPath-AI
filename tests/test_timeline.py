"""
HERPath AI - Timeline Intelligence Comprehensive Test Suite
recHERsion 2026 | PS1: Women's Healthcare

Tests:
1. Chronological sorting of events.
2. Date-range filtering.
3. Symptom and category filtering.
4. Severity range filtering.
5. Event types filtering (Symptoms, Medications, Context).
6. Episode counts and average severity calculations.
7. Missing severity and duration handling (not cast to zero).
8. Period comparison metrics and unequal period lengths.
9. Empty periods and insufficient data handling.
10. Contextual co-occurrence calculations and threshold checks.
11. Profile isolation (strict multi-user privacy).
12. Medication events grounded strictly in real records.
13. Explainable insight safety wording (no causation, no diagnoses, explicit disclaimers).
14. Plotly charts rendering with empty and populated datasets.
"""

import pytest
import os
import gc
import tempfile
from datetime import date, timedelta
import plotly.graph_objects as go

from database import (
    init_db,
    create_profile,
    add_symptom,
    add_medication,
    get_symptoms,
    get_medications
)
from models import SymptomEntry, MedicationEntry
from timeline_service import TimelineService, TimelineEvent


@pytest.fixture
def timeline_db():
    """Provides a fresh isolated SQLite database with test fixtures."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)

    # Create two test profiles to verify multi-profile isolation
    create_profile("test_user_a", "Alice Test", db_path=path)
    create_profile("test_user_b", "Bobbi Test", db_path=path)

    yield path

    gc.collect()
    try:
        if os.path.exists(path):
            os.remove(path)
    except PermissionError:
        pass


def test_chronological_sorting(timeline_db):
    """Verifies that symptom and medication events are sorted in ascending chronological order."""
    # Add events out of order
    add_symptom(SymptomEntry(
        id=None,
        profile_id="test_user_a",
        category="Neurological & Head",
        symptom="Migraine with Aura",
        onset_date="2026-10-15",
        onset_time="14:00",
        severity=8,
        duration_hours=6.0,
        status="Resolved"
    ), db_path=timeline_db)

    add_medication(MedicationEntry(
        id=None,
        profile_id="test_user_a",
        name="Sumatriptan",
        category="Prescription",
        dosage="50 mg",
        frequency="As needed",
        started_date="2026-10-10",
        notes="Rescue med"
    ), db_path=timeline_db)

    add_symptom(SymptomEntry(
        id=None,
        profile_id="test_user_a",
        category="Pelvic & Menstrual",
        symptom="Pelvic Cramping",
        onset_date="2026-10-05",
        onset_time="09:00",
        severity=6,
        duration_hours=4.0,
        status="Resolved"
    ), db_path=timeline_db)

    add_symptom(SymptomEntry(
        id=None,
        profile_id="test_user_a",
        category="Systemic & Energy",
        symptom="Fatigue",
        onset_date="2026-10-20",
        onset_time="10:00",
        severity=4,
        duration_hours=8.0,
        status="Ongoing"
    ), db_path=timeline_db)

    service = TimelineService("test_user_a", db_path=timeline_db)
    events = service.fetch_all_events()

    assert len(events) == 4
    dates = [e.date for e in events]
    assert dates == ["2026-10-05", "2026-10-10", "2026-10-15", "2026-10-20"]
    assert events[1].event_type == "medication"
    assert events[1].title == "Started Sumatriptan"
    assert events[0].event_type == "symptom"
    assert events[0].title == "Pelvic Cramping"


def test_date_range_filtering(timeline_db):
    """Tests that date filtering includes events within bounds and excludes out-of-range events."""
    for d, s in [("2026-10-01", 3), ("2026-10-10", 5), ("2026-10-20", 7), ("2026-10-24", 9)]:
        add_symptom(SymptomEntry(
            id=None,
            profile_id="test_user_a",
            category="Neurological & Head",
            symptom="Headache",
            onset_date=d,
            severity=s,
            status="Resolved"
        ), db_path=timeline_db)

    service = TimelineService("test_user_a", db_path=timeline_db)
    all_events = service.fetch_all_events()

    # Filter to 2026-10-05 to 2026-10-22
    filtered = TimelineService.filter_events(
        all_events,
        start_date="2026-10-05",
        end_date="2026-10-22"
    )

    assert len(filtered) == 2
    assert [e.date for e in filtered] == ["2026-10-10", "2026-10-20"]


def test_category_and_symptom_filtering(timeline_db):
    """Tests filtering by category and specific symptom title."""
    add_symptom(SymptomEntry(
        id=None, profile_id="test_user_a", category="Neurological & Head", symptom="Migraine", onset_date="2026-10-10", severity=7
    ), db_path=timeline_db)
    add_symptom(SymptomEntry(
        id=None, profile_id="test_user_a", category="Neurological & Head", symptom="Tension Headache", onset_date="2026-10-11", severity=4
    ), db_path=timeline_db)
    add_symptom(SymptomEntry(
        id=None, profile_id="test_user_a", category="Pelvic & Menstrual", symptom="Pelvic Pain", onset_date="2026-10-12", severity=6
    ), db_path=timeline_db)

    service = TimelineService("test_user_a", db_path=timeline_db)
    all_events = service.fetch_all_events()

    # Category filter
    cat_filtered = TimelineService.filter_events(all_events, categories=["Neurological & Head"])
    assert len(cat_filtered) == 2

    # Specific symptom filter
    sym_filtered = TimelineService.filter_events(all_events, symptoms=["Migraine"])
    assert len(sym_filtered) == 1
    assert sym_filtered[0].title == "Migraine"


def test_severity_range_filtering(timeline_db):
    """Tests filtering by minimum and maximum severity rating."""
    add_symptom(SymptomEntry(id=None, profile_id="test_user_a", category="General", symptom="Mild Aches", onset_date="2026-10-10", severity=2), db_path=timeline_db)
    add_symptom(SymptomEntry(id=None, profile_id="test_user_a", category="General", symptom="Moderate Pain", onset_date="2026-10-11", severity=5), db_path=timeline_db)
    add_symptom(SymptomEntry(id=None, profile_id="test_user_a", category="General", symptom="Severe Flare", onset_date="2026-10-12", severity=9), db_path=timeline_db)

    service = TimelineService("test_user_a", db_path=timeline_db)
    all_events = service.fetch_all_events()

    # Severity between 4 and 8
    mod_events = TimelineService.filter_events(all_events, min_severity=4, max_severity=8)
    assert len(mod_events) == 1
    assert mod_events[0].severity == 5


def test_event_types_filtering(timeline_db):
    """Tests filtering by event types (Symptoms, Medications, Context)."""
    add_symptom(SymptomEntry(
        id=None, profile_id="test_user_a", category="Neuro", symptom="Migraine", onset_date="2026-10-10", severity=7,
        impact="Moderate", context={"sleep": "Disrupted / Fragmented", "stress": "High / Pressured"}
    ), db_path=timeline_db)
    add_symptom(SymptomEntry(
        id=None, profile_id="test_user_a", category="Neuro", symptom="Mild Head Tension", onset_date="2026-10-11", severity=3,
        impact="None", context={"sleep": "Restful (7-9 hrs)", "stress": "Low / Calm"}
    ), db_path=timeline_db)
    add_medication(MedicationEntry(
        id=None, profile_id="test_user_a", name="Magnesium", category="OTC / Supplement", started_date="2026-10-08"
    ), db_path=timeline_db)

    service = TimelineService("test_user_a", db_path=timeline_db)
    all_events = service.fetch_all_events()

    # Medications only
    meds_only = TimelineService.filter_events(all_events, event_types=["Medications"])
    assert len(meds_only) == 1
    assert meds_only[0].event_type == "medication"

    # Symptoms only
    sym_only = TimelineService.filter_events(all_events, event_types=["Symptoms"])
    assert len(sym_only) == 2

    # Sleep context filter
    sleep_only = TimelineService.filter_events(all_events, event_types=["Sleep Context"])
    assert len(sleep_only) == 2  # Both have sleep context recorded


def test_summary_metrics_calculation(timeline_db):
    """Verifies that summary calculations accurately compute averages, peaks, and counts."""
    add_symptom(SymptomEntry(id=None, profile_id="test_user_a", category="General", symptom="Pain A", onset_date="2026-10-10", severity=6, duration_hours=4.0, impact="Mild"), db_path=timeline_db)
    add_symptom(SymptomEntry(id=None, profile_id="test_user_a", category="General", symptom="Pain B", onset_date="2026-10-11", severity=8, duration_hours=6.0, impact="Severe"), db_path=timeline_db)
    add_medication(MedicationEntry(id=None, profile_id="test_user_a", name="Treatment X", category="Prescription", started_date="2026-10-10"), db_path=timeline_db)

    service = TimelineService("test_user_a", db_path=timeline_db)
    events = service.fetch_all_events()

    metrics = TimelineService.calculate_summary_metrics(events)
    assert metrics["total_events"] == 3
    assert metrics["symptom_episodes"] == 2
    assert metrics["medication_changes"] == 1
    assert metrics["avg_severity"] == 7.0
    assert metrics["max_severity"] == 8
    assert metrics["avg_duration"] == 5.0
    assert metrics["impact_count"] == 2


def test_missing_severity_and_duration_handling():
    """Ensures missing severity and duration values are omitted, NOT interpreted as zero."""
    events = [
        TimelineEvent(event_id="s1", event_type="symptom", date="2026-10-01", time=None, title="Symptom 1", category="Gen", severity=8, duration_hours=4.0),
        TimelineEvent(event_id="s2", event_type="symptom", date="2026-10-02", time=None, title="Symptom 2", category="Gen", severity=None, duration_hours=None),
        TimelineEvent(event_id="s3", event_type="symptom", date="2026-10-03", time=None, title="Symptom 3", category="Gen", severity=6, duration_hours=2.0)
    ]

    metrics = TimelineService.calculate_summary_metrics(events)
    # Average of 8 and 6 is 7.0. If None was treated as 0, average would be (8+0+6)/3 = 4.67!
    assert metrics["avg_severity"] == 7.0
    # Average duration of 4.0 and 2.0 is 3.0.
    assert metrics["avg_duration"] == 3.0


def test_period_comparison_calculations():
    """Tests dual-period comparison including deltas, raw counts, and observation rates per day."""
    period_a = [
        TimelineEvent(event_id="a1", event_type="symptom", date="2026-10-15", time=None, title="Migraine", category="Neuro", severity=7, duration_hours=5.0),
        TimelineEvent(event_id="a2", event_type="symptom", date="2026-10-16", time=None, title="Migraine", category="Neuro", severity=9, duration_hours=7.0),
        TimelineEvent(event_id="a3", event_type="symptom", date="2026-10-18", time=None, title="Pelvic Pain", category="Pelvic", severity=6, duration_hours=4.0)
    ]
    period_b = [
        TimelineEvent(event_id="b1", event_type="symptom", date="2026-09-10", time=None, title="Migraine", category="Neuro", severity=5, duration_hours=3.0)
    ]

    # Compare 14 days (A) vs 30 days (B) - unequal lengths
    comp = TimelineService.compare_periods(
        period_a,
        period_b,
        period_a_label="October Recent",
        period_b_label="September Prior",
        days_a=14,
        days_b=30
    )

    deltas = comp["deltas"]
    assert deltas["episodes"] == 2  # 3 in A minus 1 in B
    # Period A avg severity: (7+9+6)/3 = 7.33 (7.3)
    # Period B avg severity: 5.0
    # Delta: 7.3 - 5.0 = 2.3
    assert deltas["severity"] == pytest.approx(2.3, abs=0.1)

    # Observation rate per day
    assert comp["period_a"]["daily_rate"] == round(3 / 14, 2)
    assert comp["period_b"]["daily_rate"] == round(1 / 30, 2)

    # Breakdown for Migraine
    breakdown = {b["symptom"]: b for b in comp["symptom_breakdown"]}
    assert "Migraine" in breakdown
    assert breakdown["Migraine"]["episodes_a"] == 2
    assert breakdown["Migraine"]["episodes_b"] == 1
    assert breakdown["Migraine"]["avg_severity_a"] == 8.0
    assert breakdown["Migraine"]["avg_severity_b"] == 5.0


def test_period_comparison_empty_and_insufficient():
    """Verifies that comparing against an empty period does not raise zero-division errors."""
    period_a = [
        TimelineEvent(event_id="a1", event_type="symptom", date="2026-10-15", time=None, title="Headache", category="Neuro", severity=6)
    ]
    period_b = []

    comp = TimelineService.compare_periods(period_a, period_b, days_a=30, days_b=30)
    assert comp["period_a"]["metrics"]["symptom_episodes"] == 1
    assert comp["period_b"]["metrics"]["symptom_episodes"] == 0
    assert comp["deltas"]["episodes"] == 1
    assert comp["deltas"]["severity"] is None  # Cannot subtract None


def test_contextual_cooccurrence_and_sample_threshold():
    """Verifies that contextual sleep co-occurrence produces proper insights and detects small sample size."""
    # Scenario 1: Only 2 entries (below n >= 3 threshold)
    few_events = [
        TimelineEvent(event_id="1", event_type="symptom", date="2026-10-01", time=None, title="Fatigue", category="Sys", severity=5, context={"sleep": "Poor (< 5 hrs)"}),
        TimelineEvent(event_id="2", event_type="symptom", date="2026-10-02", time=None, title="Fatigue", category="Sys", severity=6, context={"sleep": "Poor (< 5 hrs)"})
    ]
    insights_few = TimelineService.generate_explainable_insights(few_events)
    sleep_ins = next((i for i in insights_few if "Sleep" in i["title"]), None)
    assert sleep_ins is not None
    assert "insufficient" in sleep_ins["statement"].lower()

    # Scenario 2: 4 entries (n >= 3 threshold met)
    adequate_events = few_events + [
        TimelineEvent(event_id="3", event_type="symptom", date="2026-10-03", time=None, title="Fatigue", category="Sys", severity=7, context={"sleep": "Disrupted / Fragmented"}),
        TimelineEvent(event_id="4", event_type="symptom", date="2026-10-04", time=None, title="Fatigue", category="Sys", severity=3, context={"sleep": "Restful (7-9 hrs)"})
    ]
    insights_ad = TimelineService.generate_explainable_insights(adequate_events)
    sleep_ins_ad = next((i for i in insights_ad if "Sleep" in i["title"]), None)
    assert sleep_ins_ad is not None
    assert "coincided with" in sleep_ins_ad["statement"]
    assert sleep_ins_ad["record_count"] == 4


def test_profile_isolation(timeline_db):
    """Verifies that events belonging to profile A are never returned when querying profile B."""
    add_symptom(SymptomEntry(
        id=None, profile_id="test_user_a", category="Neuro", symptom="Migraine", onset_date="2026-10-10", severity=8
    ), db_path=timeline_db)
    add_symptom(SymptomEntry(
        id=None, profile_id="test_user_b", category="Pelvic", symptom="Pelvic Pain", onset_date="2026-10-11", severity=5
    ), db_path=timeline_db)

    service_a = TimelineService("test_user_a", db_path=timeline_db)
    events_a = service_a.fetch_all_events()

    service_b = TimelineService("test_user_b", db_path=timeline_db)
    events_b = service_b.fetch_all_events()

    assert len(events_a) == 1
    assert events_a[0].title == "Migraine"

    assert len(events_b) == 1
    assert events_b[0].title == "Pelvic Pain"


def test_medication_events_only_when_recorded(timeline_db):
    """Verifies medication events only appear when backed by real database records."""
    service = TimelineService("test_user_a", db_path=timeline_db)
    assert len(service.fetch_all_events()) == 0

    add_medication(MedicationEntry(
        id=None,
        profile_id="test_user_a",
        name="Metformin",
        category="Prescription",
        dosage="500 mg",
        frequency="Twice daily",
        started_date="2026-10-01"
    ), db_path=timeline_db)

    events = service.fetch_all_events()
    assert len(events) == 1
    assert events[0].event_type == "medication"
    assert events[0].title == "Started Metformin"
    assert events[0].dosage == "500 mg"


def test_explainable_insights_safety_wording():
    """Verifies that generated insights adhere to medical safety: no causation claims and clear limitations."""
    events = [
        TimelineEvent(event_id="1", event_type="symptom", date="2026-10-01", time=None, title="Migraine", category="Neuro", severity=7, context={"sleep": "Disrupted / Fragmented", "stress": "High / Pressured"}),
        TimelineEvent(event_id="2", event_type="symptom", date="2026-10-03", time=None, title="Migraine", category="Neuro", severity=8, context={"sleep": "Disrupted / Fragmented", "stress": "High / Pressured"}),
        TimelineEvent(event_id="3", event_type="symptom", date="2026-10-05", time=None, title="Migraine", category="Neuro", severity=6, context={"sleep": "Disrupted / Fragmented", "stress": "High / Pressured"})
    ]

    insights = TimelineService.generate_explainable_insights(events)
    for ins in insights:
        statement = ins["statement"].lower()
        # Ensure no causal claims
        assert "caused" not in statement
        assert "leads to" not in statement
        # Ensure every insight has limitation note, exact evidence, and formula calculation
        assert "limitation" in ins and len(ins["limitation"]) > 10
        assert "exact_evidence" in ins and len(ins["exact_evidence"]) > 5
        assert "calculation_note" in ins and len(ins["calculation_note"]) > 3


def test_plotly_charts_empty_and_populated():
    """Verifies that Plotly chart generators produce valid go.Figure objects on both empty and populated data."""
    # 1. Empty tests
    fig_empty_sev = TimelineService.create_severity_timeline_chart([])
    assert isinstance(fig_empty_sev, go.Figure)

    fig_empty_swim = TimelineService.create_unified_event_timeline_chart([])
    assert isinstance(fig_empty_swim, go.Figure)

    # 2. Populated tests
    events = [
        TimelineEvent(event_id="1", event_type="symptom", date="2026-10-01", time="09:00", title="Migraine", category="Neuro", severity=7, impact="Severe"),
        TimelineEvent(event_id="2", event_type="medication", date="2026-10-02", time=None, title="Started Sumatriptan", category="Prescription", dosage="50 mg")
    ]

    fig_sev = TimelineService.create_severity_timeline_chart(events)
    assert isinstance(fig_sev, go.Figure)
    assert len(fig_sev.data) >= 1

    fig_swim = TimelineService.create_unified_event_timeline_chart(events)
    assert isinstance(fig_swim, go.Figure)
    assert len(fig_swim.data) >= 2  # Symptom trace + medication trace + impact trace

    # Context chart
    fig_ctx = TimelineService.create_contextual_cooccurrence_chart(events)
    assert isinstance(fig_ctx, go.Figure)


def test_timeline_intelligence_streamlit_ui():
    """Verifies that Timeline Intelligence screen renders seamlessly in Streamlit AppTest without exceptions."""
    from pathlib import Path
    from streamlit.testing.v1 import AppTest

    app_file = str(Path(__file__).resolve().parent.parent / "app.py")
    at = AppTest.from_file(app_file, default_timeout=30)
    at.run()

    # Log in
    for ti in at.text_input:
        if ti.key and "pin" in ti.key.lower():
            ti.set_value("1234")
            break
    for b in at.button:
        if "LOGIN" in b.label:
            b.click().run()
            break

    # Navigate to Timeline Intelligence
    at.session_state["navigation"] = "Timeline Intelligence"
    at.run()

    assert not at.exception, f"Exception in Timeline Intelligence UI: {at.exception}"

    combined_text = " ".join([str(m.value) for m in at.markdown])
    assert "HERPath Timeline Intelligence" in combined_text
    assert "Timeline Summary Metrics" in combined_text
    assert "Interactive Timeline Visualizations" in combined_text
    assert "Compare Symptoms Across Selected Periods" in combined_text
    assert "Chronological Health Event Feed" in combined_text

