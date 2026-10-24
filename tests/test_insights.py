"""
HERPath AI - Automated Insights & Analytics Unit Tests
recHERsion 2026 | PS1: Women's Healthcare
"""

import pytest
from models import SymptomEntry
from insights_engine import InsightsEngine


def test_empty_entries_metrics():
    """Ensures empty entry list produces graceful zero metrics without crashing."""
    engine = InsightsEngine([])
    metrics = engine.calculate_summary_metrics()
    assert metrics["total_entries"] == 0
    assert metrics["avg_severity"] == 0.0
    assert metrics["max_severity"] == 0
    assert metrics["top_symptom"] == "None"
    assert metrics["avg_duration"] is None

    insights = engine.generate_explainable_insights()
    assert len(insights) == 1
    assert insights[0]["type"] == "insufficient_data"


def test_single_entry_metrics():
    """Ensures single entry calculates correctly and marks insufficient data for patterns."""
    entry = SymptomEntry(
        id=1,
        profile_id="p1",
        category="Neurological & Head",
        symptom="Migraine",
        onset_date="2026-10-20",
        severity=7,
        duration_hours=4.0
    )
    engine = InsightsEngine([entry])
    metrics = engine.calculate_summary_metrics()
    assert metrics["total_entries"] == 1
    assert metrics["avg_severity"] == 7.0
    assert metrics["max_severity"] == 7
    assert metrics["top_symptom"] == "Migraine"
    assert metrics["avg_duration"] == 4.0

    insights = engine.generate_explainable_insights()
    assert len(insights) == 1
    assert "not enough recorded information" in insights[0]["observation"].lower()


def test_multiple_entries_and_missing_duration():
    """
    Ensures metrics aggregate correctly and missing duration is NOT treated as zero.
    """
    entries = [
        SymptomEntry(id=1, profile_id="p1", category="Cat A", symptom="Migraine", onset_date="2026-10-18", severity=6, duration_hours=4.0),
        SymptomEntry(id=2, profile_id="p1", category="Cat A", symptom="Migraine", onset_date="2026-10-19", severity=8, duration_hours=None), # Duration missing
        SymptomEntry(id=3, profile_id="p1", category="Cat B", symptom="Fatigue", onset_date="2026-10-20", severity=4, duration_hours=6.0),
        SymptomEntry(id=4, profile_id="p1", category="Cat A", symptom="Migraine", onset_date="2026-10-21", severity=6, duration_hours=8.0),
    ]
    engine = InsightsEngine(entries)
    metrics = engine.calculate_summary_metrics()

    assert metrics["total_entries"] == 4
    # Avg severity: (6 + 8 + 4 + 6) / 4 = 24 / 4 = 6.0
    assert metrics["avg_severity"] == 6.0
    assert metrics["max_severity"] == 8
    assert metrics["top_symptom"] == "Migraine"
    assert metrics["top_symptom_count"] == 3

    # Avg duration across entries with valid duration: (4 + 6 + 8) / 3 = 18 / 3 = 6.0
    # Must NOT divide by 4 (i.e. not treating None as 0)
    assert metrics["avg_duration"] == 6.0


def test_explainable_insights_non_diagnostic():
    """
    Ensures insights generated do not make unauthorized diagnostic claims.
    """
    entries = [
        SymptomEntry(id=1, profile_id="p1", category="Pelvic", symptom="Pelvic Cramping", onset_date="2026-10-10", severity=5, context={"sleep": "Disrupted / Fragmented"}),
        SymptomEntry(id=2, profile_id="p1", category="Pelvic", symptom="Pelvic Cramping", onset_date="2026-10-12", severity=7, context={"sleep": "Disrupted / Fragmented"}),
        SymptomEntry(id=3, profile_id="p1", category="Pelvic", symptom="Pelvic Cramping", onset_date="2026-10-14", severity=8, context={"sleep": "Disrupted / Fragmented"}),
        SymptomEntry(id=4, profile_id="p1", category="Pelvic", symptom="Pelvic Cramping", onset_date="2026-10-16", severity=8, context={"sleep": "Restful (7-9 hrs)"}),
    ]
    engine = InsightsEngine(entries)
    insights = engine.generate_explainable_insights()

    assert len(insights) >= 2
    for ins in insights:
        text = (ins["title"] + " " + ins["observation"] + " " + ins.get("context_note", "")).lower()
        # Verify no diagnosis is fabricated
        assert "you have pcos" not in text
        assert "you have endometriosis" not in text
        assert "cancer" not in text
        assert "diagnosed with" not in text


def test_calendar_heatmap_generation():
    """Ensures monthly calendar heatmap generates valid Plotly figure with multi-day data."""
    # Test empty returns None
    empty_engine = InsightsEngine([])
    assert empty_engine.plot_calendar_symptom_heatmap() is None

    # Test populated entries
    entries = [
        SymptomEntry(id=1, profile_id="p1", category="Cat A", symptom="Migraine", onset_date="2026-10-18", severity=7),
        SymptomEntry(id=2, profile_id="p1", category="Cat B", symptom="Fatigue", onset_date="2026-10-18", severity=5),
        SymptomEntry(id=3, profile_id="p1", category="Cat A", symptom="Migraine", onset_date="2026-10-19", severity=8),
    ]
    engine = InsightsEngine(entries)
    fig = engine.plot_calendar_symptom_heatmap()
    assert fig is not None
    assert len(fig.data) > 0
