"""
HERPath AI - Authentication & User Registration Unit Tests
recHERsion 2026 | PS1: Women's Healthcare
"""

import pytest
import os
import gc
import tempfile

from database import init_db, get_profile, list_profiles
from validators import ValidationError
from auth import (
    hash_credential,
    verify_credential,
    has_pin_protection,
    register_user,
    authenticate_user,
    set_user_pin,
    remove_user_pin,
    get_account_stats
)


@pytest.fixture
def auth_db():
    """Provides a fresh isolated SQLite database for authentication testing."""
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


def test_hash_and_verify_credential():
    """Verifies that credential hashing is salted, non-reversible, and correctly verifies."""
    pin = "1234"
    hashed = hash_credential(pin)
    assert hashed != pin
    assert len(hashed) == 64  # SHA-256 hex length
    assert verify_credential("1234", hashed) is True
    assert verify_credential("9999", hashed) is False
    assert verify_credential("", hashed) is False


def test_register_new_user_success(auth_db):
    """Tests successful registration of a new user with PIN and health focus areas."""
    user = register_user(
        profile_id="maya_health",
        display_name="Maya Sharma",
        pin="4321",
        preferences={
            "track_menstrual": True,
            "focus_areas": ["PCOS", "Migraines"]
        },
        db_path=auth_db
    )
    assert user.id == "maya_health"
    assert user.display_name == "Maya Sharma"
    assert has_pin_protection(user) is True
    assert user.preferences["focus_areas"] == ["PCOS", "Migraines"]

    # Verify persisted in database
    fetched = get_profile("maya_health", db_path=auth_db)
    assert fetched is not None
    assert fetched.display_name == "Maya Sharma"


def test_register_duplicate_profile_id_raises_error(auth_db):
    """Ensures registering an existing profile ID fails with ValidationError."""
    register_user("unique_id_1", "User One", db_path=auth_db)
    with pytest.raises(ValidationError) as exc_info:
        register_user("unique_id_1", "User Two", db_path=auth_db)
    assert "already registered" in str(exc_info.value).lower()


def test_register_invalid_inputs(auth_db):
    """Ensures invalid ID or name raises ValidationError."""
    with pytest.raises(ValidationError):
        register_user("bad id with spaces", "Valid Name", db_path=auth_db)

    with pytest.raises(ValidationError):
        register_user("valid_id", "A", db_path=auth_db)  # Too short


def test_authenticate_user_with_pin(auth_db):
    """Tests authentication flows for a PIN-protected user account."""
    register_user("secure_user", "Secure User", pin="7890", db_path=auth_db)

    # Correct PIN
    success, msg, profile = authenticate_user("secure_user", "7890", db_path=auth_db)
    assert success is True
    assert profile is not None
    assert profile.id == "secure_user"

    # Incorrect PIN
    success, msg, profile = authenticate_user("secure_user", "0000", db_path=auth_db)
    assert success is False
    assert "incorrect" in msg.lower()
    assert profile is None

    # Missing PIN for protected account
    success, msg, profile = authenticate_user("secure_user", "", db_path=auth_db)
    assert success is False
    assert "protected by a pin" in msg.lower()


def test_authenticate_user_without_pin(auth_db):
    """Tests passwordless/demo authentication for profiles without a PIN."""
    register_user("open_user", "Open User", pin=None, db_path=auth_db)

    success, msg, profile = authenticate_user("open_user", db_path=auth_db)
    assert success is True
    assert profile is not None
    assert profile.id == "open_user"


def test_authenticate_nonexistent_user(auth_db):
    """Tests authentication failure when profile does not exist."""
    success, msg, profile = authenticate_user("ghost_user", db_path=auth_db)
    assert success is False
    assert "does not exist" in msg.lower()


def test_set_and_remove_pin(auth_db):
    """Tests adding, changing, and removing user PIN."""
    register_user("pin_tester", "Pin Tester", pin=None, db_path=auth_db)
    prof = get_profile("pin_tester", db_path=auth_db)
    assert has_pin_protection(prof) is False

    # Set PIN
    assert set_user_pin("pin_tester", "5555", db_path=auth_db) is True
    prof = get_profile("pin_tester", db_path=auth_db)
    assert has_pin_protection(prof) is True

    # Authenticate with new PIN
    success, _, _ = authenticate_user("pin_tester", "5555", db_path=auth_db)
    assert success is True

    # Remove PIN
    assert remove_user_pin("pin_tester", db_path=auth_db) is True
    prof = get_profile("pin_tester", db_path=auth_db)
    assert has_pin_protection(prof) is False


def test_get_account_stats(auth_db):
    """Tests retrieving account statistics."""
    register_user("stats_user", "Stats User", db_path=auth_db)
    stats = get_account_stats("stats_user", db_path=auth_db)
    assert stats["symptoms_count"] == 0
    assert stats["medications_count"] == 0
    assert stats["has_pin"] is False


def test_update_pin_ui_feedback():
    """Verifies that updating the security PIN displays a visible confirmation message to the user."""
    from pathlib import Path
    from streamlit.testing.v1 import AppTest

    app_file = str(Path(__file__).resolve().parent.parent / "app.py")
    at = AppTest.from_file(app_file, default_timeout=30)
    at.session_state["is_logged_in"] = True
    at.session_state["current_profile_id"] = "demo_priya"
    at.session_state["navigation"] = "Account & Login"
    at.run()
    assert not at.exception

    try:
        # Locate the change PIN input and update button
        pin_inputs = [ti for ti in at.text_input if ti.key and "change_pin_field" in ti.key]
        assert len(pin_inputs) > 0
        pin_inputs[0].set_value("9876")

        update_buttons = [b for b in at.button if b.key == "btn_update_pin"]
        assert len(update_buttons) > 0
        update_buttons[0].click().run()

        assert not at.exception
        # Check that success message is displayed on screen
        success_texts = [s.value for s in at.success]
        combined_success = " ".join(success_texts)
        assert "Security PIN updated successfully" in combined_success
    finally:
        set_user_pin("demo_priya", "1234")

