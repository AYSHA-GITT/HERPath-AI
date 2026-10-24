"""
HERPath AI - SQLite Database Layer
recHERsion 2026 | PS1: Women's Healthcare
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from config import DATABASE_PATH
from models import UserProfile, SymptomEntry
from validators import validate_symptom_payload, ValidationError


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Creates and returns an SQLite connection with WAL mode and foreign key enforcement.
    """
    path = db_path or DATABASE_PATH
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


@contextmanager
def db_session(db_path: Optional[str] = None):
    """
    Context manager providing safe transaction management and guaranteed connection closing.
    """
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Optional[str] = None) -> None:
    """
    Initializes the SQLite schema with tables, constraints, and indexes.
    Seeds initial demonstration profiles if the table is empty.
    """
    with db_session(db_path) as cursor:
        # 1. Profiles Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                preferences_json TEXT NOT NULL
            );
        """)

        # 2. Symptom Entries Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS symptom_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT NOT NULL,
                category TEXT NOT NULL,
                symptom TEXT NOT NULL,
                onset_date TEXT NOT NULL,
                onset_time TEXT,
                severity INTEGER NOT NULL CHECK(severity >= 1 AND severity <= 10),
                duration_hours REAL,
                status TEXT NOT NULL DEFAULT 'Ongoing' CHECK(status IN ('Ongoing', 'Resolved', 'Intermittent')),
                impact TEXT DEFAULT 'None',
                notes TEXT,
                context_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
            );
        """)

        # 3. Indices for fast querying and filtering
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_symptoms_profile_date 
            ON symptom_entries(profile_id, onset_date DESC);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_symptoms_category 
            ON symptom_entries(profile_id, category);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_symptoms_name 
            ON symptom_entries(profile_id, symptom);
        """)

        # 4. Seed initial default demo profile if empty
        cursor.execute("SELECT COUNT(*) FROM profiles;")
        if cursor.fetchone()[0] == 0:
            default_profiles = [
                ("demo_priya", "Priya (PCOS & Migraine Tracking)", json.dumps({
                    "track_menstrual": True,
                    "consent_acknowledged": True,
                    "focus_areas": ["PCOS", "Migraine", "Energy"]
                })),
                ("demo_ananya", "Ananya (Perimenopause & Sleep)", json.dumps({
                    "track_menstrual": True,
                    "consent_acknowledged": True,
                    "focus_areas": ["Perimenopause", "Sleep", "Mood"]
                })),
                ("demo_elena", "Elena (Endometriosis & Pelvic Health)", json.dumps({
                    "track_menstrual": True,
                    "consent_acknowledged": True,
                    "focus_areas": ["Pelvic Pain", "Fatigue"]
                }))
            ]
            now_iso = datetime.now().isoformat()
            cursor.executemany(
                "INSERT INTO profiles (id, display_name, created_at, preferences_json) VALUES (?, ?, ?, ?);",
                [(p[0], p[1], now_iso, p[2]) for p in default_profiles]
            )


# ==========================================
# Profile Operations
# ==========================================

def create_profile(profile_id: str, display_name: str, preferences: Optional[Dict[str, Any]] = None, db_path: Optional[str] = None) -> UserProfile:
    """Creates a new user profile with scoped storage."""
    pref = preferences or {"track_menstrual": True, "consent_acknowledged": True}
    now_iso = datetime.now().isoformat()
    with db_session(db_path) as cursor:
        cursor.execute(
            "INSERT INTO profiles (id, display_name, created_at, preferences_json) VALUES (?, ?, ?, ?);",
            (profile_id, display_name, now_iso, json.dumps(pref))
        )
    return UserProfile(id=profile_id, display_name=display_name, created_at=now_iso, preferences=pref)


def get_profile(profile_id: str, db_path: Optional[str] = None) -> Optional[UserProfile]:
    """Retrieves a single user profile by ID."""
    with db_session(db_path) as cursor:
        cursor.execute("SELECT id, display_name, created_at, preferences_json FROM profiles WHERE id = ?;", (profile_id,))
        row = cursor.fetchone()
        if not row:
            return None
        try:
            pref = json.loads(row[3])
        except Exception:
            pref = {}
        return UserProfile(id=row[0], display_name=row[1], created_at=row[2], preferences=pref)


def list_profiles(db_path: Optional[str] = None) -> List[UserProfile]:
    """Lists all available local profiles."""
    with db_session(db_path) as cursor:
        cursor.execute("SELECT id, display_name, created_at, preferences_json FROM profiles ORDER BY display_name ASC;")
        rows = cursor.fetchall()
        profiles = []
        for r in rows:
            try:
                pref = json.loads(r[3])
            except Exception:
                pref = {}
            profiles.append(UserProfile(id=r[0], display_name=r[1], created_at=r[2], preferences=pref))
        return profiles


def update_profile_preferences(profile_id: str, preferences: Dict[str, Any], db_path: Optional[str] = None) -> bool:
    """Updates preferences for a given profile."""
    with db_session(db_path) as cursor:
        cursor.execute(
            "UPDATE profiles SET preferences_json = ? WHERE id = ?;",
            (json.dumps(preferences), profile_id)
        )
        return cursor.rowcount > 0


def delete_profile(profile_id: str, db_path: Optional[str] = None) -> bool:
    """
    Deletes a user profile and all associated symptom records via SQLite cascade.
    Guarantees complete removal of user's local records.
    """
    with db_session(db_path) as cursor:
        cursor.execute("DELETE FROM profiles WHERE id = ?;", (profile_id,))
        return cursor.rowcount > 0


# ==========================================
# Symptom CRUD Operations (Profile-Scoped)
# ==========================================

def add_symptom(entry: SymptomEntry, db_path: Optional[str] = None) -> int:
    """
    Adds a validated symptom entry to the database for the scoped profile.
    Returns the newly created auto-incrementing entry ID.
    """
    payload = entry.to_dict()
    val = validate_symptom_payload(payload)
    now_iso = datetime.now().isoformat()
    
    with db_session(db_path) as cursor:
        cursor.execute("""
            INSERT INTO symptom_entries (
                profile_id, category, symptom, onset_date, onset_time,
                severity, duration_hours, status, impact, notes, context_json,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            val["profile_id"],
            val["category"],
            val["symptom"],
            val["onset_date"],
            val["onset_time"],
            val["severity"],
            val["duration_hours"],
            val["status"],
            val["impact"],
            val["notes"],
            json.dumps(val["context"]),
            now_iso,
            now_iso
        ))
        return cursor.lastrowid


def get_symptoms(
    profile_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    symptom_name: Optional[str] = None,
    status: Optional[str] = None,
    db_path: Optional[str] = None
) -> List[SymptomEntry]:
    """
    Fetches symptom entries for a specific profile, with optional filtering.
    Always scopes queries by profile_id to prevent any cross-profile data leakage.
    """
    query = """
        SELECT id, profile_id, category, symptom, onset_date, onset_time,
               severity, duration_hours, status, impact, notes, context_json,
               created_at, updated_at
        FROM symptom_entries
        WHERE profile_id = ?
    """
    params: List[Any] = [profile_id]

    if start_date:
        query += " AND onset_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND onset_date <= ?"
        params.append(end_date)
    if category and category != "All Categories":
        query += " AND category = ?"
        params.append(category)
    if symptom_name and symptom_name != "All Symptoms":
        query += " AND symptom = ?"
        params.append(symptom_name)
    if status and status != "All":
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY onset_date DESC, id DESC;"

    with db_session(db_path) as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [SymptomEntry.from_row(r) for r in rows]


def get_symptom_by_id(entry_id: int, profile_id: str, db_path: Optional[str] = None) -> Optional[SymptomEntry]:
    """Fetches a specific symptom entry by ID, strictly scoped to the owner profile."""
    with db_session(db_path) as cursor:
        cursor.execute("""
            SELECT id, profile_id, category, symptom, onset_date, onset_time,
                   severity, duration_hours, status, impact, notes, context_json,
                   created_at, updated_at
            FROM symptom_entries
            WHERE id = ? AND profile_id = ?;
        """, (entry_id, profile_id))
        row = cursor.fetchone()
        if not row:
            return None
        return SymptomEntry.from_row(row)


def update_symptom(entry: SymptomEntry, db_path: Optional[str] = None) -> bool:
    """Updates an existing symptom entry. Validates and ensures profile match."""
    if not entry.id:
        raise ValidationError("Entry ID is required for update.")

    payload = entry.to_dict()
    val = validate_symptom_payload(payload)
    now_iso = datetime.now().isoformat()

    with db_session(db_path) as cursor:
        cursor.execute("""
            UPDATE symptom_entries
            SET category = ?,
                symptom = ?,
                onset_date = ?,
                onset_time = ?,
                severity = ?,
                duration_hours = ?,
                status = ?,
                impact = ?,
                notes = ?,
                context_json = ?,
                updated_at = ?
            WHERE id = ? AND profile_id = ?;
        """, (
            val["category"],
            val["symptom"],
            val["onset_date"],
            val["onset_time"],
            val["severity"],
            val["duration_hours"],
            val["status"],
            val["impact"],
            val["notes"],
            json.dumps(val["context"]),
            now_iso,
            entry.id,
            val["profile_id"]
        ))
        return cursor.rowcount > 0


def delete_symptom(entry_id: int, profile_id: str, db_path: Optional[str] = None) -> bool:
    """Deletes a symptom entry, ensuring ownership by the specified profile."""
    with db_session(db_path) as cursor:
        cursor.execute(
            "DELETE FROM symptom_entries WHERE id = ? AND profile_id = ?;",
            (entry_id, profile_id)
        )
        return cursor.rowcount > 0


def clear_profile_symptoms(profile_id: str, db_path: Optional[str] = None) -> int:
    """Clears all symptom entries for a specific profile without deleting the profile."""
    with db_session(db_path) as cursor:
        cursor.execute("DELETE FROM symptom_entries WHERE profile_id = ?;", (profile_id,))
        return cursor.rowcount
