"""
HERPath AI - Personal Health Insights & Explainable Pattern Analytics
recHERsion 2026 | PS1: Women's Healthcare

Deterministic, explainable analytics engine grounded in actual database entries.
Does not predict or diagnose diseases. Identifies observable frequency,
severity trajectories, and contextual co-occurrences.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from models import SymptomEntry


class InsightsEngine:
    """Calculates statistics, produces Plotly charts, and generates explainable pattern summaries."""

    def __init__(self, entries: List[SymptomEntry]):
        self.entries = entries
        self.df = self._to_dataframe(entries)

    def _to_dataframe(self, entries: List[SymptomEntry]) -> pd.DataFrame:
        """Converts symptom entries to a structured Pandas DataFrame."""
        if not entries:
            return pd.DataFrame(columns=[
                "id", "profile_id", "category", "symptom", "onset_date",
                "onset_time", "severity", "duration_hours", "status",
                "impact", "notes", "sleep", "stress", "energy", "cycle_phase"
            ])

        records = []
        for e in entries:
            ctx = e.context or {}
            records.append({
                "id": e.id,
                "profile_id": e.profile_id,
                "category": e.category,
                "symptom": e.symptom,
                "onset_date": pd.to_datetime(e.onset_date).date() if e.onset_date else None,
                "onset_time": e.onset_time,
                "severity": e.severity,
                "duration_hours": e.duration_hours,
                "status": e.status,
                "impact": e.impact,
                "notes": e.notes,
                "sleep": ctx.get("sleep"),
                "stress": ctx.get("stress"),
                "energy": ctx.get("energy"),
                "cycle_phase": ctx.get("cycle_phase")
            })

        df = pd.DataFrame(records)
        df = df.sort_values(by="onset_date", ascending=True)
        return df

    def calculate_summary_metrics(self) -> Dict[str, Any]:
        """Calculates key health metrics from the loaded entries."""
        if self.df.empty:
            return {
                "total_entries": 0,
                "distinct_days": 0,
                "avg_severity": 0.0,
                "max_severity": 0,
                "max_severity_symptom": "None",
                "top_symptom": "None",
                "top_symptom_count": 0,
                "ongoing_count": 0,
                "resolved_count": 0,
                "avg_duration": None
            }

        total_entries = len(self.df)
        distinct_days = self.df["onset_date"].nunique()
        avg_severity = round(float(self.df["severity"].mean()), 1)
        max_idx = self.df["severity"].idxmax()
        max_severity = int(self.df.loc[max_idx, "severity"])
        max_severity_symptom = str(self.df.loc[max_idx, "symptom"])

        # Top symptoms
        symptom_counts = self.df["symptom"].value_counts()
        top_symptom = symptom_counts.index[0] if not symptom_counts.empty else "None"
        top_symptom_count = int(symptom_counts.iloc[0]) if not symptom_counts.empty else 0

        # Status counts
        status_counts = self.df["status"].value_counts().to_dict()
        ongoing_count = status_counts.get("Ongoing", 0)
        resolved_count = status_counts.get("Resolved", 0)

        # Average duration (ignoring nulls, NOT treating missing as zero)
        valid_durations = self.df["duration_hours"].dropna()
        avg_duration = round(float(valid_durations.mean()), 1) if not valid_durations.empty else None

        return {
            "total_entries": total_entries,
            "distinct_days": distinct_days,
            "avg_severity": avg_severity,
            "max_severity": max_severity,
            "max_severity_symptom": max_severity_symptom,
            "top_symptom": top_symptom,
            "top_symptom_count": top_symptom_count,
            "ongoing_count": ongoing_count,
            "resolved_count": resolved_count,
            "avg_duration": avg_duration
        }

    # ==========================================
    # Plotly Visualizations
    # ==========================================

    def plot_severity_timeline(self) -> Optional[go.Figure]:
        """Generates an interactive Plotly timeline chart showing severity over time."""
        if self.df.empty:
            return None

        plot_df = self.df.copy()
        plot_df["formatted_date"] = plot_df["onset_date"].astype(str)

        fig = px.scatter(
            plot_df,
            x="onset_date",
            y="severity",
            color="category",
            size="severity",
            hover_name="symptom",
            hover_data={
                "onset_date": True,
                "severity": True,
                "status": True,
                "impact": True,
                "duration_hours": True
            },
            color_discrete_sequence=["#7B61FF", "#2A9D8F", "#E76F7C", "#E9A13B", "#6C5CE7", "#00B894", "#E17055"],
            labels={"onset_date": "Date of Onset", "severity": "Severity Rating (1-10)", "category": "Category"},
            title="Symptom Progression & Severity Timeline"
        )

        # Add trendline line if more than 1 entry
        if len(plot_df) > 1:
            line_trace = go.Scatter(
                x=plot_df["onset_date"],
                y=plot_df["severity"],
                mode="lines",
                line=dict(color="rgba(123, 97, 255, 0.35)", width=2, dash="dot"),
                name="Severity Trajectory",
                showlegend=False
            )
            fig.add_trace(line_trace)

        fig.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FAF9FC",
            font=dict(family="sans-serif", color="#1C192B"),
            yaxis=dict(range=[0.5, 10.5], dtick=1, gridcolor="#EBE7F5"),
            xaxis=dict(gridcolor="#EBE7F5"),
            margin=dict(l=40, r=40, t=50, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        return fig

    def plot_symptom_frequency(self) -> Optional[go.Figure]:
        """Generates a horizontal bar chart displaying frequency of each symptom."""
        if self.df.empty:
            return None

        counts = self.df["symptom"].value_counts().reset_index()
        counts.columns = ["symptom", "count"]
        counts = counts.sort_values(by="count", ascending=True)

        fig = px.bar(
            counts,
            x="count",
            y="symptom",
            orientation="h",
            color="count",
            color_continuous_scale=["#EFEBFC", "#7B61FF"],
            labels={"count": "Number of Recorded Days", "symptom": "Symptom Name"},
            title="Symptom Frequency Distribution"
        )

        fig.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FAF9FC",
            font=dict(family="sans-serif", color="#1C192B"),
            xaxis=dict(dtick=1, gridcolor="#EBE7F5"),
            yaxis=dict(gridcolor="#EBE7F5"),
            coloraxis_showscale=False,
            margin=dict(l=40, r=40, t=50, b=40)
        )
        return fig

    def plot_context_comparison(self) -> Optional[go.Figure]:
        """
        Generates a contextual comparison of severity grouped by Sleep Quality or Stress.
        Returns None if not enough contextual data was logged.
        """
        if self.df.empty:
            return None

        valid_sleep = self.df.dropna(subset=["sleep"])
        if len(valid_sleep) < 2:
            return None

        grouped = valid_sleep.groupby("sleep")["severity"].agg(["mean", "count"]).reset_index()
        grouped.columns = ["sleep_quality", "mean_severity", "entry_count"]
        grouped["mean_severity"] = grouped["mean_severity"].round(1)

        fig = px.bar(
            grouped,
            x="sleep_quality",
            y="mean_severity",
            color="mean_severity",
            color_continuous_scale=["#2A9D8F", "#E9A13B", "#E76F7C"],
            labels={"sleep_quality": "Reported Sleep Quality", "mean_severity": "Average Severity"},
            title="Average Symptom Severity by Reported Sleep Quality"
        )

        fig.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FAF9FC",
            font=dict(family="sans-serif", color="#1C192B"),
            yaxis=dict(range=[0, 10.5], dtick=2, gridcolor="#EBE7F5"),
            xaxis=dict(gridcolor="#EBE7F5"),
            coloraxis_showscale=False,
            margin=dict(l=40, r=40, t=50, b=40)
        )
        return fig

    # ==========================================
    # Explainable Pattern Engine (Rule-Grounded)
    # ==========================================

    def generate_explainable_insights(self) -> List[Dict[str, str]]:
        """
        Produces explainable, deterministic statements grounded strictly in recorded data.
        Returns a list of structured insight dicts with title, observation, and note.
        """
        insights = []

        if len(self.df) < 3:
            insights.append({
                "type": "insufficient_data",
                "title": "Data Collection in Progress",
                "observation": "There is not enough recorded information to identify a meaningful pattern yet. Continue recording your symptoms to build a clearer history.",
                "context_note": "A minimum of 3 to 5 symptom entries across multiple days is required for observable pattern summaries."
            })
            return insights

        total_entries = len(self.df)
        distinct_days = self.df["onset_date"].nunique()
        start_date = self.df["onset_date"].min()
        end_date = self.df["onset_date"].max()
        period_str = f"{start_date} to {end_date}"

        # 1. Frequency & Dominance Insight
        top_symptom_series = self.df["symptom"].value_counts()
        top_symptom = top_symptom_series.index[0]
        top_count = int(top_symptom_series.iloc[0])
        pct = int(round((top_count / total_entries) * 100))

        insights.append({
            "type": "frequency",
            "title": f"Primary Recorded Symptom: {top_symptom}",
            "observation": f"'{top_symptom}' was recorded {top_count} times ({pct}% of entries) across {distinct_days} logged days between {period_str}.",
            "context_note": "This reflects your logging frequency and can help your healthcare provider understand which symptom is most prominent."
        })

        # 2. Severity Trajectory Insight
        if len(self.df) >= 4:
            mid = len(self.df) // 2
            first_half_avg = self.df.iloc[:mid]["severity"].mean()
            second_half_avg = self.df.iloc[mid:]["severity"].mean()
            diff = round(second_half_avg - first_half_avg, 1)

            if diff >= 1.5:
                trajectory = "an upward trend in recorded severity"
                note = "Recorded severity ratings have increased on average over your recent entries."
            elif diff <= -1.5:
                trajectory = "a downward trend in recorded severity"
                note = "Recent entries show lower average severity compared to earlier recorded dates."
            else:
                trajectory = "a relatively stable severity pattern"
                note = "Average recorded severity has remained within a consistent range across the tracking period."

            insights.append({
                "type": "trajectory",
                "title": "Severity Progression",
                "observation": f"Between {period_str}, your symptom ratings show {trajectory} (earlier average: {first_half_avg:.1f}/10 vs recent average: {second_half_avg:.1f}/10).",
                "context_note": f"{note} Discuss whether this aligns with any treatment changes or lifestyle adjustments."
            })

        # 3. Contextual Co-Occurrence (Sleep & Symptom)
        sleep_df = self.df.dropna(subset=["sleep"])
        if len(sleep_df) >= 3:
            poor_sleep = sleep_df[sleep_df["sleep"].str.contains("Disrupted|Insomnia", case=False, na=False)]
            poor_sleep_count = len(poor_sleep)
            if poor_sleep_count >= 2:
                # Top symptom during poor sleep
                co_top = poor_sleep["symptom"].value_counts().index[0]
                co_count = poor_sleep["symptom"].value_counts().iloc[0]
                insights.append({
                    "type": "correlation_sleep",
                    "title": "Sleep Quality Observation",
                    "observation": f"Poor or disrupted sleep was recorded on {poor_sleep_count} days. '{co_top}' was also recorded on {co_count} of those days.",
                    "context_note": "These entries show a possible observation association, not proof that poor sleep directly caused the symptom. Sharing this with your doctor can help evaluate sleep hygiene and nervous system regulation."
                })

        # 4. Stress Co-Occurrence
        stress_df = self.df.dropna(subset=["stress"])
        if len(stress_df) >= 3:
            high_stress = stress_df[stress_df["stress"].str.contains("High|Extreme", case=False, na=False)]
            high_stress_count = len(high_stress)
            if high_stress_count >= 2:
                stress_top = high_stress["symptom"].value_counts().index[0]
                insights.append({
                    "type": "correlation_stress",
                    "title": "Elevated Stress Observation",
                    "observation": f"High or extreme stress levels were noted alongside {high_stress_count} symptom records, with '{stress_top}' recorded most frequently during these intervals.",
                    "context_note": "Stress hormones (cortisol) can influence inflammatory and pain thresholds. Note this pattern to discuss stress management strategies with your clinician."
                })

        return insights

    # ==========================================
    # Advanced Multi-Symptom Co-Occurrence Heatmap
    # ==========================================

    def plot_cooccurrence_heatmap(self) -> Optional[go.Figure]:
        """
        Calculates and plots a 2D co-occurrence heatmap of symptoms recorded on the same dates.
        """
        if self.df.empty or self.df["symptom"].nunique() < 2:
            return None

        date_sym = self.df.groupby(["onset_date", "symptom"]).size().unstack(fill_value=0)
        date_sym_binary = (date_sym > 0).astype(int)

        co_matrix = date_sym_binary.T.dot(date_sym_binary)
        top_syms = self.df["symptom"].value_counts().head(6).index
        sub_matrix = co_matrix.loc[top_syms, top_syms]

        fig = px.imshow(
            sub_matrix,
            labels=dict(x="Co-Occurring Symptom", y="Reference Symptom", color="Shared Days"),
            x=sub_matrix.columns,
            y=sub_matrix.index,
            color_continuous_scale=["#FAF9FC", "#D3CBEC", "#7B61FF"],
            text_auto=True,
            title="Symptom Co-Occurrence Matrix (Days Logged Together)"
        )
        fig.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FAF9FC",
            font=dict(family="sans-serif", color="#1C192B"),
            margin=dict(l=40, r=40, t=50, b=40)
        )
        return fig

    # ==========================================
    # Doctor Discussion Kit Generator
    # ==========================================

    def generate_doctor_talking_points(self, primary_goal: str = "Diagnostic Evaluation") -> Dict[str, Any]:
        """
        Produces a personalized, prioritized 10-minute clinical visit talking-points agenda.
        """
        metrics = self.calculate_summary_metrics()
        top_sym = metrics["top_symptom"]
        avg_sev = metrics["avg_severity"]
        total_logs = metrics["total_entries"]

        goals_map = {
            "Diagnostic Evaluation": {
                "opening": f"I have tracked {total_logs} symptom entries over recent weeks. My most frequent symptom is '{top_sym}' with an average severity of {avg_sev}/10. I would like to discuss appropriate diagnostic evaluations (such as hormonal profiling, pelvic ultrasound, or ferritin levels).",
                "questions": [
                    f"What specific conditions (such as PCOS, endometriosis, or hormonal migraine) might explain the cluster of '{top_sym}' and related symptoms?",
                    "Are there baseline laboratory tests (Complete Blood Count, thyroid panel, fasting insulin) you would recommend?",
                    "What specific changes in my symptoms should prompt urgent evaluation?"
                ]
            },
            "Medication & Treatment Review": {
                "opening": f"I am experiencing recurring episodes of '{top_sym}' with peak severity reaching {metrics['max_severity']}/10. I would like to review my current medications and discuss evidence-based treatment options.",
                "questions": [
                    "Is my current treatment regimen providing optimal relief, or should we consider dosage adjustment?",
                    "What are the typical side effects or contraindications I should monitor?",
                    "Are there non-pharmacological or lifestyle adjuncts (e.g. dietary or physical therapy) that have proven efficacy?"
                ]
            },
            "Transitional Care (Perimenopause / Cycle Changes)": {
                "opening": f"I have recorded notable shifts in cycle regularity and systemic symptoms like '{top_sym}'. I want to understand whether these align with perimenopausal hormonal transitions.",
                "questions": [
                    "Do my symptom trajectories and cycle changes suggest perimenopause?",
                    "What are the risks and benefits of hormone replacement therapy (HRT) or non-hormonal options for my specific profile?",
                    "How should I track symptoms going forward to assess progression?"
                ]
            }
        }
        selected = goals_map.get(primary_goal, goals_map["Diagnostic Evaluation"])
        return {
            "goal": primary_goal,
            "opening_statement": selected["opening"],
            "suggested_questions": selected["questions"],
            "data_summary": f"{total_logs} entries logged, average severity {avg_sev}/10, primary symptom '{top_sym}'."
        }

