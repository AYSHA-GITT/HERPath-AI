"""
HERPath AI - Clinician-Ready Health Report Generator
recHERsion 2026 | PS1: Women's Healthcare

Generates structured, professional, non-diagnostic clinical summary PDFs
using ReportLab from actual user database records.
"""

import io
from datetime import datetime
from typing import List, Optional, Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)

from models import SymptomEntry, UserProfile, MedicationEntry
from config import APP_TITLE, APP_TAGLINE, CLINICAL_DISCLAIMER
from insights_engine import InsightsEngine
from clinical_summary_service import ClinicalSummaryService, ClinicalSummaryData


class ClinicianReportGenerator:
    """Generates PDF health summaries designed for review during clinical consultations."""

    def __init__(
        self,
        profile: UserProfile,
        entries: List[SymptomEntry],
        start_date: str,
        end_date: str,
        medications: Optional[List[MedicationEntry]] = None,
        patient_concerns: Optional[List[str]] = None,
        summary_data: Optional[ClinicalSummaryData] = None
    ):
        self.profile = profile
        self.entries = entries
        self.start_date = start_date
        self.end_date = end_date
        self.medications = medications or []
        self.patient_concerns = [c.strip() for c in (patient_concerns or []) if c and c.strip()]
        self.insights_engine = InsightsEngine(entries)

        # Build or use existing summary data
        if summary_data is not None:
            self.summary = summary_data
        else:
            service = ClinicalSummaryService(
                profile_id=profile.id,
                start_date=start_date,
                end_date=end_date,
                patient_concerns=self.patient_concerns,
                entries=entries,
                medications=self.medications,
                profile=profile
            )
            self.summary = service.generate_summary()

    def generate_pdf_bytes(self) -> bytes:
        """Constructs and returns the PDF document as raw bytes."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom Brand Colors
        c_rose = colors.HexColor("#B95F7B")
        c_dark = colors.HexColor("#2A1E24")
        c_muted = colors.HexColor("#6B5E65")
        c_light_bg = colors.HexColor("#FDF7F9")
        c_card_border = colors.HexColor("#EBD8DF")
        c_teal = colors.HexColor("#2A9D8F")
        c_highlight = colors.HexColor("#8E3B56")

        # Custom Typography Styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=c_rose
        )

        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=c_muted
        )

        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=15,
            textColor=c_dark,
            spaceBefore=12,
            spaceAfter=5
        )

        sub_heading = ParagraphStyle(
            "SubHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            textColor=c_highlight,
            spaceBefore=6,
            spaceAfter=3
        )

        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=c_dark
        )

        body_muted = ParagraphStyle(
            "ReportBodyMuted",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=c_muted
        )

        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white
        )

        table_cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9.5,
            textColor=c_dark
        )

        table_cell_bold = ParagraphStyle(
            "TableCellBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9.5,
            textColor=c_dark
        )

        checklist_item_style = ParagraphStyle(
            "ChecklistItem",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=c_dark
        )

        disclaimer_style = ParagraphStyle(
            "DisclaimerStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=7,
            leading=9,
            textColor=c_muted
        )

        story = []

        # 1. Header Banner
        story.append(Paragraph(f"{APP_TITLE} — Smart Clinical Consultation Summary", title_style))
        story.append(Paragraph(f"{APP_TAGLINE} | Patient-Generated Health Observations for Medical Consultation", subtitle_style))
        story.append(Spacer(1, 6))
        story.append(HRFlowable(width="100%", thickness=1.5, color=c_rose, spaceBefore=2, spaceAfter=8))

        # 2. Metadata Information Table
        meta_data = [
            [
                Paragraph(f"<b>Patient / Alias:</b> {self.profile.display_name}", body_style),
                Paragraph(f"<b>Reporting Period:</b> {self.start_date} to {self.end_date} ({self.summary.calendar_days} days)", body_style)
            ],
            [
                Paragraph(f"<b>Generated On:</b> {self.summary.generated_at}", body_style),
                Paragraph(f"<b>Data Scope:</b> {self.summary.total_entries} entries across {self.summary.distinct_days} distinct days", body_style)
            ]
        ]
        meta_table = Table(meta_data, colWidths=[270, 270])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), c_light_bg),
            ('BOX', (0, 0), (-1, -1), 0.75, c_card_border),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 8))

        # 3. Patient's Main Concerns & Priorities (if any)
        if self.summary.patient_concerns:
            story.append(Paragraph("Patient Consultation Priorities & Goals", section_heading))
            concern_rows = []
            for pc in self.summary.patient_concerns:
                concern_rows.append([
                    Paragraph("🎯", table_cell_bold),
                    Paragraph(f"<b>{pc}</b><br/><font color='#6B5E65' size='6.5'>Patient-reported discussion priority (non-diagnostic)</font>", body_style)
                ])
            c_table = Table(concern_rows, colWidths=[20, 520])
            c_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFF8FA")),
                ('BOX', (0, 0), (-1, -1), 0.5, c_card_border),
                ('PADDING', (0, 0), (-1, -1), 4),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(c_table)
            story.append(Spacer(1, 8))

        # 4. Consultation Overview & Key Metrics
        story.append(Paragraph("1. Consultation Overview & Health Metrics", section_heading))
        stats = self.insights_engine.calculate_summary_metrics()

        max_sev_txt = f"{self.summary.max_severity}/10 for <i>{self.summary.max_severity_symptom}</i> on {self.summary.max_severity_date}" if self.summary.max_severity else "N/A"
        overview_text = (
            f"During the selected period (<b>{self.start_date}</b> to <b>{self.end_date}</b>, {self.summary.calendar_days} calendar days), "
            f"a total of <b>{self.summary.total_entries}</b> symptom entries were recorded across <b>{self.summary.distinct_days}</b> distinct days. "
            f"Average recorded severity was <b>{self.summary.avg_severity or 'N/A'}/10</b> (Peak: <b>{max_sev_txt}</b>). "
            f"{self.summary.duration_stats.summary_statement}"
        )
        story.append(Paragraph(overview_text, body_style))
        story.append(Spacer(1, 6))

        # Quick Metric KPI Table
        top_sym_display = f"{stats['top_symptom']} ({stats['top_symptom_count']} logs)" if stats['top_symptom'] != "None" else "None"
        kpi_data = [
            [
                Paragraph("Total Entries", table_header_style),
                Paragraph("Distinct Days", table_header_style),
                Paragraph("Avg Severity", table_header_style),
                Paragraph("Peak Severity", table_header_style),
                Paragraph("Primary Symptom", table_header_style),
            ],
            [
                Paragraph(str(self.summary.total_entries), table_cell_bold),
                Paragraph(f"{self.summary.distinct_days} / {self.summary.calendar_days}d", table_cell_style),
                Paragraph(f"{self.summary.avg_severity or '-'}/10", table_cell_style),
                Paragraph(f"{self.summary.max_severity or '-'}/10", table_cell_style),
                Paragraph(top_sym_display, table_cell_style),
            ]
        ]
        kpi_table = Table(kpi_data, colWidths=[95, 105, 95, 95, 150])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), c_rose),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, c_card_border),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white]),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 8))

        # 5. Symptom Patterns & Severity Trajectory
        story.append(Paragraph("2. Symptom Patterns, Frequencies & Severity Trajectory", section_heading))
        if self.summary.frequent_symptoms:
            freq_rows = [[
                Paragraph("Symptom", table_header_style),
                Paragraph("Category", table_header_style),
                Paragraph("Logs", table_header_style),
                Paragraph("Days", table_header_style),
                Paragraph("Share", table_header_style),
                Paragraph("Avg Sev", table_header_style),
                Paragraph("Range", table_header_style),
                Paragraph("Avg Dur.", table_header_style),
            ]]
            for fs in self.summary.frequent_symptoms[:8]:
                dur_disp = f"{fs.avg_duration}h" if fs.avg_duration else "-"
                freq_rows.append([
                    Paragraph(f"<b>{fs.symptom}</b>", table_cell_style),
                    Paragraph(fs.category, table_cell_style),
                    Paragraph(str(fs.entry_count), table_cell_style),
                    Paragraph(str(fs.distinct_days), table_cell_style),
                    Paragraph(f"{fs.percentage_of_entries}%", table_cell_style),
                    Paragraph(f"{fs.avg_severity}/10", table_cell_style),
                    Paragraph(f"{fs.min_severity}–{fs.max_severity}", table_cell_style),
                    Paragraph(dur_disp, table_cell_style),
                ])
            freq_table = Table(freq_rows, colWidths=[120, 100, 40, 40, 45, 55, 60, 80])
            freq_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), c_highlight),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, c_card_border),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light_bg]),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(freq_table)
            story.append(Spacer(1, 5))

        # Progression observation & repeated severe episodes
        story.append(Paragraph(f"<b>Temporal Trajectory:</b> {self.summary.progression.trajectory_statement}", body_style))
        if self.summary.repeated_severe:
            rep_notes = []
            for rs in self.summary.repeated_severe:
                rep_notes.append(f"• <b>{rs.symptom}</b> reached high severity (≥7/10) across {rs.count_severe} entries (Peak: {rs.max_severity}/10 on {', '.join(rs.dates[:4])}).")
            story.append(Spacer(1, 3))
            story.append(Paragraph("<b>Repeated High-Severity Findings:</b><br/>" + "<br/>".join(rep_notes), body_style))
        story.append(Spacer(1, 8))

        # 6. Lifestyle & Functional Impact Context
        story.append(Paragraph("3. Lifestyle Context & Daily Functional Impact", section_heading))
        life = self.summary.lifestyle_impact
        life_data = [
            [
                Paragraph("Observation Area", table_header_style),
                Paragraph("Documented", table_header_style),
                Paragraph("Rate", table_header_style),
                Paragraph("Summary of Patient-Logged Observations", table_header_style),
            ],
            [
                Paragraph("<b>Sleep Quality</b>", table_cell_style),
                Paragraph(f"{life.sleep.documented_entries} / {life.sleep.total_entries}", table_cell_style),
                Paragraph(f"{life.sleep.documentation_rate}%", table_cell_style),
                Paragraph(life.sleep.summary_statement, table_cell_style),
            ],
            [
                Paragraph("<b>Stress Levels</b>", table_cell_style),
                Paragraph(f"{life.stress.documented_entries} / {life.stress.total_entries}", table_cell_style),
                Paragraph(f"{life.stress.documentation_rate}%", table_cell_style),
                Paragraph(life.stress.summary_statement, table_cell_style),
            ],
            [
                Paragraph("<b>Energy Vitality</b>", table_cell_style),
                Paragraph(f"{life.energy.documented_entries} / {life.energy.total_entries}", table_cell_style),
                Paragraph(f"{life.energy.documentation_rate}%", table_cell_style),
                Paragraph(life.energy.summary_statement, table_cell_style),
            ],
            [
                Paragraph("<b>Menstrual Cycle</b>", table_cell_style),
                Paragraph(f"{life.cycle_phase.documented_entries} / {life.cycle_phase.total_entries}", table_cell_style),
                Paragraph(f"{life.cycle_phase.documentation_rate}%", table_cell_style),
                Paragraph(life.cycle_phase.summary_statement, table_cell_style),
            ],
            [
                Paragraph("<b>Daily Impact</b>", table_cell_style),
                Paragraph(f"{life.functional_impact.documented_entries} / {life.functional_impact.total_entries}", table_cell_style),
                Paragraph(f"{life.functional_impact.documentation_rate}%", table_cell_style),
                Paragraph(life.functional_impact.summary_statement, table_cell_style),
            ],
        ]
        life_table = Table(life_data, colWidths=[95, 65, 45, 335])
        life_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), c_teal),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#B8EBE3")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2FAF9")]),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(life_table)
        story.append(Spacer(1, 8))

        # 7. Medication & Treatment History
        if self.medications or self.summary.treatments:
            story.append(Paragraph("4. Medication & Treatment History (Temporal Observations)", section_heading))
            med_rows = [[
                Paragraph("Medication / Treatment", table_header_style),
                Paragraph("Category", table_header_style),
                Paragraph("Dosage & Frequency", table_header_style),
                Paragraph("Start Date", table_header_style),
                Paragraph("Observation Note (Non-Causal)", table_header_style),
            ]]
            for t in self.summary.treatments:
                st_date = t.started_date or "Not logged"
                med_rows.append([
                    Paragraph(f"<b>{t.name}</b>", table_cell_style),
                    Paragraph(t.category, table_cell_style),
                    Paragraph(f"{t.dosage} ({t.frequency})", table_cell_style),
                    Paragraph(st_date, table_cell_style),
                    Paragraph(t.observation_statement, table_cell_style),
                ])
            med_table = Table(med_rows, colWidths=[105, 75, 105, 65, 190])
            med_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), c_rose),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, c_card_border),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light_bg]),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(med_table)
            story.append(Spacer(1, 8))

        # 8. Doctor Discussion Checklist
        story.append(Paragraph("5. Doctor Discussion Checklist & Consultation Prompts", section_heading))
        checklist_items = []

        if self.summary.checklist.symptoms_to_discuss:
            for it in self.summary.checklist.symptoms_to_discuss:
                checklist_items.append([Paragraph("☐", table_cell_bold), Paragraph(f"<b>Symptoms to Review:</b> {it}", checklist_item_style)])

        if self.summary.checklist.effects_on_daily_activities:
            for it in self.summary.checklist.effects_on_daily_activities:
                checklist_items.append([Paragraph("☐", table_cell_bold), Paragraph(f"<b>Daily Impact:</b> {it}", checklist_item_style)])

        if self.summary.checklist.medication_questions:
            for it in self.summary.checklist.medication_questions[:2]:
                checklist_items.append([Paragraph("☐", table_cell_bold), Paragraph(f"<b>Treatment Inquiry:</b> {it}", checklist_item_style)])

        if self.summary.checklist.questions_for_clinician:
            for it in self.summary.checklist.questions_for_clinician:
                checklist_items.append([Paragraph("☐", table_cell_bold), Paragraph(f"<b>Clinical Question:</b> {it}", checklist_item_style)])

        if checklist_items:
            chk_table = Table(checklist_items, colWidths=[18, 522])
            chk_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LINEBELOW', (0, 0), (-1, -1), 0.3, colors.HexColor("#F0E2E7")),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))
            story.append(chk_table)
            story.append(Spacer(1, 8))

        # 9. Detailed Chronological Log (Sample of entries)
        story.append(Paragraph("6. Detailed Chronological Record Log", section_heading))
        if not self.entries:
            story.append(Paragraph("<i>No symptom records were found for the selected reporting period.</i>", body_style))
        else:
            table_rows = [
                [
                    Paragraph("Date", table_header_style),
                    Paragraph("Symptom & Category", table_header_style),
                    Paragraph("Sev", table_header_style),
                    Paragraph("Dur.", table_header_style),
                    Paragraph("Status", table_header_style),
                    Paragraph("Impact", table_header_style),
                    Paragraph("Context & Notes", table_header_style),
                ]
            ]

            for e in self.entries[:35]:  # Up to 35 rows for document pagination
                ctx_items = []
                if e.context:
                    if e.context.get("sleep"):
                        ctx_items.append(f"Sleep: {e.context['sleep']}")
                    if e.context.get("stress"):
                        ctx_items.append(f"Stress: {e.context['stress']}")
                    if e.context.get("cycle_phase") and e.context["cycle_phase"] != "Not tracking / NA":
                        ctx_items.append(f"Cycle: {e.context['cycle_phase']}")

                context_str = f" [{'; '.join(ctx_items)}]" if ctx_items else ""
                notes_full = f"{e.notes or 'None'}{context_str}"
                dur_str = f"{e.duration_hours}h" if e.duration_hours is not None else "-"

                table_rows.append([
                    Paragraph(str(e.onset_date), table_cell_style),
                    Paragraph(f"<b>{e.symptom}</b><br/><font color='#6B5E65'>{e.category}</font>", table_cell_style),
                    Paragraph(f"<b>{e.severity}</b>/10", table_cell_style),
                    Paragraph(dur_str, table_cell_style),
                    Paragraph(str(e.status), table_cell_style),
                    Paragraph(str(e.impact or '-'), table_cell_style),
                    Paragraph(notes_full, table_cell_style),
                ])

            sym_table = Table(table_rows, colWidths=[60, 115, 40, 35, 55, 65, 170])
            sym_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), c_rose),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, c_card_border),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light_bg]),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(sym_table)

        story.append(Spacer(1, 10))

        # 10. Data Limitations & Disclaimer
        story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#D8C3CB"), spaceBefore=4, spaceAfter=6))
        lim_bullets = " &bull; ".join(self.summary.data_limitations[:4])
        disclaimer_text = (
            f"<b>DATA LIMITATIONS:</b> {lim_bullets}<br/>"
            f"<b>CLINICAL DISCLAIMER & NOTICES:</b> {CLINICAL_DISCLAIMER} "
            "This document is a patient-reported log for informational reference during an in-person or telehealth clinical consultation. "
            "It does not constitute clinical triage, a diagnosis, or an electronic health record (EHR)."
        )
        story.append(Paragraph(disclaimer_text, disclaimer_style))

        # Build document
        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data
