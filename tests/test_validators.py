"""
HERPath AI - Automated Validator Unit Tests
recHERsion 2026 | PS1: Women's Healthcare
"""

import pytest
from datetime import date, timedelta
from validators import (
    validate_severity,
    validate_onset_date,
    validate_duration_hours,
    validate_symptom_name,
    validate_category,
    validate_symptom_payload,
    validate_display_name,
    ValidationError
)


def test_severity_valid_range():
    """Ensures severity between 1 and 10 passes cleanly."""
    for s in range(1, 11):
        assert validate_severity(s) == s
        assert validate_severity(str(s)) == s


def test_severity_out_of_bounds():
    """Ensures severity below 1 or above 10 raises ValidationError."""
    with pytest.raises(ValidationError):
        validate_severity(0)

    with pytest.raises(ValidationError):
        validate_severity(11)

    with pytest.raises(ValidationError):
        validate_severity(-5)

    with pytest.raises(ValidationError):
        validate_severity("invalid_string")


def test_missing_symptom_name():
    """Ensures blank or whitespace-only symptom name raises ValidationError."""
    with pytest.raises(ValidationError):
        validate_symptom_name("")

    with pytest.raises(ValidationError):
        validate_symptom_name("   ")

    with pytest.raises(ValidationError):
        validate_symptom_name("a")  # Too short (< 2 chars)


def test_valid_symptom_name():
    """Ensures clean symptom name returns trimmed string."""
    assert validate_symptom_name("  Migraine with Aura  ") == "Migraine with Aura"


def test_onset_date_validation():
    """Ensures valid date strings and objects pass, and invalid dates fail."""
    today_str = date.today().strftime("%Y-%m-%d")
    assert validate_onset_date(today_str) == today_str
    assert validate_onset_date(date.today()) == today_str

    # Invalid format
    with pytest.raises(ValidationError):
        validate_onset_date("20-10-2026")

    # Future date beyond 1 day
    future_date = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
    with pytest.raises(ValidationError):
        validate_onset_date(future_date)


def test_duration_validation():
    """Ensures valid duration numbers pass and invalid/negative durations fail."""
    assert validate_duration_hours(None) is None
    assert validate_duration_hours("") is None
    assert validate_duration_hours(4.5) == 4.5
    assert validate_duration_hours("12") == 12.0

    with pytest.raises(ValidationError):
        validate_duration_hours(-1.5)

    with pytest.raises(ValidationError):
        validate_duration_hours(1000)  # Exceeds max 720h (30 days)

    with pytest.raises(ValidationError):
        validate_duration_hours("many hours")


def test_full_payload_validation():
    """Ensures a complete valid symptom payload validates and sets defaults."""
    payload = {
        "profile_id": "user_valid",
        "category": "Pelvic & Menstrual",
        "symptom": "Pelvic Cramping",
        "onset_date": "2026-10-20",
        "severity": 6,
        "duration_hours": 3.0,
        "status": "Ongoing",
        "notes": "",
        "context": {"sleep": "Restful"}
    }
    validated = validate_symptom_payload(payload)
    assert validated["profile_id"] == "user_valid"
    assert validated["symptom"] == "Pelvic Cramping"
    assert validated["severity"] == 6
    assert validated["notes"] == ""
    assert validated["context"]["sleep"] == "Restful"


def test_display_name_validation():
    """Ensures display name rules work as expected."""
    assert validate_display_name("Maya") == "Maya"
    with pytest.raises(ValidationError):
        validate_display_name("A")  # Too short
    with pytest.raises(ValidationError):
        validate_display_name("")
