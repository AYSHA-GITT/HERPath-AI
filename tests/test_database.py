"""
HERPath AI - Automated Database Unit Tests
recHERsion 2026 | PS1: Women's Healthcare
"""

import pytest
import sqlite3
import os
import gc
import tempfile
from models import UserProfile, SymptomEntry
from database import (
    init_db,
    create_profile,
    get_profile,
    delete_profile,
    list_profiles,
    add_symptom,
    get_symptoms,
    get_symptom_by_id,
    update_symptom,
    delete_symptom,
    clear_profile_symptoms
)


@pytest.fixture
def temp_db():
    """Creates an isolated temporary SQLite database for test execution."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    gc.collect()
    try:
        if os.path.exists(path):
            os.remove(path)
    except PermissionError:
        pass


def test_profile_creation_and_retrieval(temp_db):
    """Verifies that user profiles can be created and retrieved accurately."""
    profile = create_profile("test_user_1", "Test User", {"track_menstrual": True}, temp_db)
    assert profile.id == "test_user_1"
    assert profile.display_name == "Test User"

    fetched = get_profile("test_user_1", temp_db)
    assert fetched is not None
    assert fetched.display_name == "Test User"
    assert fetched.preferences.get("track_menstrual") is True


def test_symptom_add_and_persistence(temp_db):
    """Verifies that symptom records persist in SQLite and return an ID."""
    create_profile("user_a", "User A", db_path=temp_db)
    entry = SymptomEntry(
        id=None,
        profile_id="user_a",
        category="Neurological & Head",
        symptom="Migraine",
        onset_date="2026-10-20",
        severity=7,
        duration_hours=6.5,
        status="Resolved",
        impact="Moderate",
        notes="Photophobia",
        context={"sleep": "Disrupted"}
    )
    entry_id = add_symptom(entry, temp_db)
    assert entry_id > 0

    records = get_symptoms("user_a", db_path=temp_db)
    assert len(records) == 1
    assert records[0].symptom == "Migraine"
    assert records[0].severity == 7
    assert records[0].duration_hours == 6.5
    assert records[0].context.get("sleep") == "Disrupted"


def test_profile_scoped_isolation(temp_db):
    """Verifies that symptom queries strictly isolate data between different profiles."""
    create_profile("user_one", "User One", db_path=temp_db)
    create_profile("user_two", "User Two", db_path=temp_db)

    # Add symptom to User One
    add_symptom(SymptomEntry(
        id=None,
        profile_id="user_one",
        category="Pelvic & Menstrual",
        symptom="Pelvic Pain",
        onset_date="2026-10-21",
        severity=6
    ), temp_db)

    # Add symptom to User Two
    add_symptom(SymptomEntry(
        id=None,
        profile_id="user_two",
        category="Systemic & Energy",
        symptom="Fatigue",
        onset_date="2026-10-22",
        severity=4
    ), temp_db)

    # Verify User One only sees Pelvic Pain
    u1_records = get_symptoms("user_one", db_path=temp_db)
    assert len(u1_records) == 1
    assert u1_records[0].symptom == "Pelvic Pain"

    # Verify User Two only sees Fatigue
    u2_records = get_symptoms("user_two", db_path=temp_db)
    assert len(u2_records) == 1
    assert u2_records[0].symptom == "Fatigue"


def test_update_symptom(temp_db):
    """Verifies that an existing symptom can be modified and persists the update."""
    create_profile("user_b", "User B", db_path=temp_db)
    entry_id = add_symptom(SymptomEntry(
        id=None,
        profile_id="user_b",
        category="Systemic & Energy",
        symptom="Fatigue",
        onset_date="2026-10-15",
        severity=4,
        status="Ongoing"
    ), temp_db)

    entry = get_symptom_by_id(entry_id, "user_b", temp_db)
    assert entry is not None
    entry.severity = 8
    entry.status = "Resolved"
    entry.notes = "Updated doctor observation."

    success = update_symptom(entry, temp_db)
    assert success is True

    updated_entry = get_symptom_by_id(entry_id, "user_b", temp_db)
    assert updated_entry.severity == 8
    assert updated_entry.status == "Resolved"
    assert updated_entry.notes == "Updated doctor observation."


def test_delete_symptom(temp_db):
    """Verifies that a symptom can be safely deleted."""
    create_profile("user_c", "User C", db_path=temp_db)
    entry_id = add_symptom(SymptomEntry(
        id=None,
        profile_id="user_c",
        category="Urinary & Pelvic Floor",
        symptom="Burning Urination",
        onset_date="2026-10-10",
        severity=5
    ), temp_db)

    assert len(get_symptoms("user_c", db_path=temp_db)) == 1
    deleted = delete_symptom(entry_id, "user_c", temp_db)
    assert deleted is True
    assert len(get_symptoms("user_c", db_path=temp_db)) == 0


def test_cascade_delete_profile(temp_db):
    """Verifies that deleting a profile removes all associated symptoms via cascade."""
    create_profile("user_del", "User to Delete", db_path=temp_db)
    add_symptom(SymptomEntry(
        id=None,
        profile_id="user_del",
        category="Neurological & Head",
        symptom="Tension Headache",
        onset_date="2026-10-11",
        severity=3
    ), temp_db)

    assert len(get_symptoms("user_del", db_path=temp_db)) == 1
    delete_profile("user_del", temp_db)
    assert get_profile("user_del", temp_db) is None
    assert len(get_symptoms("user_del", db_path=temp_db)) == 0


def test_foreign_key_enforcement(temp_db):
    """Verifies that inserting a symptom for a non-existent profile violates foreign key constraints."""
    with pytest.raises(sqlite3.IntegrityError):
        conn = sqlite3.connect(temp_db)
        try:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("""
                INSERT INTO symptom_entries (
                    profile_id, category, symptom, onset_date, severity,
                    status, created_at, updated_at
                ) VALUES ('non_existent_profile', 'Test', 'Test Sym', '2026-10-20', 5, 'Ongoing', 'now', 'now');
            """)
            conn.commit()
        finally:
            conn.close()
