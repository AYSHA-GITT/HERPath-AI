"""
HERPath AI - Smart Clinical Summary Service
recHERsion 2026 | PS1: Women's Healthcare

Deterministic, privacy-preserving consultation intelligence engine.
Synthesizes actual database health records into structured, doctor-ready
clinical summaries. Adheres strictly to non-diagnostic boundaries, transparent
calculations, and clinical communication best practices.
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

from models import SymptomEntry, MedicationEntry, UserProfile
from database import get_symptoms, get_medications, get_profile
from config import APP_TITLE, CLINICAL_DISCLAIMER


@dataclass
class SymptomFrequencyItem:
    """Frequency and severity statistics for a single recorded symptom."""
    symptom: str
    category: str
    entry_count: int
    distinct_days: int
    percentage_of_entries: float
    avg_severity: float
    min_severity: int
    max_severity: int
    avg_duration: Optional[float] = None


@dataclass
class HighSeverityEpisode:
    """Notable episode with high severity (>=7/10) or significant functional impact."""
    symptom: str
    category: str
    date: str
    time: Optional[str]
    severity: int
    duration_hours: Optional[float]
    impact: str
    notes: str


@dataclass
class RepeatedSevereSymptom:
    """Symptom with repeated high severity (>=7/10) across distinct entries."""
    symptom: str
    category: str
    count_severe: int
    max_severity: int
    dates: List[str]


@dataclass
class SeverityProgression:
    """Temporal severity comparison between earlier and recent observation windows."""
    comparison_possible: bool
    earlier_start: Optional[str] = None
    earlier_end: Optional[str] = None
    recent_start: Optional[str] = None
    recent_end: Optional[str] = None
    earlier_entries: int = 0
    recent_entries: int = 0
    earlier_avg_severity: Optional[float] = None
    recent_avg_severity: Optional[float] = None
    severity_delta: Optional[float] = None
    trajectory_statement: str = "Insufficient observations to compare earlier vs recent periods."


@dataclass
class DurationStatistics:
    """Duration summary handling missing values safely without casting nulls to zero."""
    documented_entries: int
    total_entries: int
    documentation_rate: float
    mean_hours: Optional[float] = None
    min_hours: Optional[float] = None
    max_hours: Optional[float] = None
    summary_statement: str = "Duration was not documented in any entries during this period."


@dataclass
class DimensionBreakdown:
    """Documented vs unrecorded breakdown for a lifestyle or functional dimension."""
    dimension_name: str
    documented_entries: int
    total_entries: int
    documentation_rate: float
    counts_by_category: Dict[str, int] = field(default_factory=dict)
    summary_statement: str = ""


@dataclass
class LifestyleFunctionalSummary:
    """Structured lifestyle and functional impact context."""
    sleep: DimensionBreakdown
    stress: DimensionBreakdown
    energy: DimensionBreakdown
    cycle_phase: DimensionBreakdown
    functional_impact: DimensionBreakdown
    work_study_disruption_count: int = 0
    bedrest_count: int = 0


@dataclass
class TreatmentObservation:
    """Medication / treatment record with temporal before/after observation comparison."""
    name: str
    category: str
    dosage: str
    frequency: str
    started_date: Optional[str]
    notes: str
    is_started_in_period: bool
    has_comparison_data: bool
    before_window_days: int
    after_window_days: int
    before_entries_count: int
    after_entries_count: int
    before_avg_severity: Optional[float]
    after_avg_severity: Optional[float]
    observation_statement: str


@dataclass
class DoctorDiscussionChecklist:
    """Doctor-friendly checklist categorized for efficient 10-15 min consultations."""
    symptoms_to_discuss: List[str] = field(default_factory=list)
    changes_noticed: List[str] = field(default_factory=list)
    effects_on_daily_activities: List[str] = field(default_factory=list)
    medication_questions: List[str] = field(default_factory=list)
    questions_for_clinician: List[str] = field(default_factory=list)


@dataclass
class ClinicalSummaryData:
    """Unified data model encapsulating the complete Smart Clinical Summary."""
    profile_id: str
    patient_name: str
    start_date: str
    end_date: str
    calendar_days: int
    generated_at: str
    total_entries: int
    distinct_days: int
    avg_severity: Optional[float]
    max_severity: Optional[int]
    max_severity_symptom: Optional[str]
    max_severity_date: Optional[str]
    frequent_symptoms: List[SymptomFrequencyItem]
    progression: SeverityProgression
    repeated_severe: List[RepeatedSevereSymptom]
    notable_episodes: List[HighSeverityEpisode]
    duration_stats: DurationStatistics
    lifestyle_impact: LifestyleFunctionalSummary
    treatments: List[TreatmentObservation]
    patient_concerns: List[str]
    checklist: DoctorDiscussionChecklist
    data_limitations: List[str]


class ClinicalSummaryService:
    """
    On-device clinical intelligence service generating structured, non-diagnostic
    health summaries from actual SQLite records.
    """

    def __init__(
        self,
        profile_id: str,
        start_date: str,
        end_date: str,
        patient_concerns: Optional[List[str]] = None,
        entries: Optional[List[SymptomEntry]] = None,
        medications: Optional[List[MedicationEntry]] = None,
        profile: Optional[UserProfile] = None,
        all_symptoms: Optional[List[SymptomEntry]] = None,
        db_path: Optional[str] = None
    ):
        self.profile_id = profile_id
        self.start_date = str(start_date)
        self.end_date = str(end_date)
        self.patient_concerns = [c.strip() for c in (patient_concerns or []) if c and c.strip()]
        self.db_path = db_path

        # 1. Profile retrieval (isolated)
        if profile is not None:
            self.profile = profile
        else:
            self.profile = get_profile(self.profile_id, db_path=self.db_path)
        self.patient_name = self.profile.display_name if self.profile else self.profile_id

        # 2. Raw records strictly scoped to profile_id and date boundaries
        if entries is not None:
            self.entries = [
                e for e in entries
                if e.onset_date and self.start_date <= e.onset_date <= self.end_date
            ]
        else:
            self.entries = get_symptoms(
                profile_id=self.profile_id,
                start_date=self.start_date,
                end_date=self.end_date,
                db_path=self.db_path
            )

        if medications is not None:
            self.medications = medications
        else:
            self.medications = get_medications(
                profile_id=self.profile_id,
                db_path=self.db_path
            )

        # 3. All symptoms for full profile history (used for medication before/after analysis)
        if all_symptoms is not None:
            self._all_profile_symptoms = all_symptoms
        elif entries is not None:
            self._all_profile_symptoms = entries
        else:
            self._all_profile_symptoms = None

    def _get_all_symptoms(self) -> List[SymptomEntry]:
        if self._all_profile_symptoms is None:
            self._all_profile_symptoms = get_symptoms(
                profile_id=self.profile_id,
                db_path=self.db_path
            )
        return self._all_profile_symptoms

    def generate_summary(self) -> ClinicalSummaryData:
        """
        Executes deterministic calculations and returns the structured ClinicalSummaryData.
        """
        gen_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Parse date range
        try:
            d_start = datetime.strptime(self.start_date, "%Y-%m-%d").date()
            d_end = datetime.strptime(self.end_date, "%Y-%m-%d").date()
            calendar_days = max(1, (d_end - d_start).days + 1)
        except Exception:
            calendar_days = 1

        total_entries = len(self.entries)
        distinct_days = len(set(e.onset_date for e in self.entries if e.onset_date))

        # Overall severity
        severities = [e.severity for e in self.entries if e.severity is not None]
        avg_severity = round(float(np.mean(severities)), 1) if severities else None

        # Max severity & date
        max_severity = None
        max_severity_symptom = None
        max_severity_date = None
        if severities:
            max_severity = max(severities)
            for e in self.entries:
                if e.severity == max_severity:
                    max_severity_symptom = e.symptom
                    max_severity_date = e.onset_date
                    break

        # A. Frequent symptoms & breakdown
        frequent_symptoms = self._calculate_frequent_symptoms()

        # B. Symptom progression earlier vs recent
        progression = self._calculate_severity_progression()

        # B. Repeated severe symptoms (>=7/10)
        repeated_severe = self._calculate_repeated_severe()

        # B. Notable recorded episodes
        notable_episodes = self._calculate_notable_episodes()

        # B. Duration statistics
        duration_stats = self._calculate_duration_statistics()

        # C. Lifestyle & functional impact
        lifestyle_impact = self._calculate_lifestyle_impact()

        # D. Medication and treatment history with neutral before/after comparison
        treatments = self._calculate_treatment_history()

        # F. Doctor discussion checklist
        checklist = self._generate_discussion_checklist(
            frequent_symptoms=frequent_symptoms,
            repeated_severe=repeated_severe,
            progression=progression,
            lifestyle_impact=lifestyle_impact,
            treatments=treatments
        )

        # Data limitations & disclaimers
        data_limitations = [
            f"Summary covers {calendar_days} calendar days ({self.start_date} to {self.end_date}).",
            f"Contains {total_entries} patient-recorded entries across {distinct_days} distinct days.",
            "Unrecorded symptoms or omitted dates cannot be inferred as clinically absent.",
            "Medication adherence is not tracked; records indicate logged start dates only.",
            "Temporal observations indicate co-occurrence and do not prove physiological causation.",
            "This summary is strictly educational and non-diagnostic; review all findings with a licensed healthcare provider."
        ]

        return ClinicalSummaryData(
            profile_id=self.profile_id,
            patient_name=self.patient_name,
            start_date=self.start_date,
            end_date=self.end_date,
            calendar_days=calendar_days,
            generated_at=gen_timestamp,
            total_entries=total_entries,
            distinct_days=distinct_days,
            avg_severity=avg_severity,
            max_severity=max_severity,
            max_severity_symptom=max_severity_symptom,
            max_severity_date=max_severity_date,
            frequent_symptoms=frequent_symptoms,
            progression=progression,
            repeated_severe=repeated_severe,
            notable_episodes=notable_episodes,
            duration_stats=duration_stats,
            lifestyle_impact=lifestyle_impact,
            treatments=treatments,
            patient_concerns=self.patient_concerns,
            checklist=checklist,
            data_limitations=data_limitations
        )

    # ==========================================
    # Calculations & Section Builders
    # ==========================================

    def _calculate_frequent_symptoms(self) -> List[SymptomFrequencyItem]:
        """Calculates frequency, distinct days, and severity metrics for each symptom."""
        if not self.entries:
            return []

        sym_groups: Dict[str, List[SymptomEntry]] = {}
        for e in self.entries:
            sym_groups.setdefault(e.symptom, []).append(e)

        total_entries = len(self.entries)
        items: List[SymptomFrequencyItem] = []

        for sym_name, group in sym_groups.items():
            entry_count = len(group)
            distinct_days = len(set(e.onset_date for e in group if e.onset_date))
            pct = round((entry_count / total_entries) * 100, 1)

            sevs = [e.severity for e in group if e.severity is not None]
            avg_sev = round(float(np.mean(sevs)), 1) if sevs else 0.0
            min_sev = min(sevs) if sevs else 0
            max_sev = max(sevs) if sevs else 0

            durs = [e.duration_hours for e in group if e.duration_hours is not None]
            avg_dur = round(float(np.mean(durs)), 1) if durs else None

            cat = group[0].category if group else "General"

            items.append(SymptomFrequencyItem(
                symptom=sym_name,
                category=cat,
                entry_count=entry_count,
                distinct_days=distinct_days,
                percentage_of_entries=pct,
                avg_severity=avg_sev,
                min_severity=min_sev,
                max_severity=max_sev,
                avg_duration=avg_dur
            ))

        # Sort by entry count descending, then avg severity descending
        items.sort(key=lambda x: (x.entry_count, x.avg_severity), reverse=True)
        return items

    def _calculate_severity_progression(self) -> SeverityProgression:
        """
        Compares severity in earlier vs recent window of the reporting period.
        Splits calendar range into two equal halves.
        """
        if len(self.entries) < 2:
            return SeverityProgression(
                comparison_possible=False,
                trajectory_statement="Insufficient entries to calculate a period-over-period severity comparison."
            )

        try:
            d_start = datetime.strptime(self.start_date, "%Y-%m-%d").date()
            d_end = datetime.strptime(self.end_date, "%Y-%m-%d").date()
            total_days = (d_end - d_start).days
            if total_days < 1:
                return SeverityProgression(
                    comparison_possible=False,
                    trajectory_statement="Reporting period is too short (1 day) for earlier vs recent period comparison."
                )

            half_days = total_days // 2
            mid_date = d_start + timedelta(days=half_days)
            earlier_end_date = mid_date
            recent_start_date = mid_date + timedelta(days=1)

            earlier_entries = [
                e for e in self.entries
                if e.onset_date and e.onset_date <= str(earlier_end_date)
            ]
            recent_entries = [
                e for e in self.entries
                if e.onset_date and e.onset_date >= str(recent_start_date)
            ]

            if not earlier_entries or not recent_entries:
                return SeverityProgression(
                    comparison_possible=False,
                    earlier_start=str(d_start),
                    earlier_end=str(earlier_end_date),
                    recent_start=str(recent_start_date),
                    recent_end=str(d_end),
                    earlier_entries=len(earlier_entries),
                    recent_entries=len(recent_entries),
                    trajectory_statement=(
                        f"Records are clustered primarily in one window ({len(earlier_entries)} earlier vs "
                        f"{len(recent_entries)} recent), precluding a balanced severity comparison."
                    )
                )

            e_sevs = [e.severity for e in earlier_entries if e.severity is not None]
            r_sevs = [e.severity for e in recent_entries if e.severity is not None]

            e_avg = round(float(np.mean(e_sevs)), 1) if e_sevs else None
            r_avg = round(float(np.mean(r_sevs)), 1) if r_sevs else None

            delta = round(r_avg - e_avg, 1) if (r_avg is not None and e_avg is not None) else None

            if delta is not None:
                if delta >= 1.0:
                    trend_desc = f"an increase of +{delta} points in recorded severity"
                elif delta <= -1.0:
                    trend_desc = f"a decrease of {abs(delta)} points in recorded severity"
                else:
                    trend_desc = "a relatively stable severity pattern (within ±1.0 point)"

                stmt = (
                    f"Earlier observation period ({d_start} to {earlier_end_date}) recorded {len(earlier_entries)} entries "
                    f"with average severity {e_avg}/10. Recent observation period ({recent_start_date} to {d_end}) recorded "
                    f"{len(recent_entries)} entries with average severity {r_avg}/10, reflecting {trend_desc}."
                )
            else:
                stmt = "Missing severity ratings precluded delta calculation."

            return SeverityProgression(
                comparison_possible=True,
                earlier_start=str(d_start),
                earlier_end=str(earlier_end_date),
                recent_start=str(recent_start_date),
                recent_end=str(d_end),
                earlier_entries=len(earlier_entries),
                recent_entries=len(recent_entries),
                earlier_avg_severity=e_avg,
                recent_avg_severity=r_avg,
                severity_delta=delta,
                trajectory_statement=stmt
            )
        except Exception:
            return SeverityProgression(
                comparison_possible=False,
                trajectory_statement="Could not compute period progression due to date formatting."
            )

    def _calculate_repeated_severe(self) -> List[RepeatedSevereSymptom]:
        """Identifies symptoms that reached high severity (>=7/10) in 2 or more entries."""
        if not self.entries:
            return []

        severe_by_sym: Dict[str, List[SymptomEntry]] = {}
        for e in self.entries:
            if e.severity is not None and e.severity >= 7:
                severe_by_sym.setdefault(e.symptom, []).append(e)

        results: List[RepeatedSevereSymptom] = []
        for sym, group in severe_by_sym.items():
            if len(group) >= 2:
                cat = group[0].category
                dates = sorted(list(set(e.onset_date for e in group if e.onset_date)))
                max_s = max(e.severity for e in group if e.severity is not None)
                results.append(RepeatedSevereSymptom(
                    symptom=sym,
                    category=cat,
                    count_severe=len(group),
                    max_severity=max_s,
                    dates=dates
                ))

        results.sort(key=lambda x: (x.count_severe, x.max_severity), reverse=True)
        return results

    def _calculate_notable_episodes(self) -> List[HighSeverityEpisode]:
        """Finds notable episodes with severity >= 8 or severe functional impact."""
        notable: List[HighSeverityEpisode] = []
        for e in self.entries:
            is_high_sev = e.severity is not None and e.severity >= 8
            is_high_impact = bool(e.impact and any(w in e.impact.lower() for w in ["bedrest", "severe", "inability", "incapacitated"]))
            if is_high_sev or is_high_impact:
                notable.append(HighSeverityEpisode(
                    symptom=e.symptom,
                    category=e.category,
                    date=e.onset_date,
                    time=e.onset_time,
                    severity=e.severity,
                    duration_hours=e.duration_hours,
                    impact=e.impact or "None",
                    notes=e.notes or ""
                ))

        # Sort by date descending
        notable.sort(key=lambda x: (x.date, x.severity), reverse=True)
        return notable

    def _calculate_duration_statistics(self) -> DurationStatistics:
        """Calculates duration statistics without treating missing values as zero."""
        total = len(self.entries)
        if total == 0:
            return DurationStatistics(
                documented_entries=0,
                total_entries=0,
                documentation_rate=0.0,
                summary_statement="No symptom records logged in selected period."
            )

        dur_entries = [e.duration_hours for e in self.entries if e.duration_hours is not None]
        documented_count = len(dur_entries)
        rate = round((documented_count / total) * 100, 1)

        if documented_count == 0:
            return DurationStatistics(
                documented_entries=0,
                total_entries=total,
                documentation_rate=0.0,
                mean_hours=None,
                min_hours=None,
                max_hours=None,
                summary_statement=f"Duration was not documented in any of the {total} symptom entries (0.0%)."
            )

        mean_h = round(float(np.mean(dur_entries)), 1)
        min_h = round(float(min(dur_entries)), 1)
        max_h = round(float(max(dur_entries)), 1)

        stmt = (
            f"Duration was documented in {documented_count} of {total} symptom entries ({rate}%). "
            f"Average episode duration was {mean_h} hours (range: {min_h} to {max_h} hours). "
            f"{total - documented_count} entries omitted duration."
        )

        return DurationStatistics(
            documented_entries=documented_count,
            total_entries=total,
            documentation_rate=rate,
            mean_hours=mean_h,
            min_hours=min_h,
            max_hours=max_h,
            summary_statement=stmt
        )

    def _calculate_lifestyle_impact(self) -> LifestyleFunctionalSummary:
        """
        Summarizes sleep, stress, energy, cycle phase, and functional impact.
        Transparently separates documented counts from missing counts.
        """
        total = len(self.entries)
        if total == 0:
            empty_bd = lambda name: DimensionBreakdown(name, 0, 0, 0.0, {}, f"No {name} data recorded.")
            return LifestyleFunctionalSummary(
                sleep=empty_bd("Sleep"),
                stress=empty_bd("Stress"),
                energy=empty_bd("Energy"),
                cycle_phase=empty_bd("Cycle Phase"),
                functional_impact=empty_bd("Functional Impact")
            )

        # 1. Sleep
        sleep_vals = [e.context.get("sleep") for e in self.entries if e.context and e.context.get("sleep")]
        sleep_counts = pd.Series(sleep_vals).value_counts().to_dict() if sleep_vals else {}
        sleep_doc = len(sleep_vals)
        sleep_rate = round((sleep_doc / total) * 100, 1)
        sleep_stmt = (
            f"Sleep quality was documented in {sleep_doc} of {total} entries ({sleep_rate}%). "
            + (f"Reported: {', '.join(f'{k}: {v}' for k, v in sleep_counts.items())}." if sleep_counts else "No sleep entries.")
            + (f" ({total - sleep_doc} entries unrecorded)." if total > sleep_doc else "")
        )
        sleep_bd = DimensionBreakdown("Sleep Quality", sleep_doc, total, sleep_rate, sleep_counts, sleep_stmt)

        # 2. Stress
        stress_vals = [e.context.get("stress") for e in self.entries if e.context and e.context.get("stress")]
        stress_counts = pd.Series(stress_vals).value_counts().to_dict() if stress_vals else {}
        stress_doc = len(stress_vals)
        stress_rate = round((stress_doc / total) * 100, 1)
        stress_stmt = (
            f"Stress level was documented in {stress_doc} of {total} entries ({stress_rate}%). "
            + (f"Reported: {', '.join(f'{k}: {v}' for k, v in stress_counts.items())}." if stress_counts else "No stress entries.")
            + (f" ({total - stress_doc} entries unrecorded)." if total > stress_doc else "")
        )
        stress_bd = DimensionBreakdown("Stress Levels", stress_doc, total, stress_rate, stress_counts, stress_stmt)

        # 3. Energy
        energy_vals = [e.context.get("energy") for e in self.entries if e.context and e.context.get("energy")]
        energy_counts = pd.Series(energy_vals).value_counts().to_dict() if energy_vals else {}
        energy_doc = len(energy_vals)
        energy_rate = round((energy_doc / total) * 100, 1)
        energy_stmt = (
            f"Energy level was documented in {energy_doc} of {total} entries ({energy_rate}%). "
            + (f"Reported: {', '.join(f'{k}: {v}' for k, v in energy_counts.items())}." if energy_counts else "No energy entries.")
            + (f" ({total - energy_doc} entries unrecorded)." if total > energy_doc else "")
        )
        energy_bd = DimensionBreakdown("Energy Vitality", energy_doc, total, energy_rate, energy_counts, energy_stmt)

        # 4. Cycle Phase
        cycle_vals = [
            e.context.get("cycle_phase") for e in self.entries
            if e.context and e.context.get("cycle_phase") and e.context.get("cycle_phase") != "Not tracking / NA"
        ]
        cycle_counts = pd.Series(cycle_vals).value_counts().to_dict() if cycle_vals else {}
        cycle_doc = len(cycle_vals)
        cycle_rate = round((cycle_doc / total) * 100, 1)
        cycle_stmt = (
            f"Cycle phase was documented in {cycle_doc} of {total} entries ({cycle_rate}%). "
            + (f"Reported: {', '.join(f'{k}: {v}' for k, v in cycle_counts.items())}." if cycle_counts else "Cycle tracking not logged.")
            + (f" ({total - cycle_doc} entries unrecorded or non-tracking)." if total > cycle_doc else "")
        )
        cycle_bd = DimensionBreakdown("Menstrual Cycle Context", cycle_doc, total, cycle_rate, cycle_counts, cycle_stmt)

        # 5. Functional Impact
        impact_vals = [e.impact for e in self.entries if e.impact and e.impact != "None"]
        impact_counts = pd.Series(impact_vals).value_counts().to_dict() if impact_vals else {}
        impact_doc = len(impact_vals)
        impact_rate = round((impact_doc / total) * 100, 1)

        # Count specific activity disruption
        work_study_count = sum(
            1 for e in self.entries
            if e.impact and any(k in e.impact.lower() for k in ["work", "study", "bedrest", "severe", "incapacitated", "plans", "moderate"])
        )
        bedrest_count = sum(
            1 for e in self.entries
            if e.impact and any(k in e.impact.lower() for k in ["bedrest", "incapacitated"])
        )

        impact_stmt = (
            f"Daily functional impact was reported in {impact_doc} of {total} entries ({impact_rate}%). "
            f"{work_study_count} entries noted disruption to work, study, or daily routines; "
            f"{bedrest_count} entries noted bedrest or incapacitation."
        )
        impact_bd = DimensionBreakdown("Daily Activity & Functional Impact", impact_doc, total, impact_rate, impact_counts, impact_stmt)

        return LifestyleFunctionalSummary(
            sleep=sleep_bd,
            stress=stress_bd,
            energy=energy_bd,
            cycle_phase=cycle_bd,
            functional_impact=impact_bd,
            work_study_disruption_count=work_study_count,
            bedrest_count=bedrest_count
        )

    def _calculate_treatment_history(self) -> List[TreatmentObservation]:
        """
        Analyzes recorded medications and treatments.
        For treatments with recorded start dates, calculates 14-day before vs after
        symptom severity observations using strictly non-causal phrasing.
        """
        if not self.medications:
            return []

        all_syms = self._get_all_symptoms()
        observations: List[TreatmentObservation] = []

        for m in self.medications:
            is_in_period = False
            has_comparison = False
            before_count = 0
            after_count = 0
            before_avg: Optional[float] = None
            after_avg: Optional[float] = None
            stmt = "No start date recorded for temporal before/after comparison."

            if m.started_date:
                try:
                    start_dt = datetime.strptime(m.started_date, "%Y-%m-%d").date()
                    # Check if started within reporting period
                    if self.start_date <= m.started_date <= self.end_date:
                        is_in_period = True

                    # 14-day observation windows
                    w_before_start = start_dt - timedelta(days=14)
                    w_before_end = start_dt - timedelta(days=1)
                    w_after_start = start_dt
                    w_after_end = start_dt + timedelta(days=14)

                    before_entries = [
                        e for e in all_syms
                        if e.onset_date and str(w_before_start) <= e.onset_date <= str(w_before_end)
                    ]
                    after_entries = [
                        e for e in all_syms
                        if e.onset_date and str(w_after_start) <= e.onset_date <= str(w_after_end)
                    ]

                    before_count = len(before_entries)
                    after_count = len(after_entries)

                    b_sevs = [e.severity for e in before_entries if e.severity is not None]
                    a_sevs = [e.severity for e in after_entries if e.severity is not None]

                    before_avg = round(float(np.mean(b_sevs)), 1) if b_sevs else None
                    after_avg = round(float(np.mean(a_sevs)), 1) if a_sevs else None

                    if before_count > 0 and after_count > 0 and before_avg is not None and after_avg is not None:
                        has_comparison = True
                        if after_avg < before_avg:
                            rel_text = f"lower in the subsequent observation period ({after_avg}/10 across {after_count} entries vs. {before_avg}/10 across {before_count} entries prior)"
                        elif after_avg > before_avg:
                            rel_text = f"higher in the subsequent observation period ({after_avg}/10 across {after_count} entries vs. {before_avg}/10 across {before_count} entries prior)"
                        else:
                            rel_text = f"similar across both observation periods ({after_avg}/10 across {after_count} entries vs. {before_avg}/10 across {before_count} entries prior)"

                        stmt = (
                            f"Symptom severity was recorded as {rel_text} within 14 days of starting {m.name}. "
                            f"Explicit notice: Timing alone does not establish causation or treatment efficacy."
                        )
                    elif before_count > 0 and after_count == 0:
                        stmt = f"{before_count} symptom entries recorded in the 14 days prior (average severity {before_avg}/10); no entries recorded in subsequent 14 days."
                    elif before_count == 0 and after_count > 0:
                        stmt = f"{after_count} symptom entries recorded in the 14 days after starting (average severity {after_avg}/10); no entries recorded in the 14 days prior."
                    else:
                        stmt = "No symptom entries were recorded in the 14-day window immediately before or after initiation."

                except Exception:
                    stmt = "Could not parse start date for temporal window calculation."

            observations.append(TreatmentObservation(
                name=m.name,
                category=m.category,
                dosage=m.dosage or "Not specified",
                frequency=m.frequency or "As directed",
                started_date=m.started_date,
                notes=m.notes or "",
                is_started_in_period=is_in_period,
                has_comparison_data=has_comparison,
                before_window_days=14,
                after_window_days=14,
                before_entries_count=before_count,
                after_entries_count=after_count,
                before_avg_severity=before_avg,
                after_avg_severity=after_avg,
                observation_statement=stmt
            ))

        return observations

    def _generate_discussion_checklist(
        self,
        frequent_symptoms: List[SymptomFrequencyItem],
        repeated_severe: List[RepeatedSevereSymptom],
        progression: SeverityProgression,
        lifestyle_impact: LifestyleFunctionalSummary,
        treatments: List[TreatmentObservation]
    ) -> DoctorDiscussionChecklist:
        """
        Generates a practical, doctor-ready discussion checklist based on user concerns
        and actual database records.
        """
        # 1. Symptoms to discuss
        symptoms_prompts = []
        if frequent_symptoms:
            top_3 = frequent_symptoms[:3]
            for s in top_3:
                dur_note = f", duration avg {s.avg_duration}h" if s.avg_duration else ""
                symptoms_prompts.append(
                    f"Frequent symptom: {s.symptom} — recorded {s.entry_count} times across {s.distinct_days} days (avg severity {s.avg_severity}/10{dur_note})."
                )

        if repeated_severe:
            for rs in repeated_severe[:2]:
                symptoms_prompts.append(
                    f"Repeated severe episodes (≥7/10): {rs.symptom} — peaked at {rs.max_severity}/10 across {rs.count_severe} entries on {', '.join(rs.dates[:3])}."
                )

        if not symptoms_prompts:
            symptoms_prompts.append("No recurrent symptom clusters met frequency thresholds during this period.")

        # 2. Changes noticed
        changes_prompts = []
        if progression.comparison_possible:
            changes_prompts.append(progression.trajectory_statement)
        else:
            changes_prompts.append("Documented observations over this period to establish personal symptom baseline.")

        if lifestyle_impact.sleep.documented_entries >= 2:
            disrupted_count = sum(v for k, v in lifestyle_impact.sleep.counts_by_category.items() if any(w in k.lower() for w in ["disrupt", "insomnia", "poor"]))
            if disrupted_count >= 2:
                changes_prompts.append(f"Sleep disruption documented in {disrupted_count} entries during this period.")

        if lifestyle_impact.cycle_phase.documented_entries >= 2:
            top_phase = max(lifestyle_impact.cycle_phase.counts_by_category.items(), key=lambda x: x[1])[0]
            changes_prompts.append(f"Symptom clustering observed primarily during the {top_phase} cycle phase.")

        # 3. Effects on daily activities
        impact_prompts = []
        if lifestyle_impact.work_study_disruption_count > 0:
            impact_prompts.append(
                f"{lifestyle_impact.work_study_disruption_count} entries documented interference with work, study, or social plans."
            )
        if lifestyle_impact.bedrest_count > 0:
            impact_prompts.append(
                f"{lifestyle_impact.bedrest_count} entries required bedrest or physical incapacitation."
            )
        if not impact_prompts:
            impact_prompts.append("No severe functional disruptions were explicitly documented during this period.")

        # 4. Medication or treatment questions
        med_prompts = []
        if treatments:
            for t in treatments[:3]:
                start_txt = f"started {t.started_date}" if t.started_date else "start date not recorded"
                med_prompts.append(
                    f"Review {t.name} ({t.dosage}, {t.frequency}; {start_txt}): discuss efficacy, side effects, and ongoing appropriateness."
                )
        else:
            med_prompts.append("Discuss whether evidence-based pharmacological or non-pharmacological interventions are recommended.")

        # 5. Questions for clinician
        clinician_prompts = []
        # Include patient concerns first
        if self.patient_concerns:
            for pc in self.patient_concerns:
                clinician_prompts.append(f"[Patient Consultation Goal]: {pc}")

        # Clinician evidence questions
        clinician_prompts.extend([
            "Based on the frequency and severity patterns recorded, what diagnostic evaluations (such as hormonal panel, CBC, ferritin, pelvic ultrasound) would you recommend?",
            "What evidence-based management strategies (pharmacological, lifestyle, nutritional) can reduce the intensity of peak episodes?",
            "What specific warning symptoms or red flags should prompt immediate or emergency medical care?"
        ])

        return DoctorDiscussionChecklist(
            symptoms_to_discuss=symptoms_prompts,
            changes_noticed=changes_prompts,
            effects_on_daily_activities=impact_prompts,
            medication_questions=med_prompts,
            questions_for_clinician=clinician_prompts
        )

    # ==========================================
    # Text / Markdown Formatter (for Copy to Clipboard)
    # ==========================================

    def generate_plain_text_summary(self) -> str:
        """
        Generates a clean, copyable text summary structured for clinical communication.
        """
        s = self.generate_summary()
        lines = []

        lines.append(f"===========================================================")
        lines.append(f"  HERPath AI — Smart Clinical Consultation Summary")
        lines.append(f"===========================================================")
        lines.append(f"Patient / Profile Alias: {s.patient_name}")
        lines.append(f"Reporting Period: {s.start_date} to {s.end_date} ({s.calendar_days} calendar days)")
        lines.append(f"Generated On: {s.generated_at}")
        lines.append(f"Data Basis: {s.total_entries} recorded entries across {s.distinct_days} distinct days")
        lines.append("")

        if s.patient_concerns:
            lines.append("--- PATIENT'S MAIN CONSULTATION PRIORITIES ---")
            for c in s.patient_concerns:
                lines.append(f"• {c}")
            lines.append("")

        lines.append("--- 1. CONSULTATION OVERVIEW ---")
        lines.append(f"• Total Logged Entries: {s.total_entries}")
        lines.append(f"• Distinct Logged Days: {s.distinct_days} of {s.calendar_days} days")
        lines.append(f"• Average Recorded Severity: {s.avg_severity or 'N/A'}/10")
        if s.max_severity:
            lines.append(f"• Peak Recorded Severity: {s.max_severity}/10 for '{s.max_severity_symptom}' on {s.max_severity_date}")
        lines.append(f"• {s.duration_stats.summary_statement}")
        lines.append("")

        lines.append("--- 2. SYMPTOM PATTERNS & FREQUENCY ---")
        if s.frequent_symptoms:
            for fs in s.frequent_symptoms:
                dur_text = f", avg dur: {fs.avg_duration}h" if fs.avg_duration else ""
                lines.append(
                    f"• {fs.symptom} ({fs.category}): {fs.entry_count} entries ({fs.percentage_of_entries}% of logs) "
                    f"across {fs.distinct_days} days | Severity: avg {fs.avg_severity}/10 (range {fs.min_severity}-{fs.max_severity}){dur_text}"
                )
        else:
            lines.append("• No symptoms recorded in this period.")

        if s.repeated_severe:
            lines.append("")
            lines.append("Repeated High-Severity Episodes (≥7/10):")
            for rs in s.repeated_severe:
                lines.append(f"  - {rs.symptom}: {rs.count_severe} severe entries (Peak: {rs.max_severity}/10) on {', '.join(rs.dates)}")

        lines.append("")
        lines.append(f"Severity Trajectory Observation:")
        lines.append(f"  {s.progression.trajectory_statement}")
        lines.append("")

        lines.append("--- 3. LIFESTYLE CONTEXT & FUNCTIONAL IMPACT ---")
        lines.append(f"• Sleep: {s.lifestyle_impact.sleep.summary_statement}")
        lines.append(f"• Stress: {s.lifestyle_impact.stress.summary_statement}")
        lines.append(f"• Energy: {s.lifestyle_impact.energy.summary_statement}")
        lines.append(f"• Cycle Phase: {s.lifestyle_impact.cycle_phase.summary_statement}")
        lines.append(f"• Functional Disruption: {s.lifestyle_impact.functional_impact.summary_statement}")
        lines.append("")

        lines.append("--- 4. MEDICATION & TREATMENT HISTORY ---")
        if s.treatments:
            for t in s.treatments:
                st_date = t.started_date or "Not specified"
                lines.append(f"• {t.name} ({t.category}) | Dosage: {t.dosage} | Freq: {t.frequency} | Started: {st_date}")
                lines.append(f"  Observation Note: {t.observation_statement}")
        else:
            lines.append("• No medications or treatments recorded in database.")
        lines.append("")

        lines.append("--- 5. DOCTOR DISCUSSION CHECKLIST ---")
        lines.append("A. Symptoms to Discuss:")
        for item in s.checklist.symptoms_to_discuss:
            lines.append(f"   [ ] {item}")
        lines.append("B. Changes Noticed:")
        for item in s.checklist.changes_noticed:
            lines.append(f"   [ ] {item}")
        lines.append("C. Daily Functional Effects:")
        for item in s.checklist.effects_on_daily_activities:
            lines.append(f"   [ ] {item}")
        lines.append("D. Medication / Treatment Questions:")
        for item in s.checklist.medication_questions:
            lines.append(f"   [ ] {item}")
        lines.append("E. Questions for Clinician:")
        for item in s.checklist.questions_for_clinician:
            lines.append(f"   [ ] {item}")
        lines.append("")

        lines.append("--- DATA LIMITATIONS & CLINICAL DISCLAIMER ---")
        for lim in s.data_limitations:
            lines.append(f"• {lim}")
        lines.append(f"Clinical Disclaimer: {CLINICAL_DISCLAIMER}")
        lines.append("===========================================================")

        return "\n".join(lines)
