"""
HERPath AI - Authentication, PIN Security & User Onboarding Service
recHERsion 2026 | PS1: Women's Healthcare

Provides privacy-first, on-device user authentication, SHA-256 PIN/password hashing,
credential verification, and new user registration with health onboarding profile defaults.
"""

import hashlib
import json
from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime

from database import (
    get_profile,
    create_profile,
    list_profiles,
    update_profile_preferences,
    get_symptoms,
    get_medications
)
from models import UserProfile
from validators import (
    validate_profile_id,
    validate_display_name,
    ValidationError
)

AUTH_SALT = "herpath_secure_salt_2026"


def hash_credential(credential: str, salt: str = AUTH_SALT) -> str:
    """
    Computes a salted SHA-256 digest of a PIN or password.
    Ensures user credentials are never stored in plain text.
    """
    if not credential:
        return ""
    combined = f"{salt}:{credential.strip()}:{salt}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def verify_credential(credential: str, stored_hash: str, salt: str = AUTH_SALT) -> bool:
    """
    Verifies a plain text credential against a stored SHA-256 hash.
    """
    if not stored_hash:
        return True  # No PIN configured
    if not credential:
        return False
    return hash_credential(credential, salt) == stored_hash


def has_pin_protection(profile: UserProfile) -> bool:
    """
    Returns True if the given profile has a PIN or password configured.
    """
    if not profile or not profile.preferences:
        return False
    return bool(profile.preferences.get("pin_hash"))


def register_user(
    profile_id: str,
    display_name: str,
    pin: Optional[str] = None,
    preferences: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None
) -> UserProfile:
    """
    Registers and persists a new user profile with input validation,
    optional salted PIN hashing, and default health preferences.

    Raises ValidationError if profile_id or display_name is invalid or already taken.
    """
    # 1. Validate inputs
    clean_id = validate_profile_id(profile_id).lower()
    clean_name = validate_display_name(display_name)

    # 2. Check for duplicate profile ID
    existing = get_profile(clean_id, db_path=db_path)
    if existing is not None:
        raise ValidationError(f"Profile ID '{clean_id}' is already registered. Please choose another username or log in.")

    # 3. Build preferences dict
    pref = preferences.copy() if preferences else {}
    if "track_menstrual" not in pref:
        pref["track_menstrual"] = True
    if "consent_acknowledged" not in pref:
        pref["consent_acknowledged"] = True
    if "focus_areas" not in pref:
        pref["focus_areas"] = ["General Wellness"]

    # 4. Hash PIN if provided
    if pin and pin.strip():
        pref["pin_hash"] = hash_credential(pin)

    # 5. Persist profile
    return create_profile(clean_id, clean_name, pref, db_path=db_path)


def find_profile_by_identifier(identifier: str, db_path: Optional[str] = None) -> Optional[UserProfile]:
    """Finds a profile by ID or by matching display name (case-insensitive)."""
    if not identifier:
        return None
    clean = identifier.strip().lower()
    # 1. Direct ID match
    prof = get_profile(clean, db_path=db_path)
    if prof:
        return prof
    # 2. Match on display name (case-insensitive)
    all_profs = list_profiles(db_path=db_path)
    for p in all_profs:
        if p.display_name.lower() == clean:
            return p
    # 3. Match on display name before parenthesis (e.g. 'Priya' matches 'Priya (PCOS & Migraine Tracking)')
    for p in all_profs:
        name_part = p.display_name.split("(")[0].strip().lower()
        if name_part == clean:
            return p
    # 4. Prefix match
    for p in all_profs:
        if p.display_name.lower().startswith(clean):
            return p
    return None


def authenticate_user(
    profile_id: str,
    pin: Optional[str] = None,
    db_path: Optional[str] = None
) -> Tuple[bool, str, Optional[UserProfile]]:
    """
    Authenticates an existing user profile by ID or username and optional PIN.

    Returns:
        (success: bool, message: str, profile: Optional[UserProfile])
    """
    if not profile_id or not profile_id.strip():
        return False, "Please enter your username or account name.", None

    clean_id = profile_id.strip().lower()
    profile = find_profile_by_identifier(clean_id, db_path=db_path)

    if profile is None:
        return False, f"Profile '{clean_id}' does not exist. Please check the ID or create a new account.", None

    stored_pin_hash = profile.preferences.get("pin_hash")

    # If profile has PIN protection
    if stored_pin_hash:
        if not pin or not pin.strip():
            return False, "This account is protected by a PIN. Please enter your PIN to continue.", None
        if not verify_credential(pin, stored_pin_hash):
            return False, "Incorrect security PIN. Please try again.", None

    return True, f"Welcome back, {profile.display_name}!", profile


def set_user_pin(profile_id: str, new_pin: str, db_path: Optional[str] = None) -> bool:
    """
    Sets or updates a PIN for an existing profile.
    """
    profile = get_profile(profile_id, db_path=db_path)
    if not profile:
        return False
    prefs = profile.preferences.copy()
    if new_pin and new_pin.strip():
        prefs["pin_hash"] = hash_credential(new_pin)
    else:
        prefs.pop("pin_hash", None)
    return update_profile_preferences(profile_id, prefs, db_path=db_path)


def remove_user_pin(profile_id: str, db_path: Optional[str] = None) -> bool:
    """
    Removes PIN protection from an existing profile.
    """
    return set_user_pin(profile_id, "", db_path=db_path)


def get_account_stats(profile_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns high-level statistics for an account (symptoms count, medications count, days active).
    """
    profile = get_profile(profile_id, db_path=db_path)
    if not profile:
        return {"symptoms_count": 0, "medications_count": 0, "created_at": ""}

    symptoms = get_symptoms(profile_id, db_path=db_path)
    medications = get_medications(profile_id, db_path=db_path)

    created_dt_str = profile.created_at[:10] if profile.created_at else "Recently"

    return {
        "symptoms_count": len(symptoms),
        "medications_count": len(medications),
        "created_at": created_dt_str,
        "has_pin": has_pin_protection(profile),
        "focus_areas": profile.preferences.get("focus_areas", ["General Wellness"]),
        "track_menstrual": profile.preferences.get("track_menstrual", True)
    }
