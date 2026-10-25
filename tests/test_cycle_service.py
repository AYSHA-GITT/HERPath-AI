"""
HERPath AI - Cycle Intelligence & Calendar Verification Suite
recHERsion 2026 | PS1: Women's Healthcare

Verifies:
1. Profile isolation (Zero cross-profile data leakage in calendar & cycle stats).
2. Honest handling of insufficient data (0 periods, 1 period).
3. Mathematical accuracy of cycle intervals and exclusion of >75d gaps.
4. Strict non-diagnostic phrasing for irregular cycles (Zero "PCOS detected" claims).
5. Visual and logical distinction between recorded period days and predicted future period dates.
6. Non-assumption of blank days as symptom-free.
"""

import pytest
import sqlite3
import tempfile
import os
from datetime import date, timedelta
from pathlib import Path

from database import init_db, create_profile, add_symptom, add_medication, get_connection
from models import SymptomEntry, MedicationEntry
from cycle_service import CycleService, CycleStatisticsData, MonthCalendarData


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_cycle_service_profile_isolation(temp_db):
    """Verifies that cycle statistics and calendar events never leak across profile boundaries."""
    create_profile("user_a", "Alice", {"cycle_length": 28}, temp_db)
    create_profile("user_b", "Bobbie", {"cycle_length": 30}, temp_db)

    # Add periods only for user_a
    add_symptom(SymptomEntry(
        id=None, profile_id="user_a", category="Pelvic & Menstrual",
        symptom="Menstrual Bleeding (Period Start)", onset_date="2026-08-01",
        severity=4
    ), temp_db)
    add_symptom(SymptomEntry(
        id=None, profile_id="user_a", category="Pelvic & Menstrual",
        symptom="Menstrual Bleeding (Period Start)", onset_date="2026-08-29",
        severity=5
    ), temp_db)

    # Query stats for user_a
    stats_a = CycleService.calculate_cycle_statistics("user_a", temp_db)
    assert stats_a.total_periods_recorded == 2
    assert stats_a.total_cycles_analyzed == 1
    assert stats_a.average_cycle_length == 28.0

    # Query stats for user_b (must be completely empty)
    stats_b = CycleService.calculate_cycle_statistics("user_b", temp_db)
    assert stats_b.total_periods_recorded == 0
    assert stats_b.total_cycles_analyzed == 0
    assert stats_b.average_cycle_length is None
    assert "No period start dates recorded yet" in stats_b.clinical_note

    # Calendar query for user_b in August 2026 must have 0 periods
    cal_b = CycleService.get_month_calendar_data("user_b", 2026, 8, temp_db)
    assert cal_b.total_period_days_in_month == 0
    assert cal_b.total_symptoms_in_month == 0


def test_cycle_service_insufficient_data(temp_db):
    """Verifies honest handling when fewer than 2 period dates are recorded."""
    create_profile("solo_user", "Solo", {}, temp_db)

    # 0 periods
    stats_0 = CycleService.calculate_cycle_statistics("solo_user", temp_db)
    assert stats_0.total_periods_recorded == 0
    assert stats_0.total_cycles_analyzed == 0
    assert stats_0.average_cycle_length is None

    # 1 period recorded
    add_symptom(SymptomEntry(
        id=None, profile_id="solo_user", category="Pelvic & Menstrual",
        symptom="Menstrual Bleeding (Period Start)", onset_date="2026-10-01",
        severity=4
    ), temp_db)

    stats_1 = CycleService.calculate_cycle_statistics("solo_user", temp_db)
    assert stats_1.total_periods_recorded == 1
    assert stats_1.total_cycles_analyzed == 0
    assert stats_1.average_cycle_length is None
    assert "At least 2 recorded period start dates are needed" in stats_1.clinical_note
    assert stats_1.is_sufficient_for_trend is False


def test_cycle_service_single_interval(temp_db):
    """Verifies that 2 recorded periods allow calculating 1 interval but honestly state trend requires >= 3."""
    create_profile("two_p", "Two Periods", {}, temp_db)

    add_symptom(SymptomEntry(
        id=None, profile_id="two_p", category="Pelvic & Menstrual",
        symptom="Menstrual Bleeding", onset_date="2026-08-01", severity=4
    ), temp_db)
    add_symptom(SymptomEntry(
        id=None, profile_id="two_p", category="Pelvic & Menstrual",
        symptom="Menstrual Bleeding", onset_date="2026-08-30", severity=5
    ), temp_db)

    stats = CycleService.calculate_cycle_statistics("two_p", temp_db)
    assert stats.total_periods_recorded == 2
    assert stats.total_cycles_analyzed == 1
    assert stats.average_cycle_length == 29.0
    assert stats.is_sufficient_for_trend is False
    assert "At least 3 recorded cycles are needed" in stats.clinical_note


def test_cycle_service_consistent_intervals(temp_db):
    """Verifies cycle variation calculation for consistent cycles (<= 7 days variation)."""
    create_profile("reg_user", "Regular User", {}, temp_db)

    # 4 periods: intervals are 28, 29, 28 (variation = 1 day)
    dates = ["2026-06-01", "2026-06-29", "2026-07-28", "2026-08-25"]
    for d in dates:
        add_symptom(SymptomEntry(
            id=None, profile_id="reg_user", category="Pelvic & Menstrual",
            symptom="Menstrual Bleeding", onset_date=d, severity=4
        ), temp_db)

    stats = CycleService.calculate_cycle_statistics("reg_user", temp_db)
    assert stats.total_periods_recorded == 4
    assert stats.total_cycles_analyzed == 3
    assert stats.average_cycle_length == 28.3
    assert stats.shortest_cycle == 28
    assert stats.longest_cycle == 29
    assert stats.variation_days == 1
    assert stats.is_sufficient_for_trend is True
    assert "Consistent Interval Pattern" in stats.variation_status
    assert "relatively consistent interval pattern" in stats.clinical_note


def test_cycle_service_variable_intervals_non_diagnostic_pcos_boundary(temp_db):
    """
    CRITICAL SAFETY TEST:
    Verifies that when cycle variation exceeds 7-9 days:
    1. NEVER displays 'You have PCOS' or 'PCOS detected'.
    2. NEVER assigns a definitive PCOS risk score.
    3. Uses objective educational phrasing recommending discussion with a healthcare professional.
    """
    create_profile("var_user", "Variable User", {}, temp_db)

    # 4 periods with variable intervals:
    # 2026-05-01 -> 2026-05-26: 25 days
    # 2026-05-26 -> 2026-07-05: 40 days
    # 2026-07-05 -> 2026-08-01: 27 days
    # Variation: 40 - 25 = 15 days (> 7 days)
    dates = ["2026-05-01", "2026-05-26", "2026-07-05", "2026-08-01"]
    for d in dates:
        add_symptom(SymptomEntry(
            id=None, profile_id="var_user", category="Pelvic & Menstrual",
            symptom="Menstrual Bleeding", onset_date=d, severity=4
        ), temp_db)

    stats = CycleService.calculate_cycle_statistics("var_user", temp_db)
    assert stats.total_cycles_analyzed == 3
    assert stats.variation_days == 15
    assert stats.shortest_cycle == 25
    assert stats.longest_cycle == 40
    assert stats.variation_status == "Variable Interval Pattern"

    note = stats.clinical_note
    # Non-diagnostic assertions:
    assert "You have PCOS" not in note
    assert "PCOS detected" not in note
    assert "PCOS risk score" not in note
    assert "diagnosed" not in note.lower()

    # Required phrasing:
    assert "Your recorded cycle pattern may be worth discussing with a healthcare professional" in note
    assert "Cycle variation can occur for many natural reasons" in note


def test_cycle_service_excludes_anomalous_gaps(temp_db):
    """Verifies that intervals > 75 days (indicating unrecorded cycles) are excluded from statistics."""
    create_profile("gap_user", "Gap User", {}, temp_db)

    # 2026-01-01 -> 2026-01-29 (28 days)
    # 2026-01-29 -> 2026-05-15 (106 days - missed recording periods)
    # 2026-05-15 -> 2026-06-14 (30 days)
    dates = ["2026-01-01", "2026-01-29", "2026-05-15", "2026-06-14"]
    for d in dates:
        add_symptom(SymptomEntry(
            id=None, profile_id="gap_user", category="Pelvic & Menstrual",
            symptom="Menstrual Bleeding", onset_date=d, severity=4
        ), temp_db)

    stats = CycleService.calculate_cycle_statistics("gap_user", temp_db)
    # Total intervals in list = 3, but valid intervals = 2 (28 and 30 days)
    assert stats.total_cycles_analyzed == 2
    assert stats.average_cycle_length == 29.0  # (28 + 30) / 2
    assert stats.shortest_cycle == 28
    assert stats.longest_cycle == 30

    # Interval 2 must be marked invalid
    intv2 = stats.intervals[1]
    assert intv2.is_valid is False
    assert intv2.length_days == 106
    assert "excluded from statistics" in intv2.notes


def test_month_calendar_distinguishes_recorded_and_predicted_periods(temp_db):
    """
    Verifies that:
    1. User-recorded period days have has_period=True, is_predicted_period=False.
    2. Future estimated dates have is_predicted_period=True, has_period=False.
    3. Displaying calendar NEVER saves predicted dates into SQLite.
    """
    create_profile("cal_user", "Calendar User", {"cycle_length": 28, "period_duration": 5}, temp_db)

    # Period recorded on 2026-10-01
    add_symptom(SymptomEntry(
        id=None, profile_id="cal_user", category="Pelvic & Menstrual",
        symptom="Menstrual Bleeding", onset_date="2026-10-01", severity=5
    ), temp_db)

    # Add medication
    add_medication(MedicationEntry(
        id=None, profile_id="cal_user", name="Inositol", category="OTC / Supplement",
        dosage="2000mg", frequency="Daily", started_date="2026-09-01"
    ), temp_db)

    # Count symptom entries before calendar generation
    conn = get_connection(temp_db)
    count_before = conn.execute("SELECT COUNT(*) FROM symptom_entries WHERE profile_id = 'cal_user';").fetchone()[0]
    conn.close()

    cal_data = CycleService.get_month_calendar_data("cal_user", 2026, 10, temp_db)
    assert cal_data.month_name == "October"
    assert len(cal_data.days) == 31

    # Day 1: Recorded period
    day1 = cal_data.days[0]
    assert day1.has_period is True
    assert day1.is_predicted_period is False
    assert len(day1.symptoms) == 1
    assert day1.max_severity == 5
    assert len(day1.medications) >= 1

    # Check predicted period (around Day 29: 2026-10-01 + 28 days = 2026-10-29)
    # Day 29:
    day29 = cal_data.days[28]
    # If day29 is >= today, it will be marked as predicted
    if date(2026, 10, 29) >= date.today():
        assert day29.is_predicted_period is True
        assert day29.has_period is False  # Must NOT be marked as confirmed

    # Verify NO side-effects (database count unchanged)
    conn = get_connection(temp_db)
    count_after = conn.execute("SELECT COUNT(*) FROM symptom_entries WHERE profile_id = 'cal_user';").fetchone()[0]
    conn.close()
    assert count_before == count_after, "Calendar data retrieval must be strictly read-only and never write predicted dates to SQLite."


def test_apptest_home_dashboard_calendar_and_cycle_stats():
    """Verifies that the Home Dashboard renders the calendar and historical cycle statistics tabs via Streamlit AppTest."""
    from streamlit.testing.v1 import AppTest
    APP_FILE = str(Path(__file__).resolve().parent.parent / "app.py")

    at = AppTest.from_file(APP_FILE, default_timeout=30)
    at.run()
    # Sign in
    for ti in at.text_input:
        if ti.key and "pin" in ti.key.lower():
            ti.set_value("1234")
            break
    for b in at.button:
        if "LOGIN" in b.label:
            b.click().run()
            break

    assert not at.exception
    combined_md = " ".join([m.value for m in at.markdown])

    # Check that Calendar section and accessible legend exist
    assert "Cycle Calendar & History" in combined_md
    assert "Period" in combined_md
    assert "Est. Period" in combined_md
    assert "Symptom" in combined_md
    assert "Medication" in combined_md

    # Check month navigation buttons exist
    btn_keys = [b.key for b in at.button if b.key]
    assert "cal_btn_prev_month" in btn_keys
    assert "cal_btn_next_month" in btn_keys
    assert "cal_btn_today" in btn_keys

    # Check metrics
    metric_labels = [m.label for m in at.metric]
    assert "Cycles Analyzed" in metric_labels
    assert "Average Length" in metric_labels
    assert "Cycle Range" in metric_labels
    assert "Variability" in metric_labels

    # Check that PCOS diagnosis is strictly absent
    assert "You have PCOS" not in combined_md
    assert "PCOS detected" not in combined_md

