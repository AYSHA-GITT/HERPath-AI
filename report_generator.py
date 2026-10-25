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


class ClinicianReportGenerator:
    """Generates PDF health summaries designed for review during clinical consultations."""

    def __init__(
        self,
        profile: UserProfile,
        entries: List[SymptomEntry],
        start_date: str,
        end_date: str,
        medications: Optional[List[MedicationEntry]] = None,
        user_selected_notes: Optional[Dict[int, str]] = None,
        custom_questions: Optional[List[str]] = None,
        include_all_notes: bool = False
    ):
        self.profile = profile
        self.entries = entries
        self.start_date = start_date
        self.end_date = end_date
        self.medications = medications or []
        self.user_selected_notes = user_selected_notes
        self.custom_questions = custom_questions
        self.include_all_notes = include_all_notes
        self.insights_engine = InsightsEngine(entries)

    def generate_pdf_bytes(self) -> bytes:
        """Constructs and returns the PDF document as raw bytes."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()

        # Custom Brand Styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#7B61FF")
        )

        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#5C5770")
        )

        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#1C192B"),
            spaceBefore=14,
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#2C283B")
        )

        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.white
        )

        table_cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#1C192B")
        )

        disclaimer_style = ParagraphStyle(
            "DisclaimerStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#777286")
        )

        story = []

        # 1. Header Banner
        story.append(Paragraph(f"{APP_TITLE} — Clinician Health Summary", title_style))
        story.append(Paragraph(f"{APP_TAGLINE} | Patient-Generated Health Observations", subtitle_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#7B61FF"), spaceBefore=2, spaceAfter=12))

        # 2. Meta Information Card Table
        gen_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        meta_data = [
            [
                Paragraph(f"<b>Profile Name / Alias:</b> {self.profile.display_name}", body_style),
                Paragraph(f"<b>Report Period:</b> {self.start_date} to {self.end_date}", body_style)
            ],
            [
                Paragraph(f"<b>Generated On:</b> {gen_time}", body_style),
                Paragraph(f"<b>Total Entries Recorded:</b> {len(self.entries)}", body_style)
            ]
        ]
        meta_table = Table(meta_data, colWidths=[270, 260])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8F7FC")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2DEF0")),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 14))

        # 3. Clinical Summary Statistics
        stats = self.insights_engine.calculate_summary_metrics()
        story.append(Paragraph("1. Summary of Logged Observations", section_heading))

        avg_dur_text = f"{stats['avg_duration']} hrs" if stats['avg_duration'] else "Not recorded"
        summary_text = (
            f"During the selected period (<b>{self.start_date}</b> to <b>{self.end_date}</b>), "
            f"a total of <b>{stats['total_entries']}</b> symptom instances were logged across "
            f"<b>{stats['distinct_days']}</b> distinct dates. "
            f"Average recorded severity was <b>{stats['avg_severity']}/10</b> (Peak: <b>{stats['max_severity']}/10</b> for <i>{stats['max_severity_symptom']}</i>). "
            f"The most frequently logged symptom was <b>{stats['top_symptom']}</b> ({stats['top_symptom_count']} logs). "
            f"Active status: <b>{stats['ongoing_count']} Ongoing</b>, <b>{stats['resolved_count']} Resolved</b>. "
            f"Average episode duration: <b>{avg_dur_text}</b>."
        )
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 10))

        # 4. Relevant Wellbeing Context Summary (Sleep, Stress, Menstrual Context)
        if self.entries:
            sleep_counts = {}
            stress_counts = {}
            cycle_counts = {}
            for e in self.entries:
                if e.context:
                    sl = e.context.get("sleep")
                    if sl:
                        sleep_counts[sl] = sleep_counts.get(sl, 0) + 1
                    st_val = e.context.get("stress")
                    if st_val:
                        stress_counts[st_val] = stress_counts.get(st_val, 0) + 1
                    cyc = e.context.get("cycle_phase")
                    if cyc and cyc not in ["Not tracking / NA", "None", ""]:
                        cycle_counts[cyc] = cycle_counts.get(cyc, 0) + 1

            if sleep_counts or stress_counts or cycle_counts:
                story.append(Paragraph("2. Relevant Wellbeing & Context Summary", section_heading))
                wellbeing_rows = [
                    [
                        Paragraph("Context Domain", table_header_style),
                        Paragraph("Reported Distribution / Patterns", table_header_style),
                    ]
                ]
                if sleep_counts:
                    sleep_str = ", ".join([f"{k}: {v}" for k, v in sleep_counts.items()])
                    wellbeing_rows.append([
                        Paragraph("<b>Sleep Quality</b>", table_cell_style),
                        Paragraph(sleep_str, table_cell_style)
                    ])
                if stress_counts:
                    stress_str = ", ".join([f"{k}: {v}" for k, v in stress_counts.items()])
                    wellbeing_rows.append([
                        Paragraph("<b>Stress Levels</b>", table_cell_style),
                        Paragraph(stress_str, table_cell_style)
                    ])
                if cycle_counts:
                    cycle_str = ", ".join([f"{k}: {v}" for k, v in cycle_counts.items()])
                    wellbeing_rows.append([
                        Paragraph("<b>Cycle / Hormonal Phase</b>", table_cell_style),
                        Paragraph(cycle_str, table_cell_style)
                    ])

                wb_table = Table(wellbeing_rows, colWidths=[150, 380])
                wb_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#5C5770")),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D8D3E8")),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F7FC")]),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                story.append(wb_table)
                story.append(Spacer(1, 10))

        # 5. Current Medications & Treatments (if any recorded)
        sec_num = 3
        if self.medications:
            story.append(Paragraph(f"{sec_num}. Current Medications & Health Interventions", section_heading))
            sec_num += 1
            med_rows = [[
                Paragraph("Medication / Treatment", table_header_style),
                Paragraph("Category", table_header_style),
                Paragraph("Dosage & Frequency", table_header_style),
                Paragraph("Notes", table_header_style),
            ]]
            for m in self.medications:
                med_rows.append([
                    Paragraph(f"<b>{m.name}</b>", table_cell_style),
                    Paragraph(m.category, table_cell_style),
                    Paragraph(f"{m.dosage} ({m.frequency})" if m.dosage or m.frequency else "-", table_cell_style),
                    Paragraph(m.notes or "-", table_cell_style),
                ])
            med_table = Table(med_rows, colWidths=[130, 95, 135, 165])
            med_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2A9D8F")),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#B8EBE3")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2FAF9")]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(med_table)
            story.append(Spacer(1, 10))

        # 6. Detailed Symptom Timeline Log
        story.append(Paragraph(f"{sec_num}. Detailed Chronological Symptom Timeline", section_heading))
        sec_num += 1

        if not self.entries:
            story.append(Paragraph("<i>No symptom records were found for the selected reporting period.</i>", body_style))
        else:
            table_rows = [
                [
                    Paragraph("Date", table_header_style),
                    Paragraph("Symptom & Category", table_header_style),
                    Paragraph("Sev (1-10)", table_header_style),
                    Paragraph("Dur.", table_header_style),
                    Paragraph("Status", table_header_style),
                    Paragraph("Impact", table_header_style),
                    Paragraph("Reviewed Notes & Context", table_header_style),
                ]
            ]

            for e in self.entries[:40]:  # Cap at 40 rows per summary report
                ctx_items = []
                if e.context:
                    if e.context.get("sleep"):
                        ctx_items.append(f"Sleep: {e.context['sleep']}")
                    if e.context.get("stress"):
                        ctx_items.append(f"Stress: {e.context['stress']}")
                    if e.context.get("cycle_phase") and e.context["cycle_phase"] != "Not tracking / NA":
                        ctx_items.append(f"Cycle: {e.context['cycle_phase']}")
                
                context_str = f" [{'; '.join(ctx_items)}]" if ctx_items else ""

                # Privacy-preserving note handling
                if self.include_all_notes:
                    note_body = e.notes or "-"
                elif self.user_selected_notes is not None and e.id in self.user_selected_notes:
                    note_body = self.user_selected_notes[e.id] or "-"
                elif e.notes and e.notes.strip():
                    note_body = "<font color='#888888'><i>[Private - Excluded by Patient]</i></font>"
                else:
                    note_body = "-"

                notes_full = f"{note_body}{context_str}"
                dur_str = f"{e.duration_hours}h" if e.duration_hours else "-"

                table_rows.append([
                    Paragraph(str(e.onset_date), table_cell_style),
                    Paragraph(f"<b>{e.symptom}</b><br/><font color='#5C5770'>{e.category}</font>", table_cell_style),
                    Paragraph(f"<b>{e.severity}</b>", table_cell_style),
                    Paragraph(dur_str, table_cell_style),
                    Paragraph(str(e.status), table_cell_style),
                    Paragraph(str(e.impact or '-'), table_cell_style),
                    Paragraph(notes_full, table_cell_style),
                ])

            sym_table = Table(table_rows, colWidths=[65, 115, 45, 40, 55, 65, 145])
            sym_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#7B61FF")),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2DEF0")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#FBFBFE")]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(sym_table)

        story.append(Spacer(1, 14))

        # 7. Questions for Discussion with Physician
        story.append(Paragraph(f"{sec_num}. Patient Questions for Discussion with Physician", section_heading))
        default_questions = [
            "Based on the frequency and severity trajectory of these symptoms, what diagnostic evaluations or laboratory profiles (e.g., hormonal panel, CBC, pelvic imaging) would you recommend?",
            "Are there evidence-based pharmacologic or non-pharmacologic interventions that could help address the episodes with high severity or disruption?",
            "Do any of the observed patterns (such as sleep or cycle timing correlations) suggest specific underlying conditions to monitor (such as PCOS, endometriosis, hormonal migraine, or perimenopause)?",
            "What specific red-flag warning signs should prompt an emergency department visit or urgent same-day appointment?"
        ]
        questions_to_render = self.custom_questions if self.custom_questions else default_questions
        for q in questions_to_render:
            story.append(Paragraph(f"• {q}", body_style))
            story.append(Spacer(1, 3))

        story.append(Spacer(1, 14))

        # 8. Disclaimer & Non-Diagnostic Notice
        story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#D8D3E8"), spaceBefore=4, spaceAfter=8))
        disclaimer_text = (
            f"<b>CLINICAL DISCLAIMER & NOTICES:</b> {CLINICAL_DISCLAIMER} "
            "This document is a patient-reported log for informational reference during an in-person or telehealth clinical consultation. "
            "It does not constitute clinical triage, a diagnosis, or a verified electronic health record (EHR)."
        )
        story.append(Paragraph(disclaimer_text, disclaimer_style))

        # Build document
        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data
