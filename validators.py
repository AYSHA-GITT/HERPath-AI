"""
HERPath AI - Input Validation & Sanitization Module
recHERsion 2026 | PS1: Women's Healthcare
"""

from typing import Tuple, Optional, Dict, Any
from datetime import datetime, date
import re


class ValidationError(Exception):
    """Custom exception raised for invalid health tracking inputs."""
    pass


def validate_profile_id(profile_id: str) -> str:
    """Validates that a profile ID is clean, non-empty, and alphanumeric with underscores/hyphens."""
    if not profile_id or not isinstance(profile_id, str):
        raise ValidationError("Profile ID cannot be empty.")
    cleaned = profile_id.strip()
    if not re.match(r"^[a-zA-Z0-9_\-]+$", cleaned):
        raise ValidationError("Profile ID must contain only alphanumeric characters, dashes, or underscores.")
    if len(cleaned) > 64:
        raise ValidationError("Profile ID must be 64 characters or fewer.")
    return cleaned


def validate_display_name(display_name: str) -> str:
    """Validates user display name or pseudonym."""
    if not display_name or not isinstance(display_name, str):
        raise ValidationError("Display name cannot be empty.")
    cleaned = display_name.strip()
    if len(cleaned) < 2:
        raise ValidationError("Display name must be at least 2 characters long.")
    if len(cleaned) > 50:
        raise ValidationError("Display name must be 50 characters or fewer.")
    return cleaned


def validate_severity(severity: Any) -> int:
    """Validates that symptom severity is an integer between 1 and 10."""
    try:
        val = int(severity)
    except (TypeError, ValueError):
        raise ValidationError("Severity must be an integer between 1 and 10.")
    if val < 1 or val > 10:
        raise ValidationError("Severity rating must be between 1 (mild) and 10 (debilitating).")
    return val


def validate_onset_date(onset_date_val: Any) -> str:
    """Validates onset date is a valid date object or YYYY-MM-DD string, not in the distant future."""
    if isinstance(onset_date_val, (datetime, date)):
        date_obj = onset_date_val if isinstance(onset_date_val, date) else onset_date_val.date()
        date_str = date_obj.strftime("%Y-%m-%d")
    elif isinstance(onset_date_val, str):
        date_str = onset_date_val.strip()
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError("Onset date must be in YYYY-MM-DD format.")
    else:
        raise ValidationError("Onset date is required.")

    # Allow up to tomorrow to accommodate international timezones
    today = date.today()
    if (date_obj - today).days > 1:
        raise ValidationError("Onset date cannot be set to a future date beyond tomorrow.")
    if (today - date_obj).days > 365 * 10:
        raise ValidationError("Onset date cannot be older than 10 years.")
    return date_str


def validate_duration_hours(duration: Any) -> Optional[float]:
    """Validates optional duration in hours (0 to 720 hours / 30 days)."""
    if duration is None or duration == "":
        return None
    try:
        val = float(duration)
    except (TypeError, ValueError):
        raise ValidationError("Duration must be a valid numeric value in hours.")
    if val < 0:
        raise ValidationError("Duration cannot be negative.")
    if val > 720:
        raise ValidationError("Duration cannot exceed 720 hours (30 days). For ongoing symptoms, select status 'Ongoing'.")
    return round(val, 2)


def validate_symptom_name(symptom: str) -> str:
    """Validates symptom name is non-empty and reasonably sized."""
    if not symptom or not isinstance(symptom, str):
        raise ValidationError("Symptom name is required.")
    cleaned = symptom.strip()
    if len(cleaned) < 2:
        raise ValidationError("Symptom name must be at least 2 characters.")
    if len(cleaned) > 100:
        raise ValidationError("Symptom name cannot exceed 100 characters.")
    return cleaned


def validate_category(category: str) -> str:
    """Validates category is non-empty."""
    if not category or not isinstance(category, str):
        raise ValidationError("Category is required.")
    cleaned = category.strip()
    if len(cleaned) < 2:
        raise ValidationError("Category name is too short.")
    return cleaned


def validate_symptom_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates a complete symptom entry payload before database persistence.
    Returns the sanitized, validated dictionary.
    """
    validated = {}
    validated["profile_id"] = validate_profile_id(data.get("profile_id", ""))
    validated["category"] = validate_category(data.get("category", ""))
    validated["symptom"] = validate_symptom_name(data.get("symptom", ""))
    validated["onset_date"] = validate_onset_date(data.get("onset_date"))
    validated["severity"] = validate_severity(data.get("severity"))
    validated["duration_hours"] = validate_duration_hours(data.get("duration_hours"))
    
    # Status
    status = data.get("status", "Ongoing")
    if status not in ("Ongoing", "Resolved", "Intermittent"):
        status = "Ongoing"
    validated["status"] = status
    
    # Time
    onset_time = data.get("onset_time")
    if onset_time:
        validated["onset_time"] = str(onset_time).strip()
    else:
        validated["onset_time"] = None

    # Impact
    impact = data.get("impact", "None")
    validated["impact"] = str(impact).strip() if impact else "None"

    # Notes
    notes = data.get("notes", "")
    validated["notes"] = str(notes).strip() if notes else ""

    # Context (Sleep, stress, energy, cycle_phase)
    context = data.get("context")
    if isinstance(context, dict):
        validated["context"] = context
    else:
        validated["context"] = {}

    return validated
