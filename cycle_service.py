"""
HERPath AI - Cycle Intelligence & Calendar Service
recHERsion 2026 | PS1: Women's Healthcare

Provides:
1. Deterministic historical cycle statistics and variation analysis with strict non-diagnostic phrasing.
2. Full month calendar data synthesis with heatmap dots, symptom severity, active medications, and clear distinction between recorded and predicted period dates.
3. 100% on-device SQLite queries strictly isolated by profile_id.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from datetime import date, datetime, timedelta
import calendar
import numpy as np

from database import get_connection
from models import SymptomEntry, MedicationEntry


@dataclass
class CycleInterval:
    cycle_index: int
    start_date: str
    end_date: str
    length_days: int
    is_valid: bool = True
    notes: str = ""


@dataclass
class CycleStatisticsData:
    profile_id: str
    total_periods_recorded: int
    total_cycles_analyzed: int
    intervals: List[CycleInterval] = field(default_factory=list)
    average_cycle_length: Optional[float] = None
    shortest_cycle: Optional[int] = None
    longest_cycle: Optional[int] = None
    variation_days: Optional[int] = None
    cycle_std_dev: Optional[float] = None
    variation_status: str = "Insufficient Data"
    clinical_note: str = ""
    is_sufficient_for_trend: bool = False


@dataclass
class CalendarDayData:
    date_str: str
    day_num: int
    is_current_month: bool
    is_today: bool
    has_period: bool = False
    is_predicted_period: bool = False
    symptoms: List[Dict[str, Any]] = field(default_factory=list)
    symptom_count: int = 0
    max_severity: Optional[int] = None
    medications: List[str] = field(default_factory=list)
    lifestyle_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MonthCalendarData:
    profile_id: str
    year: int
    month: int
    month_name: str
    days: List[CalendarDayData] = field(default_factory=list)
    total_symptoms_in_month: int = 0
    total_period_days_in_month: int = 0
    active_medications_count: int = 0


class CycleService:
    """
    Service layer providing historical cycle statistics, interval analysis,
    and calendar data aggregation. Reuses existing SQLite tables without duplication.
    """

    @classmethod
    def get_recorded_period_start_dates(cls, profile_id: str, db_path: Optional[str] = None) -> List[date]:
        """
        Extracts confirmed period start dates for the profile from:
        1. Explicit bleeding records in symptom_entries (category = 'Pelvic & Menstrual')
        2. Profile preferences ('period_start_date' and 'recorded_period_starts')
        Clusters consecutive bleeding days into distinct start episodes (separated by >= 14 days).
        """
        conn = get_connection(db_path)
        cursor = conn.cursor()

        raw_dates: set[date] = set()

        try:
            # 1. Query symptom_entries for menstrual bleeding records
            cursor.execute("""
                SELECT onset_date, symptom FROM symptom_entries
                WHERE profile_id = ? 
                AND category = 'Pelvic & Menstrual'
                AND (
                    LOWER(symptom) LIKE '%bleeding%' OR 
                    LOWER(symptom) LIKE '%period%' OR 
                    LOWER(symptom) LIKE '%flow%' OR 
                    LOWER(symptom) LIKE '%menstrua%'
                )
                ORDER BY onset_date ASC;
            """, (profile_id,))
            for row in cursor.fetchall():
                try:
                    d = datetime.strptime(row[0], "%Y-%m-%d").date()
                    raw_dates.add(d)
                except Exception:
                    continue

            # 2. Check profile preferences for recorded period anchors
            cursor.execute("SELECT preferences_json FROM profiles WHERE id = ?;", (profile_id,))
            prof_row = cursor.fetchone()
            if prof_row and prof_row[0]:
                import json
                try:
                    pref = json.loads(prof_row[0])
                    if pref.get("period_start_date"):
                        raw_dates.add(datetime.strptime(pref["period_start_date"], "%Y-%m-%d").date())
                    if isinstance(pref.get("recorded_period_starts"), list):
                        for ps in pref["recorded_period_starts"]:
                            raw_dates.add(datetime.strptime(ps, "%Y-%m-%d").date())
                except Exception:
                    pass

        finally:
            conn.close()

        if not raw_dates:
            return []

        # Sort dates chronologically
        sorted_dates = sorted(list(raw_dates))

        # Cluster into distinct cycle start dates:
        # Consecutive bleeding days (<= 5 days apart) belong to the same period.
        # A new cycle start requires >= 14 days separation from previous start.
        distinct_starts: List[date] = []
        for d in sorted_dates:
            if not distinct_starts:
                distinct_starts.append(d)
            else:
                last_start = distinct_starts[-1]
                if (d - last_start).days >= 14:
                    distinct_starts.append(d)

        return distinct_starts

    @classmethod
    def calculate_cycle_statistics(cls, profile_id: str, db_path: Optional[str] = None) -> CycleStatisticsData:
        """
        Calculates mathematically honest historical cycle intervals and variation metrics.
        Adheres strictly to clinical safety boundaries:
        - Never diagnoses PCOS, predicts risk scores, or makes definitive claims.
        - Calculates intervals strictly between consecutive recorded period start dates.
        - Excludes incomplete intervals or intervals > 75 days (probable missing/unrecorded cycles).
        - Honestly displays sample counts and requires >= 3 cycles for trend analysis.
        """
        start_dates = cls.get_recorded_period_start_dates(profile_id, db_path)

        if not start_dates:
            return CycleStatisticsData(
                profile_id=profile_id,
                total_periods_recorded=0,
                total_cycles_analyzed=0,
                clinical_note="No period start dates recorded yet. Tap 'Log Period Start' or record menstrual flow to begin tracking your cycle intervals.",
                variation_status="No Data Recorded"
            )

        if len(start_dates) == 1:
            return CycleStatisticsData(
                profile_id=profile_id,
                total_periods_recorded=1,
                total_cycles_analyzed=0,
                clinical_note="Only 1 period start date recorded. At least 2 recorded period start dates are needed to calculate your first cycle interval.",
                variation_status="Insufficient Data"
            )

        # Compute intervals between consecutive start dates
        intervals: List[CycleInterval] = []
        valid_lengths: List[int] = []

        for idx in range(len(start_dates) - 1):
            s_date = start_dates[idx]
            e_date = start_dates[idx + 1]
            diff_days = (e_date - s_date).days

            # Validity check:
            # Cycles between 15 and 75 days are considered analyzable.
            # Intervals > 75 days suggest intervening unrecorded period(s) and must not inflate average.
            if 15 <= diff_days <= 75:
                intervals.append(CycleInterval(
                    cycle_index=idx + 1,
                    start_date=str(s_date),
                    end_date=str(e_date),
                    length_days=diff_days,
                    is_valid=True,
                    notes=f"{diff_days} days"
                ))
                valid_lengths.append(diff_days)
            else:
                intervals.append(CycleInterval(
                    cycle_index=idx + 1,
                    start_date=str(s_date),
                    end_date=str(e_date),
                    length_days=diff_days,
                    is_valid=False,
                    notes=f"Interval of {diff_days} days exceeds typical limit (likely includes unrecorded periods); excluded from statistics."
                ))

        if not valid_lengths:
            return CycleStatisticsData(
                profile_id=profile_id,
                total_periods_recorded=len(start_dates),
                total_cycles_analyzed=0,
                intervals=intervals,
                clinical_note="Recorded intervals contain large gaps (likely unrecorded cycles in between). To maintain statistical accuracy, intervals over 75 days are excluded from average calculations.",
                variation_status="Gaps Detected"
            )

        avg_len = round(float(np.mean(valid_lengths)), 1)
        min_len = int(min(valid_lengths))
        max_len = int(max(valid_lengths))
        variation = max_len - min_len
        std_dev = round(float(np.std(valid_lengths)), 1) if len(valid_lengths) > 1 else 0.0

        if len(valid_lengths) == 1:
            return CycleStatisticsData(
                profile_id=profile_id,
                total_periods_recorded=len(start_dates),
                total_cycles_analyzed=1,
                intervals=intervals,
                average_cycle_length=avg_len,
                shortest_cycle=min_len,
                longest_cycle=max_len,
                variation_days=0,
                cycle_std_dev=0.0,
                is_sufficient_for_trend=False,
                variation_status="Baseline Established (1 cycle)",
                clinical_note=f"1 cycle interval recorded ({valid_lengths[0]} days). At least 3 recorded cycles are needed to establish a personal variation trend."
            )

        # 2 or more valid cycles analyzed
        is_sufficient = len(valid_lengths) >= 3

        if variation <= 7:
            status = "Consistent Interval Pattern"
            note = (
                f"Based on {len(valid_lengths)} recorded cycle intervals, your cycle length averages {avg_len} days "
                f"with a variation of ±{variation} days (shortest: {min_len}d, longest: {max_len}d). "
                f"This reflects a relatively consistent interval pattern."
            )
        else:
            status = "Variable Interval Pattern"
            # Non-diagnostic statement complying strictly with rule 1
            note = (
                f"Based on {len(valid_lengths)} recorded cycle intervals, your cycle length shows notable variation of {variation} days "
                f"(ranging from {min_len} to {max_len} days, average {avg_len} days). "
                f"Cycle variation can occur for many natural reasons, including sleep disruption, high stress, thyroid levels, "
                f"perimenopause, or metabolic factors. Your recorded cycle pattern may be worth discussing with a healthcare professional."
            )

        return CycleStatisticsData(
            profile_id=profile_id,
            total_periods_recorded=len(start_dates),
            total_cycles_analyzed=len(valid_lengths),
            intervals=intervals,
            average_cycle_length=avg_len,
            shortest_cycle=min_len,
            longest_cycle=max_len,
            variation_days=variation,
            cycle_std_dev=std_dev,
            is_sufficient_for_trend=is_sufficient,
            variation_status=status,
            clinical_note=note
        )

    @classmethod
    def get_month_calendar_data(
        cls,
        profile_id: str,
        year: int,
        month: int,
        db_path: Optional[str] = None
    ) -> MonthCalendarData:
        """
        Synthesizes a full month's calendar days with heatmap dots for:
        - Confirmed Period Days (real recorded bleeding)
        - Predicted Period Days (clearly marked as estimated future dates, NEVER saved)
        - Logged Symptoms with severity ratings
        - Active Medications
        - Lifestyle Context
        100% scoped to active profile_id.
        """
        conn = get_connection(db_path)
        cursor = conn.cursor()

        month_str = f"{year}-{month:02d}"
        today_date = date.today()
        _, num_days_in_month = calendar.monthrange(year, month)
        month_name = calendar.month_name[month]

        # 1. Fetch profile preferences for cycle duration & baseline
        cursor.execute("SELECT preferences_json FROM profiles WHERE id = ?;", (profile_id,))
        prof_row = cursor.fetchone()
        cycle_len = 28
        flow_duration = 5
        period_start_str = ""

        if prof_row and prof_row[0]:
            import json
            try:
                p_pref = json.loads(prof_row[0])
                cycle_len = int(p_pref.get("cycle_length", 28))
                flow_duration = int(p_pref.get("period_duration", 5))
                period_start_str = p_pref.get("period_start_date", "")
            except Exception:
                pass

        # 2. Fetch all symptoms logged in this month for this profile
        cursor.execute("""
            SELECT id, symptom, category, onset_date, severity, status, duration_hours, impact, notes, context_json
            FROM symptom_entries
            WHERE profile_id = ? AND onset_date LIKE ?
            ORDER BY onset_date ASC, severity DESC;
        """, (profile_id, f"{month_str}-%"))

        symptoms_by_date: Dict[str, List[Dict[str, Any]]] = {}
        for row in cursor.fetchall():
            s_date = row[3]
            ctx = {}
            if row[9]:
                import json
                try:
                    ctx = json.loads(row[9])
                except Exception:
                    pass

            entry_dict = {
                "id": row[0],
                "symptom": row[1],
                "category": row[2],
                "onset_date": s_date,
                "severity": row[4],
                "status": row[5],
                "duration_hours": row[6],
                "impact": row[7],
                "notes": row[8] or "",
                "context": ctx
            }
            if s_date not in symptoms_by_date:
                symptoms_by_date[s_date] = []
            symptoms_by_date[s_date].append(entry_dict)

        # 3. Fetch active medications for this profile
        cursor.execute("""
            SELECT name, dosage, frequency, started_date, category
            FROM medications
            WHERE profile_id = ?
            ORDER BY name ASC;
        """, (profile_id,))
        all_meds = cursor.fetchall()

        # 4. Find all confirmed period start dates across history
        conn.close()
        distinct_period_starts = cls.get_recorded_period_start_dates(profile_id, db_path)

        # Build confirmed period dates set:
        # Each period start covers start_date to start_date + flow_duration - 1
        confirmed_period_dates: set[date] = set()
        for p_start in distinct_period_starts:
            for offset in range(flow_duration):
                confirmed_period_dates.add(p_start + timedelta(days=offset))

        # Also add any explicit bleeding days logged in this month
        for s_date_str, s_list in symptoms_by_date.items():
            for s_entry in s_list:
                s_name = s_entry["symptom"].lower()
                if "bleeding" in s_name or "period" in s_name or "flow" in s_name:
                    try:
                        confirmed_period_dates.add(datetime.strptime(s_date_str, "%Y-%m-%d").date())
                    except Exception:
                        pass

        # 5. Build predicted future period dates (Rule 3: Distinct from recorded periods, never saved)
        predicted_period_dates: set[date] = set()
        if distinct_period_starts:
            last_recorded_start = max(distinct_period_starts)
            # Project forward up to 3 cycles
            curr_pred = last_recorded_start + timedelta(days=cycle_len)
            while curr_pred <= today_date + timedelta(days=90):
                for offset in range(flow_duration):
                    p_day = curr_pred + timedelta(days=offset)
                    # Only mark future dates as predicted
                    if p_day >= today_date and p_day not in confirmed_period_dates:
                        predicted_period_dates.add(p_day)
                curr_pred += timedelta(days=cycle_len)

        # 6. Assemble CalendarDayData for every day of the month
        days_list: List[CalendarDayData] = []
        total_symptoms_count = 0
        total_period_days = 0

        for day_num in range(1, num_days_in_month + 1):
            curr_d = date(year, month, day_num)
            curr_d_str = curr_d.strftime("%Y-%m-%d")
            is_today = (curr_d == today_date)

            # Check period status
            is_confirmed_period = curr_d in confirmed_period_dates
            is_pred_period = (curr_d in predicted_period_dates) and (not is_confirmed_period)

            if is_confirmed_period:
                total_period_days += 1

            # Symptoms on this day
            day_symptoms = symptoms_by_date.get(curr_d_str, [])
            total_symptoms_count += len(day_symptoms)
            max_sev = max([s["severity"] for s in day_symptoms]) if day_symptoms else None

            # Context
            ctx_summary = {}
            for s in day_symptoms:
                if s.get("context"):
                    ctx_summary.update(s["context"])

            # Active medications on this day (started_date <= curr_d_str)
            active_med_names = []
            for m in all_meds:
                m_start = m[3]
                if not m_start or m_start <= curr_d_str:
                    active_med_names.append(f"{m[0]} ({m[1]})")

            days_list.append(CalendarDayData(
                date_str=curr_d_str,
                day_num=day_num,
                is_current_month=True,
                is_today=is_today,
                has_period=is_confirmed_period,
                is_predicted_period=is_pred_period,
                symptoms=day_symptoms,
                symptom_count=len(day_symptoms),
                max_severity=max_sev,
                medications=active_med_names,
                lifestyle_context=ctx_summary
            ))

        return MonthCalendarData(
            profile_id=profile_id,
            year=year,
            month=month,
            month_name=month_name,
            days=days_list,
            total_symptoms_in_month=total_symptoms_count,
            total_period_days_in_month=total_period_days,
            active_medications_count=len(all_meds)
        )
