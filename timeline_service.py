"""
HERPath AI - Timeline Intelligence Service
recHERsion 2026 | PS1: Women's Healthcare

Provides deterministic, on-device chronological event unification, multi-dimensional
filtering, dual-period comparative analysis, explainable pattern generation, and Plotly
visualizations. Strictly non-diagnostic and privacy-preserving.
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from models import SymptomEntry, MedicationEntry
from database import get_symptoms, get_medications


@dataclass
class TimelineEvent:
    """Represents a unified chronological health observation or intervention."""
    event_id: str                          # e.g. "symptom_12" or "med_4"
    event_type: str                        # "symptom" or "medication"
    date: str                              # YYYY-MM-DD
    time: Optional[str]                    # HH:MM or None
    title: str                             # Display title (e.g. "Migraine" or "Started Sumatriptan")
    category: str                          # Health category or intervention type
    severity: Optional[int] = None         # 1 - 10 (symptoms)
    duration_hours: Optional[float] = None
    status: Optional[str] = None           # "Ongoing", "Resolved", "Intermittent"
    impact: Optional[str] = None           # Functional impact rating
    notes: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict) # sleep, stress, energy, cycle_phase
    dosage: Optional[str] = None           # For medications
    frequency: Optional[str] = None        # For medications
    source: str = "SQLite Database"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "date": self.date,
            "time": self.time,
            "title": self.title,
            "category": self.category,
            "severity": self.severity,
            "duration_hours": self.duration_hours,
            "status": self.status,
            "impact": self.impact,
            "notes": self.notes,
            "context": self.context,
            "dosage": self.dosage,
            "frequency": self.frequency,
            "source": self.source
        }


class TimelineService:
    """
    On-device analytics & unification engine for chronological health records.
    All calculations are deterministic, local, and profile-isolated.
    """

    def __init__(self, profile_id: str, db_path: Optional[str] = None):
        self.profile_id = profile_id
        self.db_path = db_path

    def fetch_all_events(self) -> List[TimelineEvent]:
        """
        Fetches recorded symptoms and medications for the active profile from SQLite
        and unifies them into a chronologically sorted event stream.
        """
        symptoms = get_symptoms(self.profile_id, db_path=self.db_path)
        medications = get_medications(self.profile_id, db_path=self.db_path)

        events: List[TimelineEvent] = []

        # 1. Unify Symptom Entries
        for s in symptoms:
            if not s.onset_date:
                continue
            events.append(TimelineEvent(
                event_id=f"symptom_{s.id or 0}",
                event_type="symptom",
                date=str(s.onset_date).strip(),
                time=s.onset_time,
                title=s.symptom,
                category=s.category,
                severity=s.severity,
                duration_hours=s.duration_hours,
                status=s.status,
                impact=s.impact,
                notes=s.notes or "",
                context=s.context or {},
                source="Symptom Journal (SQLite)"
            ))

        # 2. Unify Medication / Treatment Start Events (only actual records)
        for m in medications:
            if not m.started_date:
                continue
            events.append(TimelineEvent(
                event_id=f"med_{m.id or 0}",
                event_type="medication",
                date=str(m.started_date).strip(),
                time=None,
                title=f"Started {m.name}",
                category=m.category,
                dosage=m.dosage or "",
                frequency=m.frequency or "",
                notes=m.notes or "",
                source="Medication Registry (SQLite)"
            ))

        # 3. Sort chronologically (ascending by date, then time or ID)
        events.sort(key=lambda e: (e.date, e.time or "00:00", e.event_id))
        return events

    @staticmethod
    def filter_events(
        events: List[TimelineEvent],
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None,
        categories: Optional[List[str]] = None,
        symptoms: Optional[List[str]] = None,
        min_severity: int = 1,
        max_severity: int = 10,
        event_types: Optional[List[str]] = None
    ) -> List[TimelineEvent]:
        """
        Applies multi-dimensional filters to a timeline event collection.
        Handles missing values safely and does not fabricate entries.
        """
        filtered: List[TimelineEvent] = []

        # Normalize dates to strings YYYY-MM-DD
        start_str = str(start_date) if start_date else None
        end_str = str(end_date) if end_date else None

        active_categories = set(categories) if categories and "All Categories" not in categories else None
        active_symptoms = set(symptoms) if symptoms and "All Symptoms" not in symptoms else None
        types_set = set(event_types) if event_types else {"Symptoms", "Medications"}

        for e in events:
            # 1. Date Range Filter
            if start_str and e.date < start_str:
                continue
            if end_str and e.date > end_str:
                continue

            # 2. Event Type Filter
            if e.event_type == "symptom":
                if "Symptoms" not in types_set:
                    # Check if allowed by context filters
                    has_sleep_filter = "Sleep Context" in types_set and bool(e.context.get("sleep"))
                    has_stress_filter = "Stress Context" in types_set and bool(e.context.get("stress"))
                    has_impact_filter = "Functional Impact" in types_set and e.impact and e.impact != "None"
                    if not (has_sleep_filter or has_stress_filter or has_impact_filter):
                        continue

                # 3. Category Filter
                if active_categories and e.category not in active_categories:
                    continue

                # 4. Symptom Name Filter
                if active_symptoms and e.title not in active_symptoms:
                    continue

                # 5. Severity Filter
                if e.severity is not None:
                    if e.severity < min_severity or e.severity > max_severity:
                        continue

            elif e.event_type == "medication":
                if "Medications" not in types_set:
                    continue
                # Medications pass unless category specifically filtered
                if active_categories and e.category not in active_categories:
                    continue

            filtered.append(e)

        return filtered

    @staticmethod
    def calculate_summary_metrics(events: List[TimelineEvent]) -> Dict[str, Any]:
        """
        Calculates descriptive summary metrics over a collection of timeline events.
        Does not interpret missing severity or duration as zero.
        """
        symptom_events = [e for e in events if e.event_type == "symptom"]
        med_events = [e for e in events if e.event_type == "medication"]

        total_episodes = len(symptom_events)
        distinct_dates = len(set(e.date for e in events))
        distinct_symptom_dates = len(set(e.date for e in symptom_events))

        severities = [e.severity for e in symptom_events if e.severity is not None]
        avg_severity = round(float(np.mean(severities)), 1) if severities else None
        max_severity = max(severities) if severities else None

        durations = [e.duration_hours for e in symptom_events if e.duration_hours is not None]
        avg_duration = round(float(np.mean(durations)), 1) if durations else None

        impact_count = sum(1 for e in symptom_events if e.impact and e.impact != "None")
        sleep_disrupted_count = sum(
            1 for e in symptom_events
            if e.context.get("sleep") in [
                "Disrupted / Fragmented",
                "Severe Insomnia (<5 hrs)",
                "Poor (< 5 hrs)",
                "Restless"
            ]
        )
        high_stress_count = sum(
            1 for e in symptom_events
            if e.context.get("stress") in [
                "High / Pressured",
                "Extreme / Overwhelming",
                "Severe",
                "High"
            ]
        )

        return {
            "total_events": len(events),
            "symptom_episodes": total_episodes,
            "medication_changes": len(med_events),
            "distinct_dates": distinct_dates,
            "distinct_symptom_dates": distinct_symptom_dates,
            "avg_severity": avg_severity,
            "max_severity": max_severity,
            "avg_duration": avg_duration,
            "impact_count": impact_count,
            "sleep_disrupted_count": sleep_disrupted_count,
            "high_stress_count": high_stress_count
        }

    @classmethod
    def compare_periods(
        cls,
        period_a_events: List[TimelineEvent],
        period_b_events: List[TimelineEvent],
        period_a_label: str = "Recent Period",
        period_b_label: str = "Previous Period",
        days_a: int = 30,
        days_b: int = 30
    ) -> Dict[str, Any]:
        """
        Compares two distinct date ranges using actual records.
        Handles unequal date ranges by calculating both raw episode counts and
        observation rates per day.
        """
        metrics_a = cls.calculate_summary_metrics(period_a_events)
        metrics_b = cls.calculate_summary_metrics(period_b_events)

        safe_days_a = max(1, days_a)
        safe_days_b = max(1, days_b)

        rate_a = round(metrics_a["symptom_episodes"] / safe_days_a, 2)
        rate_b = round(metrics_b["symptom_episodes"] / safe_days_b, 2)

        # Delta calculations (Period A - Period B)
        diff_episodes = metrics_a["symptom_episodes"] - metrics_b["symptom_episodes"]
        diff_rate = round(rate_a - rate_b, 2)

        if metrics_a["avg_severity"] is not None and metrics_b["avg_severity"] is not None:
            diff_severity = round(metrics_a["avg_severity"] - metrics_b["avg_severity"], 1)
        else:
            diff_severity = None

        if metrics_a["avg_duration"] is not None and metrics_b["avg_duration"] is not None:
            diff_duration = round(metrics_a["avg_duration"] - metrics_b["avg_duration"], 1)
        else:
            diff_duration = None

        diff_impact = metrics_a["impact_count"] - metrics_b["impact_count"]
        rate_imp_a = round((metrics_a["impact_count"] / max(1, metrics_a["symptom_episodes"])) * 100, 1) if metrics_a["symptom_episodes"] > 0 else 0.0
        rate_imp_b = round((metrics_b["impact_count"] / max(1, metrics_b["symptom_episodes"])) * 100, 1) if metrics_b["symptom_episodes"] > 0 else 0.0
        diff_impact_rate = round(rate_imp_a - rate_imp_b, 1)

        is_sufficient = metrics_a["symptom_episodes"] >= 2 and metrics_b["symptom_episodes"] >= 2
        sufficiency_message = (
            f"Sufficient records available ({metrics_a['symptom_episodes']} in {period_a_label}, {metrics_b['symptom_episodes']} in {period_b_label}) for comparative trend evaluation."
            if is_sufficient
            else f"Insufficient records for reliable comparative analysis: {period_a_label} has {metrics_a['symptom_episodes']} episodes; {period_b_label} has {metrics_b['symptom_episodes']} episodes (minimum 2 per period recommended)."
        )

        # Per-symptom breakdown
        sym_map_a: Dict[str, List[TimelineEvent]] = {}
        for e in period_a_events:
            if e.event_type == "symptom":
                sym_map_a.setdefault(e.title, []).append(e)

        sym_map_b: Dict[str, List[TimelineEvent]] = {}
        for e in period_b_events:
            if e.event_type == "symptom":
                sym_map_b.setdefault(e.title, []).append(e)

        all_symptom_names = sorted(list(set(sym_map_a.keys()) | set(sym_map_b.keys())))
        symptom_comparisons = []

        for sym in all_symptom_names:
            ev_a = sym_map_a.get(sym, [])
            ev_b = sym_map_b.get(sym, [])

            cnt_a = len(ev_a)
            cnt_b = len(ev_b)

            sevs_a = [e.severity for e in ev_a if e.severity is not None]
            sevs_b = [e.severity for e in ev_b if e.severity is not None]

            avg_s_a = round(float(np.mean(sevs_a)), 1) if sevs_a else None
            avg_s_b = round(float(np.mean(sevs_b)), 1) if sevs_b else None

            max_s_a = max(sevs_a) if sevs_a else None
            max_s_b = max(sevs_b) if sevs_b else None

            durs_a = [e.duration_hours for e in ev_a if e.duration_hours is not None]
            durs_b = [e.duration_hours for e in ev_b if e.duration_hours is not None]

            avg_d_a = round(float(np.mean(durs_a)), 1) if durs_a else None
            avg_d_b = round(float(np.mean(durs_b)), 1) if durs_b else None

            s_diff = round(avg_s_a - avg_s_b, 1) if (avg_s_a is not None and avg_s_b is not None) else None

            imp_a = sum(1 for e in ev_a if e.impact and e.impact != "None")
            imp_b = sum(1 for e in ev_b if e.impact and e.impact != "None")
            imp_diff = imp_a - imp_b

            category = ev_a[0].category if ev_a else (ev_b[0].category if ev_b else "General")

            symptom_comparisons.append({
                "symptom": sym,
                "category": category,
                "count_a": cnt_a,
                "count_b": cnt_b,
                "count_diff": cnt_a - cnt_b,
                "episodes_a": cnt_a,
                "episodes_b": cnt_b,
                "episodes_diff": cnt_a - cnt_b,
                "avg_sev_a": avg_s_a,
                "avg_sev_b": avg_s_b,
                "avg_severity_a": avg_s_a,
                "avg_severity_b": avg_s_b,
                "sev_diff": s_diff,
                "severity_diff": s_diff,
                "max_severity": max([m for m in [max_s_a, max_s_b] if m is not None], default=None),
                "max_sev_a": max_s_a,
                "max_sev_b": max_s_b,
                "avg_dur_a": avg_d_a,
                "avg_dur_b": avg_d_b,
                "impact_a": imp_a,
                "impact_b": imp_b,
                "impact_diff": imp_diff
            })

        return {
            "period_a": {
                "label": period_a_label,
                "days": safe_days_a,
                "metrics": metrics_a,
                "rate_per_day": rate_a,
                "daily_rate": rate_a,
                "impact_rate": rate_imp_a
            },
            "period_b": {
                "label": period_b_label,
                "days": safe_days_b,
                "metrics": metrics_b,
                "rate_per_day": rate_b,
                "daily_rate": rate_b,
                "impact_rate": rate_imp_b
            },
            "deltas": {
                "episodes": diff_episodes,
                "rate_per_day": diff_rate,
                "severity": diff_severity,
                "duration": diff_duration,
                "impact": diff_impact,
                "impact_rate": diff_impact_rate
            },
            "data_sufficiency": {
                "is_sufficient": is_sufficient,
                "message": sufficiency_message,
                "count_a": metrics_a["symptom_episodes"],
                "count_b": metrics_b["symptom_episodes"]
            },
            "symptom_breakdown": symptom_comparisons
        }

    @classmethod
    def generate_explainable_insights(
        cls,
        events: List[TimelineEvent],
        comparison: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generates explainable, rule-based observations grounded strictly in actual database records.
        Adheres to clinical safety boundaries: does not claim causation, diagnose diseases,
        infer clinical conditions, or predict future outcomes.
        """
        insights: List[Dict[str, Any]] = []

        symptom_events = [e for e in events if e.event_type == "symptom"]
        if not symptom_events:
            return [{
                "title": "No Recorded Episodes in Selected Filter",
                "category": "Baseline",
                "statement": "No symptom entries were recorded within the selected date and filter range.",
                "exact_evidence": "0 matching entries in local SQLite database.",
                "date_range": "N/A",
                "record_count": 0,
                "supporting_dates": [],
                "calculation_note": "Filter count query returned 0 rows.",
                "limitation": "Log symptoms regularly to observe meaningful chronological health patterns.",
                "level": "info",
                "why_explanation": {
                    "criteria": "Active date and category filters matched 0 database records.",
                    "formula": "count(matching_records) == 0",
                    "evidence": "No entries available to compute health patterns.",
                    "supporting_dates": [],
                    "safety_note": "Antigravity HERPath AI displays insights strictly grounded in logged observations; zero records produce no speculative inferences.",
                    "clinical_question": "Discuss your overall symptom history with your doctor even if recent journal entries are empty."
                }
            }]

        dates = sorted([e.date for e in symptom_events])
        start_d, end_d = dates[0], dates[-1]
        date_range_str = f"{start_d} to {end_d}"
        total_count = len(symptom_events)

        # 1. Frequency & Top Symptom Observation
        sym_counts = pd.Series([e.title for e in symptom_events]).value_counts()
        top_sym = sym_counts.index[0]
        top_count = int(sym_counts.iloc[0])
        top_pct = round((top_count / total_count) * 100, 1)
        top_sym_dates = sorted(list(set(e.date for e in symptom_events if e.title == top_sym)))

        insights.append({
            "title": f"Primary Reported Symptom: {top_sym}",
            "category": "Frequency",
            "statement": f"'{top_sym}' was recorded on {top_count} occasions between {date_range_str}, representing {top_pct}% of symptom entries in this view.",
            "exact_evidence": f"{top_count} of {total_count} recorded entries over {len(set(dates))} distinct observation dates.",
            "date_range": date_range_str,
            "record_count": top_count,
            "supporting_dates": top_sym_dates,
            "calculation_note": f"count(symptom == '{top_sym}') / total_symptom_entries * 100",
            "limitation": "Personal journaling frequency depends on individual recording habits and may not reflect continuous symptom presence.",
            "level": "observation",
            "why_explanation": {
                "criteria": f"Identifies the symptom with the highest logging frequency in the selected date range ({date_range_str}).",
                "formula": f"count('{top_sym}') / total_entries = {top_count} / {total_count} = {top_pct}%",
                "evidence": f"Logged on {len(top_sym_dates)} distinct calendar dates: {', '.join(top_sym_dates[:5])}{' (and more...)' if len(top_sym_dates) > 5 else ''}.",
                "supporting_dates": top_sym_dates,
                "safety_note": "A higher logging frequency reflects how often you documented this symptom. It does not establish disease progression or a confirmed diagnosis.",
                "clinical_question": f"Is a frequency of {top_count} episodes of {top_sym} typical for my profile, and are there preventative steps we should consider?"
            }
        })

        # 2. Severity Trajectory & Peak
        sevs = [e.severity for e in symptom_events if e.severity is not None]
        if sevs:
            avg_sev = round(float(np.mean(sevs)), 1)
            max_sev = max(sevs)
            max_entries = [e for e in symptom_events if e.severity == max_sev]
            peak_dates = sorted(list(set(e.date for e in max_entries)))
            peak_date = peak_dates[0] if peak_dates else "recorded dates"
            peak_sym = max_entries[0].title if max_entries else top_sym

            insights.append({
                "title": "Recorded Severity Distribution",
                "category": "Severity",
                "statement": f"Average recorded symptom severity was {avg_sev}/10 across {len(sevs)} entries in the selected period. Peak severity was {max_sev}/10 ({peak_sym} on {peak_date}).",
                "exact_evidence": f"Mean calculation from {len(sevs)} valid severity ratings (range: {min(sevs)}–{max_sev}/10).",
                "date_range": date_range_str,
                "record_count": len(sevs),
                "supporting_dates": peak_dates,
                "calculation_note": "sum(recorded_severity) / count(valid_severities)",
                "limitation": "Severity scores represent self-reported subjective perception (1–10 scale), not laboratory or clinical biomarker measurements.",
                "level": "observation",
                "why_explanation": {
                    "criteria": "Aggregates all numeric severity scores recorded by the user on a 1–10 visual analog scale.",
                    "formula": f"Mean = sum({len(sevs)} scores) / {len(sevs)} = {avg_sev}/10 | Max = {max_sev}/10",
                    "evidence": f"Peak severity {max_sev}/10 was recorded on: {', '.join(peak_dates)} for {peak_sym}.",
                    "supporting_dates": peak_dates,
                    "safety_note": "Subjective pain and severity scores help communicate symptom burden during clinical review. They do not replace objective clinical diagnostic criteria.",
                    "clinical_question": f"What acute interventions or pain management strategies do you recommend when my symptom severity reaches {max_sev}/10?"
                }
            })

        # 3. Episode Duration Pattern
        dur_entries = [e for e in symptom_events if e.duration_hours is not None and e.duration_hours > 0]
        if len(dur_entries) >= 2:
            durations = [e.duration_hours for e in dur_entries]
            avg_dur = round(float(np.mean(durations)), 1)
            max_dur = max(durations)
            max_dur_entries = [e for e in dur_entries if e.duration_hours == max_dur]
            dur_dates = sorted(list(set(e.date for e in max_dur_entries)))

            insights.append({
                "title": "Episode Duration Pattern",
                "category": "Duration",
                "statement": f"Symptoms had an average recorded duration of {avg_dur} hours across {len(dur_entries)} timed episodes (longest episode: {max_dur} hrs on {dur_dates[0]}).",
                "exact_evidence": f"{len(dur_entries)} episodes logged with duration tracking between {date_range_str}.",
                "date_range": date_range_str,
                "record_count": len(dur_entries),
                "supporting_dates": dur_dates,
                "calculation_note": "sum(duration_hours) / count(timed_entries)",
                "limitation": "Self-recorded duration estimates the time window of symptom experience and does not replace continuous medical monitoring.",
                "level": "observation",
                "why_explanation": {
                    "criteria": "Evaluated when >= 2 symptom entries have recorded duration in hours.",
                    "formula": f"Average duration = sum(hours) / n = {avg_dur} hrs; Maximum duration = {max_dur} hrs",
                    "evidence": f"{len(dur_entries)} episodes logged with duration; peak duration ({max_dur}h) on {', '.join(dur_dates)}.",
                    "supporting_dates": dur_dates,
                    "safety_note": "Duration logs indicate how long episodes typically persist. They do not diagnose chronicity or indicate underlying pathology.",
                    "clinical_question": f"Does an average episode duration of {avg_dur} hours suggest acute rescue medication or longer-acting maintenance therapies?"
                }
            })

        # 4. Contextual Sleep Co-Occurrence (Strict safety wording: 'coincided with', 'recorded alongside')
        sleep_entries = [e for e in symptom_events if e.context.get("sleep")]
        if len(sleep_entries) >= 3:
            poor_sleep_matches = [
                e for e in sleep_entries
                if e.context.get("sleep") in ["Disrupted / Fragmented", "Severe Insomnia (<5 hrs)", "Poor (< 5 hrs)", "Restless"]
            ]
            poor_count = len(poor_sleep_matches)
            poor_pct = round((poor_count / len(sleep_entries)) * 100, 1)
            poor_sleep_dates = sorted(list(set(e.date for e in poor_sleep_matches)))

            insights.append({
                "title": "Sleep & Symptom Co-Occurrence",
                "category": "Context",
                "statement": f"Symptom entries coincided with poor or fragmented sleep ratings in {poor_count} of {len(sleep_entries)} contextual entries ({poor_pct}%).",
                "exact_evidence": f"{poor_count} entries recorded alongside disrupted sleep ratings between {date_range_str}.",
                "date_range": date_range_str,
                "record_count": len(sleep_entries),
                "supporting_dates": poor_sleep_dates,
                "calculation_note": "count(symptoms_with_disrupted_sleep) / count(symptoms_with_sleep_logged) * 100",
                "limitation": "Exploratory co-occurrence only. These records demonstrate temporal coexistence; they do not establish that sleep disruption caused the symptom.",
                "level": "notice" if poor_pct >= 50 else "observation",
                "why_explanation": {
                    "criteria": "Triggered when >= 3 entries include sleep quality context and co-occur with disrupted sleep ratings.",
                    "formula": f"Co-occurrence rate = {poor_count} / {len(sleep_entries)} = {poor_pct}%",
                    "evidence": f"Poor/fragmented sleep recorded on the same date as symptoms on: {', '.join(poor_sleep_dates)}.",
                    "supporting_dates": poor_sleep_dates,
                    "safety_note": "Co-occurrence does not equal causation. While sleep and symptom flares often coincide chronologically, this does not prove sleep loss caused the symptom.",
                    "clinical_question": "Could optimizing my sleep hygiene or addressing nocturnal symptoms help reduce the frequency or severity of my daytime episodes?"
                }
            })
        elif sleep_entries:
            sleep_dates = sorted(list(set(e.date for e in sleep_entries)))
            insights.append({
                "title": "Sleep Context Observations",
                "category": "Context",
                "statement": "Fewer than 3 entries included sleep context. There is insufficient recorded data to observe consistent sleep patterns.",
                "exact_evidence": f"Only {len(sleep_entries)} entries contain sleep context.",
                "date_range": date_range_str,
                "record_count": len(sleep_entries),
                "supporting_dates": sleep_dates,
                "calculation_note": "Sample size check: n < 3 threshold triggered.",
                "limitation": "Consistently logging sleep context alongside symptoms helps reveal potential wellness correlations.",
                "level": "info",
                "why_explanation": {
                    "criteria": "Sample size verification: Minimum 3 contextual logs required for pattern detection.",
                    "formula": f"Current sleep logs count = {len(sleep_entries)} < 3 minimum threshold",
                    "evidence": f"Entries logged on {', '.join(sleep_dates)}.",
                    "supporting_dates": sleep_dates,
                    "safety_note": "HERPath AI does not extrapolate health patterns without sufficient sample sizes to avoid misleading associations.",
                    "clinical_question": "Should I keep a daily sleep and symptom diary ahead of our next review?"
                }
            })

        # 5. Contextual Stress Co-Occurrence
        stress_entries = [e for e in symptom_events if e.context.get("stress")]
        if len(stress_entries) >= 3:
            high_stress_matches = [
                e for e in stress_entries
                if e.context.get("stress") in ["High / Pressured", "Extreme / Overwhelming", "Severe", "High"]
            ]
            stress_count = len(high_stress_matches)
            stress_pct = round((stress_count / len(stress_entries)) * 100, 1)
            stress_dates = sorted(list(set(e.date for e in high_stress_matches)))

            insights.append({
                "title": "Elevated Stress Co-Occurrence",
                "category": "Context",
                "statement": f"{stress_count} symptom entries coincided with elevated stress ratings in the recorded period ({stress_pct}% of contextual logs).",
                "exact_evidence": f"{stress_count} of {len(stress_entries)} stress-logged entries recorded as High or Overwhelming.",
                "date_range": date_range_str,
                "record_count": len(stress_entries),
                "supporting_dates": stress_dates,
                "calculation_note": "count(symptoms_with_elevated_stress) / count(symptoms_with_stress_logged) * 100",
                "limitation": "Self-reported stress ratings co-occurred alongside physical symptoms; this does not prove stress was the physiological origin of episodes.",
                "level": "notice" if stress_pct >= 50 else "observation",
                "why_explanation": {
                    "criteria": "Triggered when >= 3 entries include stress ratings and co-occur with high or overwhelming stress.",
                    "formula": f"Stress co-occurrence rate = {stress_count} / {len(stress_entries)} = {stress_pct}%",
                    "evidence": f"Elevated stress coincided with symptoms on: {', '.join(stress_dates)}.",
                    "supporting_dates": stress_dates,
                    "safety_note": "Stress often amplifies pain sensitivity or co-occurs with busy periods, but temporal co-occurrence does not mean symptoms are solely stress-induced.",
                    "clinical_question": "What stress management or nervous system regulation approaches are most appropriate alongside medical treatment?"
                }
            })

        # 6. Menstrual / Hormonal Cycle Phase Co-Occurrence
        cycle_entries = [
            e for e in symptom_events
            if e.context.get("cycle_phase") and e.context.get("cycle_phase") not in ["Not tracking / NA", "None", ""]
        ]
        if len(cycle_entries) >= 2:
            phase_counts = pd.Series([e.context["cycle_phase"] for e in cycle_entries]).value_counts()
            top_phase = phase_counts.index[0]
            top_phase_count = int(phase_counts.iloc[0])
            top_phase_pct = round((top_phase_count / len(cycle_entries)) * 100, 1)
            phase_matches = [e for e in cycle_entries if e.context.get("cycle_phase") == top_phase]
            phase_dates = sorted(list(set(e.date for e in phase_matches)))

            if top_phase_count >= 2:
                insights.append({
                    "title": f"Cycle Phase Co-Occurrence: {top_phase}",
                    "category": "Cycle Context",
                    "statement": f"Symptom entries repeatedly coincided with your {top_phase} in {top_phase_count} of {len(cycle_entries)} cycle-tracked logs ({top_phase_pct}%).",
                    "exact_evidence": f"{top_phase_count} entries recorded during '{top_phase}' between {date_range_str}.",
                    "date_range": date_range_str,
                    "record_count": len(cycle_entries),
                    "supporting_dates": phase_dates,
                    "calculation_note": f"count(cycle_phase == '{top_phase}') / total_cycle_logged_entries * 100",
                    "limitation": "Hormonal phase timing is based on self-logged tracking and does not substitute for laboratory serum hormone assays.",
                    "level": "notice" if top_phase_pct >= 60 else "observation",
                    "why_explanation": {
                        "criteria": f"Identifies recurring symptom clustering during specific menstrual or hormonal cycle phases (>= 2 entries).",
                        "formula": f"Phase concentration = {top_phase_count} / {len(cycle_entries)} = {top_phase_pct}% in {top_phase}",
                        "evidence": f"Logged during {top_phase} on: {', '.join(phase_dates)}.",
                        "supporting_dates": phase_dates,
                        "safety_note": "A cyclical pattern suggests a temporal co-occurrence with hormonal shifts, not an endocrine disorder or confirmed diagnosis. It does not establish clinical causation.",
                        "clinical_question": f"Given that {top_phase_count} symptom episodes clustered during my {top_phase}, could cyclic hormonal fluctuations be contributing, and should we evaluate targeted luteal or menstrual support?"
                    }
                })

        # 7. Functional Daily Impact Observation
        impact_entries = [e for e in symptom_events if e.impact and e.impact != "None"]
        if impact_entries:
            severe_impact = [e for e in impact_entries if any(k in e.impact for k in ["Severe", "Bedrest", "Unable"])]
            impact_dates = sorted(list(set(e.date for e in impact_entries)))
            impact_pct = round((len(impact_entries) / total_count) * 100, 1)

            insights.append({
                "title": "Functional Daily Impact",
                "category": "Impact",
                "statement": f"Functional disruption was recorded in {len(impact_entries)} of {total_count} symptom episodes ({impact_pct}%), with {len(severe_impact)} rated as significantly impairing daily work or rest.",
                "exact_evidence": f"{len(impact_entries)} entries marked with modified daily plans, work/study interruption, or bedrest.",
                "date_range": date_range_str,
                "record_count": len(impact_entries),
                "supporting_dates": impact_dates,
                "calculation_note": "count(functional_impact != 'None') / total_symptom_entries * 100",
                "limitation": "Functional impact entries assist clinician discussions regarding symptom interference with daily quality of life.",
                "level": "notice" if severe_impact else "observation",
                "why_explanation": {
                    "criteria": "Tallies episodes where user reported disruption to normal routine, work/study, or need for bedrest.",
                    "formula": f"Disruption rate = {len(impact_entries)} / {total_count} = {impact_pct}% ({len(severe_impact)} severe)",
                    "evidence": f"Functional interference logged on: {', '.join(impact_dates)}.",
                    "supporting_dates": impact_dates,
                    "safety_note": "Daily activity impact measures personal quality of life interference to help doctors prioritize supportive interventions. It does not replace clinical disability evaluation or disease staging.",
                    "clinical_question": "Since symptoms interfere with my regular daily routine on several days, what management options could best restore my baseline functionality?"
                }
            })

        # 8. Period Comparison Insight (if available)
        if comparison and comparison.get("period_b", {}).get("metrics", {}).get("symptom_episodes", 0) > 0:
            p_a = comparison["period_a"]
            p_b = comparison["period_b"]
            deltas = comparison["deltas"]

            sev_diff = deltas["severity"]
            ep_diff = deltas["episodes"]
            imp_diff = deltas.get("impact", 0)

            if sev_diff is not None:
                direction = "increased" if sev_diff > 0 else ("decreased" if sev_diff < 0 else "remained steady")
                diff_abs = abs(sev_diff)
                diff_text = f"{direction} by {diff_abs} points (from {p_b['metrics']['avg_severity']} to {p_a['metrics']['avg_severity']}/10)"
            else:
                diff_text = f"had {ep_diff:+d} episode difference"

            comp_dates = sorted(list(set(dates)))
            insights.append({
                "title": f"Comparative Period Trend: {p_a['label']} vs. {p_b['label']}",
                "category": "Comparison",
                "statement": f"Your recorded symptom severity {diff_text} compared with the previous selected period ({ep_diff:+d} episode delta, {imp_diff:+d} functional impact shift).",
                "exact_evidence": f"{p_a['metrics']['symptom_episodes']} episodes in {p_a['label']} vs. {p_b['metrics']['symptom_episodes']} episodes in {p_b['label']}.",
                "date_range": f"{p_b['label']} compared to {p_a['label']}",
                "record_count": p_a['metrics']['symptom_episodes'] + p_b['metrics']['symptom_episodes'],
                "supporting_dates": comp_dates,
                "calculation_note": "Period A metrics minus Period B metrics",
                "limitation": "Comparative shifts reflect logged entries during these specific timeframes and can vary with reporting frequency.",
                "level": "observation",
                "why_explanation": {
                    "criteria": f"Directly contrasts aggregate metrics between {p_a['label']} and {p_b['label']}.",
                    "formula": f"Episode Delta: {ep_diff:+d} | Severity Delta: {f'{sev_diff:+0.1f}' if sev_diff is not None else 'N/A'} | Impact Delta: {imp_diff:+d}",
                    "evidence": f"Period A ({p_a['label']}): {p_a['metrics']['symptom_episodes']} episodes, avg sev {p_a['metrics']['avg_severity']}/10; Period B ({p_b['label']}): {p_b['metrics']['symptom_episodes']} episodes, avg sev {p_b['metrics']['avg_severity']}/10.",
                    "supporting_dates": comp_dates,
                    "safety_note": "Shifts between periods indicate changes in self-logged records over time. They do not constitute an evaluation of disease trajectory without clinician review.",
                    "clinical_question": f"Given the shift between these two periods ({diff_text}), does this trend suggest we should adjust my current management plan?"
                }
            })

        return insights

    # ==========================================
    # Plotly Chart Visualizations
    # ==========================================

    @staticmethod
    def create_severity_timeline_chart(events: List[TimelineEvent]) -> go.Figure:
        """
        Builds an interactive Plotly scatter & spline timeline of recorded symptom severity
        plotted against actual entry dates.
        """
        symptom_events = [e for e in events if e.event_type == "symptom" and e.severity is not None]

        fig = go.Figure()

        if not symptom_events:
            fig.add_annotation(
                text="No symptom severity entries recorded in the selected range",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=13, color="#8A7A83", family="Plus Jakarta Sans")
            )
            fig.update_layout(
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFF9F8",
                height=260,
                margin=dict(l=20, r=20, t=30, b=30)
            )
            return fig

        df = pd.DataFrame([e.to_dict() for e in symptom_events])
        df["date_parsed"] = pd.to_datetime(df["date"])
        df = df.sort_values(by=["date_parsed", "time"])

        # Curated palette for symptoms
        palette = [
            "#B95F7B", "#7E5265", "#C87D94", "#5C3848",
            "#D996AA", "#4A2B39", "#A64B67", "#8E6074"
        ]
        unique_syms = df["title"].unique()
        color_map = {sym: palette[i % len(palette)] for i, sym in enumerate(unique_syms)}

        for sym in unique_syms:
            sub = df[df["title"] == sym]
            hover_texts = []
            for _, row in sub.iterrows():
                ctx = row.get("context") or {}
                ctx_parts = []
                if ctx.get("sleep"):
                    ctx_parts.append(f"Sleep: {ctx['sleep']}")
                if ctx.get("stress"):
                    ctx_parts.append(f"Stress: {ctx['stress']}")
                if ctx.get("cycle_phase"):
                    ctx_parts.append(f"Phase: {ctx['cycle_phase']}")
                ctx_str = " | ".join(ctx_parts) if ctx_parts else "None"

                hover_texts.append(
                    f"<b>{row['title']}</b> ({row['category']})<br>"
                    f"📅 Date: {row['date']}" + (f" at {row['time']}" if row.get("time") else "") + "<br>"
                    f"⚡ Severity: <b>{row['severity']}/10</b><br>"
                    f"⏱️ Duration: {row['duration_hours']}h<br>"
                    f"⚠️ Impact: {row.get('impact') or 'None'}<br>"
                    f"🌿 Context: {ctx_str}"
                    + (f"<br>📝 Note: {row['notes'][:50]}..." if row.get("notes") else "")
                )

            fig.add_trace(go.Scatter(
                x=sub["date_parsed"],
                y=sub["severity"],
                mode="lines+markers",
                name=sym,
                line=dict(color=color_map[sym], width=2.5, shape="spline"),
                marker=dict(
                    size=10,
                    color=color_map[sym],
                    line=dict(width=1.5, color="#FFFFFF")
                ),
                text=hover_texts,
                hoverinfo="text"
            ))

        # Severity Reference Zones
        fig.add_hrect(y0=7, y1=10, fillcolor="#FCEEF3", opacity=0.45, line_width=0, layer="below")
        fig.add_hrect(y0=4, y1=7, fillcolor="#FFF5F7", opacity=0.35, line_width=0, layer="below")
        fig.add_hrect(y0=1, y1=4, fillcolor="#F3FBF7", opacity=0.35, line_width=0, layer="below")

        fig.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFF9F8",
            margin=dict(l=15, r=15, t=30, b=25),
            height=300,
            font=dict(family="Plus Jakarta Sans, sans-serif", size=11, color="#34272E"),
            xaxis=dict(
                title=None,
                showgrid=True,
                gridcolor="#F0DFE6",
                tickformat="%b %d",
                zeroline=False
            ),
            yaxis=dict(
                title="Severity (1–10)",
                range=[0.5, 10.5],
                tickvals=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                showgrid=True,
                gridcolor="#F0DFE6",
                zeroline=False
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(size=10)
            ),
            hovermode="closest"
        )

        return fig

    @staticmethod
    def create_unified_event_timeline_chart(events: List[TimelineEvent]) -> go.Figure:
        """
        Builds a swimlane-style chronological event scatter chart showing symptoms,
        medication starts, and high-impact observations alongside each other.
        """
        fig = go.Figure()

        if not events:
            fig.add_annotation(
                text="No events recorded for this timeline",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=13, color="#8A7A83", family="Plus Jakarta Sans")
            )
            fig.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#FFF9F8", height=240)
            return fig

        symptoms = [e for e in events if e.event_type == "symptom"]
        meds = [e for e in events if e.event_type == "medication"]
        high_impact = [e for e in symptoms if e.impact and e.impact not in ["None", "Mild (Minor inconvenience)"]]

        # Trace 1: Symptoms
        if symptoms:
            fig.add_trace(go.Scatter(
                x=[pd.to_datetime(e.date) for e in symptoms],
                y=["Symptom Episodes"] * len(symptoms),
                mode="markers",
                name="Symptom Logged",
                marker=dict(
                    size=[(e.severity or 5) * 2.2 for e in symptoms],
                    color="#B95F7B",
                    opacity=0.85,
                    line=dict(color="#FFFFFF", width=1.5)
                ),
                text=[f"<b>{e.title}</b><br>Date: {e.date}<br>Severity: {e.severity}/10" for e in symptoms],
                hoverinfo="text"
            ))

        # Trace 2: High Functional Impact
        if high_impact:
            fig.add_trace(go.Scatter(
                x=[pd.to_datetime(e.date) for e in high_impact],
                y=["Functional Impact"] * len(high_impact),
                mode="markers",
                name="Functional Disruption",
                marker=dict(
                    symbol="diamond",
                    size=12,
                    color="#C52233",
                    opacity=0.9,
                    line=dict(color="#FFFFFF", width=1.5)
                ),
                text=[f"<b>{e.title}</b><br>Impact: {e.impact}<br>Date: {e.date}" for e in high_impact],
                hoverinfo="text"
            ))

        # Trace 3: Medication Starts
        if meds:
            fig.add_trace(go.Scatter(
                x=[pd.to_datetime(e.date) for e in meds],
                y=["Medications / Rx"] * len(meds),
                mode="markers",
                name="Medication Started",
                marker=dict(
                    symbol="star",
                    size=14,
                    color="#2563EB",
                    opacity=0.95,
                    line=dict(color="#FFFFFF", width=1.5)
                ),
                text=[f"<b>{e.title}</b><br>Category: {e.category}<br>Dosage: {e.dosage}<br>Started: {e.date}" for e in meds],
                hoverinfo="text"
            ))

        fig.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFF9F8",
            margin=dict(l=15, r=15, t=30, b=25),
            height=250,
            font=dict(family="Plus Jakarta Sans, sans-serif", size=11, color="#34272E"),
            xaxis=dict(
                title=None,
                showgrid=True,
                gridcolor="#F0DFE6",
                tickformat="%b %d",
                zeroline=False
            ),
            yaxis=dict(
                title=None,
                showgrid=True,
                gridcolor="#F0DFE6",
                zeroline=False
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(size=10)
            ),
            hovermode="closest"
        )

        return fig

    @staticmethod
    def create_period_comparison_chart(comparison: Dict[str, Any]) -> go.Figure:
        """
        Builds a comparative grouped bar chart comparing episode counts and average severity
        between Period A and Period B.
        """
        p_a = comparison["period_a"]
        p_b = comparison["period_b"]

        fig = go.Figure()

        categories = ["Episodes Recorded", "Avg Severity (1–10)"]
        val_a = [
            p_a["metrics"]["symptom_episodes"],
            p_a["metrics"]["avg_severity"] or 0
        ]
        val_b = [
            p_b["metrics"]["symptom_episodes"],
            p_b["metrics"]["avg_severity"] or 0
        ]

        fig.add_trace(go.Bar(
            name=p_a["label"],
            x=categories,
            y=val_a,
            marker_color="#B95F7B",
            text=[str(v) if v else "0" for v in val_a],
            textposition="auto"
        ))

        fig.add_trace(go.Bar(
            name=p_b["label"],
            x=categories,
            y=val_b,
            marker_color="#7E5265",
            text=[str(v) if v else "0" for v in val_b],
            textposition="auto"
        ))

        fig.update_layout(
            barmode="group",
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFF9F8",
            margin=dict(l=15, r=15, t=30, b=25),
            height=260,
            font=dict(family="Plus Jakarta Sans, sans-serif", size=11, color="#34272E"),
            xaxis=dict(title=None, showgrid=False),
            yaxis=dict(title=None, showgrid=True, gridcolor="#F0DFE6"),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(size=10)
            )
        )

        return fig

    @staticmethod
    def create_contextual_cooccurrence_chart(events: List[TimelineEvent]) -> Optional[go.Figure]:
        """
        Creates an exploratory contextual co-occurrence breakdown comparing symptom severity
        across sleep quality tiers or stress ratings.
        Only generates when at least 3 entries have sleep/stress data.
        """
        symptom_events = [
            e for e in events
            if e.event_type == "symptom" and e.severity is not None and e.context.get("sleep")
        ]

        if len(symptom_events) < 3:
            fig = go.Figure()
            fig.add_annotation(
                text="Insufficient contextual sleep observations recorded (< 3 entries).",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=12, color="#8A7A83", family="Plus Jakarta Sans")
            )
            fig.update_layout(
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFF9F8",
                height=220,
                margin=dict(l=15, r=15, t=30, b=25)
            )
            return fig

        records = []
        for e in symptom_events:
            records.append({
                "sleep": e.context.get("sleep", "Unspecified"),
                "severity": e.severity,
                "symptom": e.title
            })

        df = pd.DataFrame(records)
        grouped = df.groupby("sleep", as_index=False)["severity"].agg(["mean", "count"]).reset_index()
        grouped["mean"] = grouped["mean"].round(1)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=grouped["sleep"],
            y=grouped["mean"],
            marker=dict(
                color=["#FAD0DD" if "Restful" in str(s) else "#B95F7B" for s in grouped["sleep"]],
                line=dict(color="#34272E", width=1)
            ),
            text=[f"Avg: {m}/10 (n={c})" for m, c in zip(grouped["mean"], grouped["count"])],
            textposition="auto"
        ))

        fig.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFF9F8",
            margin=dict(l=15, r=15, t=30, b=25),
            height=250,
            font=dict(family="Plus Jakarta Sans, sans-serif", size=11, color="#34272E"),
            xaxis=dict(title=None, showgrid=False, tickangle=-10),
            yaxis=dict(title="Average Severity (1–10)", range=[0, 10.5], showgrid=True, gridcolor="#F0DFE6"),
            title=dict(
                text="Mean Symptom Severity by Reported Sleep Context",
                font=dict(size=12, color="#34272E")
            )
        )

        return fig
