"""
HERPath AI - Symptom Tracker Service Layer
recHERsion 2026 | PS1: Women's Healthcare
"""

from typing import List, Optional, Dict, Any, Tuple
from models import SymptomEntry
from database import (
    add_symptom,
    get_symptoms,
    get_symptom_by_id,
    update_symptom,
    delete_symptom
)
from validators import validate_symptom_payload, ValidationError


class SymptomTrackerService:
    """Provides high-level business operations for recording, editing, and querying symptoms."""

    @staticmethod
    def record_symptom(
        profile_id: str,
        category: str,
        symptom: str,
        onset_date: Any,
        severity: int,
        duration_hours: Optional[float] = None,
        status: str = "Ongoing",
        onset_time: Optional[str] = None,
        impact: Optional[str] = "None",
        notes: str = "",
        context: Optional[Dict[str, Any]] = None,
        db_path: Optional[str] = None
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Validates and records a new symptom entry.
        Returns: (success: bool, entry_id: Optional[int], error_message: Optional[str])
        """
        try:
            entry = SymptomEntry(
                id=None,
                profile_id=profile_id,
                category=category,
                symptom=symptom,
                onset_date=str(onset_date),
                severity=severity,
                duration_hours=duration_hours,
                status=status,
                onset_time=onset_time,
                impact=impact,
                notes=notes,
                context=context or {}
            )
            new_id = add_symptom(entry, db_path)
            return True, new_id, None
        except ValidationError as ve:
            return False, None, str(ve)
        except Exception as e:
            return False, None, f"Database persistence error: {str(e)}"

    @staticmethod
    def edit_symptom(
        entry_id: int,
        profile_id: str,
        category: str,
        symptom: str,
        onset_date: Any,
        severity: int,
        duration_hours: Optional[float] = None,
        status: str = "Ongoing",
        onset_time: Optional[str] = None,
        impact: Optional[str] = "None",
        notes: str = "",
        context: Optional[Dict[str, Any]] = None,
        db_path: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Updates an existing symptom entry.
        Returns: (success: bool, error_message: Optional[str])
        """
        try:
            entry = SymptomEntry(
                id=entry_id,
                profile_id=profile_id,
                category=category,
                symptom=symptom,
                onset_date=str(onset_date),
                severity=severity,
                duration_hours=duration_hours,
                status=status,
                onset_time=onset_time,
                impact=impact,
                notes=notes,
                context=context or {}
            )
            updated = update_symptom(entry, db_path)
            if updated:
                return True, None
            return False, "Record could not be found or updated."
        except ValidationError as ve:
            return False, str(ve)
        except Exception as e:
            return False, f"Update failed: {str(e)}"

    @staticmethod
    def remove_symptom(entry_id: int, profile_id: str, db_path: Optional[str] = None) -> bool:
        """Deletes a symptom entry owned by the profile."""
        return delete_symptom(entry_id, profile_id, db_path)

    @staticmethod
    def get_history(
        profile_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        symptom_name: Optional[str] = None,
        status: Optional[str] = None,
        db_path: Optional[str] = None
    ) -> List[SymptomEntry]:
        """Fetches filtered symptom entries for the profile."""
        return get_symptoms(
            profile_id=profile_id,
            start_date=start_date,
            end_date=end_date,
            category=category,
            symptom_name=symptom_name,
            status=status,
            db_path=db_path
        )

    @staticmethod
    def get_entry(entry_id: int, profile_id: str, db_path: Optional[str] = None) -> Optional[SymptomEntry]:
        """Retrieves an entry by ID for the profile."""
        return get_symptom_by_id(entry_id, profile_id, db_path)
