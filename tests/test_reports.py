"""
HERPath AI - Automated Report Generation Unit Tests
recHERsion 2026 | PS1: Women's Healthcare
"""

import pytest
from models import UserProfile, SymptomEntry
from report_generator import ClinicianReportGenerator


@pytest.fixture
def mock_profile():
    return UserProfile(
        id="demo_test",
        display_name="Maya Sharma",
        preferences={"track_menstrual": True}
    )


def test_empty_report_generation(mock_profile):
    """Ensures empty symptom history still generates a valid, well-formed PDF document."""
    generator = ClinicianReportGenerator(
        profile=mock_profile,
        entries=[],
        start_date="2026-10-01",
        end_date="2026-10-24"
    )
    pdf_bytes = generator.generate_pdf_bytes()
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")


def test_single_entry_report_generation(mock_profile):
    """Ensures a single entry generates a valid PDF."""
    entry = SymptomEntry(
        id=1,
        profile_id="demo_test",
        category="Neurological & Head",
        symptom="Migraine",
        onset_date="2026-10-15",
        severity=7,
        duration_hours=6.0,
        status="Resolved",
        impact="Moderate",
        notes="Sensitivity to light.",
        context={"sleep": "Disrupted / Fragmented"}
    )
    generator = ClinicianReportGenerator(
        profile=mock_profile,
        entries=[entry],
        start_date="2026-10-01",
        end_date="2026-10-24"
    )
    pdf_bytes = generator.generate_pdf_bytes()
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


def test_multiple_entries_report_generation(mock_profile):
    """Ensures multi-entry history with long notes compiles into a valid PDF."""
    entries = [
        SymptomEntry(
            id=i,
            profile_id="demo_test",
            category="Pelvic & Menstrual",
            symptom="Pelvic Pain / Cramping",
            onset_date=f"2026-10-{10+i:02d}",
            severity=5 + (i % 4),
            duration_hours=4.0 * i,
            status="Ongoing" if i == 5 else "Resolved",
            impact="Severe",
            notes="Extensive notes about daily disruption, heat therapy, and symptoms observed during clinical appointment preparation.",
            context={"sleep": "Moderate (5-7 hrs)", "stress": "High / Pressured"}
        )
        for i in range(1, 8)
    ]
    generator = ClinicianReportGenerator(
        profile=mock_profile,
        entries=entries,
        start_date="2026-10-01",
        end_date="2026-10-24"
    )
    pdf_bytes = generator.generate_pdf_bytes()
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF")
