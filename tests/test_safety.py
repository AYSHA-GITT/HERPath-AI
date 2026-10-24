"""
HERPath AI - Automated Safety Navigator Unit Tests
recHERsion 2026 | PS1: Women's Healthcare
"""

import pytest
from safety_navigator import SafetyNavigator
from config import (
    PRIORITY_EMERGENCY,
    PRIORITY_PROMPT,
    PRIORITY_ROUTINE,
    PRIORITY_SELFCARE
)


def test_routine_mild_scenario():
    """Ensures mild symptoms with no red flags route to supportive self-care and monitoring."""
    assessment = SafetyNavigator.evaluate(
        symptom="Tension Headache",
        category="Neurological & Head",
        severity=3,
        duration_hours=2.0,
        notes="Spent long hours on computer."
    )
    assert assessment.priority == PRIORITY_SELFCARE
    assert "MILD" in assessment.title or "HEALTH EDUCATION" in assessment.title
    assert len(assessment.recommended_actions) > 0
    assert assessment.disclaimer is not None


def test_routine_moderate_consultation_scenario():
    """Ensures moderate symptoms (severity 4-7) suggest routine clinician review."""
    assessment = SafetyNavigator.evaluate(
        symptom="Pelvic Pain / Cramping",
        category="Pelvic & Menstrual",
        severity=6,
        duration_hours=12.0,
        notes="Worsening cramps compared to last month."
    )
    assert assessment.priority == PRIORITY_ROUTINE
    assert "ROUTINE" in assessment.title


def test_prompt_evaluation_scenario():
    """Ensures clinical flags like breast lump or severe dysuria route to prompt medical evaluation."""
    assessment = SafetyNavigator.evaluate(
        symptom="Breast Lump",
        category="Breast Health",
        severity=4,
        notes="Felt a new firm pea-sized lump."
    )
    assert assessment.priority == PRIORITY_PROMPT
    assert "PROMPT" in assessment.title
    assert any("24" in a or "schedule" in a.lower() for a in assessment.recommended_actions)


def test_emergency_evaluation_scenario():
    """Ensures acute emergency triggers route immediately to emergency evaluation."""
    # Test 1: Thunderclap headache
    assessment = SafetyNavigator.evaluate(
        symptom="Migraine",
        category="Neurological & Head",
        severity=9,
        notes="Sudden worst headache of life with blurred vision."
    )
    assert assessment.priority == PRIORITY_EMERGENCY
    assert "EMERGENCY" in assessment.title
    assert assessment.emergency_contact is not None

    # Test 2: Severe acute pelvic pain with fainting
    assessment_pelvic = SafetyNavigator.evaluate(
        symptom="Pelvic Pain",
        category="Pelvic & Menstrual",
        severity=9,
        notes="Acute pelvic pain with dizziness and fainting"
    )
    assert assessment_pelvic.priority == PRIORITY_EMERGENCY


def test_emergency_flag_selected():
    """Ensures user explicitly checking an emergency warning flag forces emergency priority."""
    assessment = SafetyNavigator.evaluate(
        symptom="Headache",
        category="Neurological & Head",
        severity=5,
        red_flags_checked=["Sudden onset 'worst headache of life' (thunderclap)"]
    )
    assert assessment.priority == PRIORITY_EMERGENCY


def test_no_diagnostic_claims():
    """Ensures the safety assessment never claims to confirm a specific medical diagnosis."""
    assessment = SafetyNavigator.evaluate(
        symptom="Pelvic Pain / Cramping",
        category="Pelvic & Menstrual",
        severity=7,
        notes="Heavy bleeding and painful intercourse"
    )
    combined = (assessment.title + " " + assessment.headline + " " + " ".join(assessment.rationale)).lower()
    assert "you have been diagnosed" not in combined
    assert "this confirms you have endometriosis" not in combined
    assert "prescription" not in assessment.title.lower()
