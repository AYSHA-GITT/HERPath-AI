"""
HERPath AI - Data Models
recHERsion 2026 | PS1: Women's Healthcare
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
from datetime import datetime, date
import json


@dataclass
class UserProfile:
    id: str
    display_name: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    preferences: Dict[str, Any] = field(default_factory=lambda: {
        "track_menstrual": True,
        "theme_contrast": "standard",
        "consent_acknowledged": True
    })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "created_at": self.created_at,
            "preferences": self.preferences
        }


@dataclass
class SymptomEntry:
    id: Optional[int]
    profile_id: str
    category: str
    symptom: str
    onset_date: str  # YYYY-MM-DD
    severity: int     # 1 - 10
    duration_hours: Optional[float] = None
    status: str = "Ongoing"  # 'Ongoing', 'Resolved', 'Intermittent'
    onset_time: Optional[str] = None
    impact: Optional[str] = "None"
    notes: Optional[str] = ""
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "category": self.category,
            "symptom": self.symptom,
            "onset_date": self.onset_date,
            "severity": self.severity,
            "duration_hours": self.duration_hours,
            "status": self.status,
            "onset_time": self.onset_time,
            "impact": self.impact,
            "notes": self.notes,
            "context": self.context,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_row(cls, row: tuple) -> "SymptomEntry":
        # row: (id, profile_id, category, symptom, onset_date, onset_time,
        #       severity, duration_hours, status, impact, notes, context_json, created_at, updated_at)
        ctx_data = {}
        if row[11]:
            try:
                ctx_data = json.loads(row[11])
            except Exception:
                ctx_data = {}
        return cls(
            id=row[0],
            profile_id=row[1],
            category=row[2],
            symptom=row[3],
            onset_date=row[4],
            onset_time=row[5],
            severity=row[6],
            duration_hours=row[7],
            status=row[8],
            impact=row[9],
            notes=row[10] or "",
            context=ctx_data,
            created_at=row[12],
            updated_at=row[13]
        )


@dataclass
class MedicationEntry:
    id: Optional[int]
    profile_id: str
    name: str
    category: str  # Prescription, OTC / Supplement, Lifestyle / Therapy
    dosage: Optional[str] = ""
    frequency: Optional[str] = ""
    started_date: Optional[str] = None
    notes: Optional[str] = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "name": self.name,
            "category": self.category,
            "dosage": self.dosage,
            "frequency": self.frequency,
            "started_date": self.started_date,
            "notes": self.notes,
            "created_at": self.created_at
        }

    @classmethod
    def from_row(cls, row: tuple) -> "MedicationEntry":
        # (id, profile_id, name, category, dosage, frequency, started_date, notes, created_at)
        return cls(
            id=row[0],
            profile_id=row[1],
            name=row[2],
            category=row[3],
            dosage=row[4] or "",
            frequency=row[5] or "",
            started_date=row[6],
            notes=row[7] or "",
            created_at=row[8]
        )

