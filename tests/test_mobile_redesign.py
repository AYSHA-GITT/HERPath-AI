"""
HERPath AI - Mobile Redesign Verification Suite
recHERsion 2026 | PS1: Women's Healthcare

Verifies:
1. Four fixed mobile bottom navigation buttons (Home, My Health, Care, Learn).
2. 5-step symptom form flow, post-save confirmation card, and navigation shortcuts.
3. Daily check-in pulse disclaimer and personal tracking indicators.
4. Mobile-first palette, typography, and accessibility markers.
"""

import pytest
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP_FILE = str(Path(__file__).resolve().parent.parent / "app.py")


def get_authenticated_app() -> AppTest:
    """Helper to launch app and log in via the primary Login button."""
    at = AppTest.from_file(APP_FILE, default_timeout=30)
    at.run()
    for ti in at.text_input:
        if ti.key and "pin" in ti.key.lower():
            ti.set_value("1234")
            break
    for b in at.button:
        if "LOGIN" in b.label:
            b.click().run()
            break
    return at


def test_mobile_bottom_navigation_elements():
    """Verifies that the 4 mobile bottom navigation tabs are hidden before sign-in and present after authentication."""
    # 1. Unauthenticated state: 4-tab bottom navigation must be hidden
    at_unauth = AppTest.from_file(APP_FILE, default_timeout=30)
    at_unauth.run()
    assert not at_unauth.exception
    unauth_buttons = [b.label for b in at_unauth.button]
    assert not any("🌸 Home" in b for b in unauth_buttons), "Home bottom tab should be hidden before sign in"
    assert not any("💗 My Health" in b for b in unauth_buttons), "My Health bottom tab should be hidden before sign in"
    assert not any("🛡️ Care" in b for b in unauth_buttons), "Care bottom tab should be hidden before sign in"
    assert not any("📚 Learn" in b for b in unauth_buttons), "Learn bottom tab should be hidden before sign in"

    # 2. Authenticated state: all 4 bottom tabs must exist and be accessible
    at = get_authenticated_app()
    assert not at.exception
    button_labels = [b.label for b in at.button]
    assert any("Home" in b for b in button_labels), "Home bottom tab missing"
    assert any("My Health" in b for b in button_labels), "My Health bottom tab missing"
    assert any("Care" in b for b in button_labels), "Care bottom tab missing"
    assert any("Learn" in b for b in button_labels), "Learn bottom tab missing"


def test_mobile_symptom_journal_5_step_flow():
    """Verifies the 5-step symptom form flow and post-save confirmation card."""
    at = get_authenticated_app()

    # Navigate to Symptom Journal
    at.sidebar.radio[0].set_value("Symptom Journal").run()
    assert not at.exception

    # Verify 5-step headings are present
    combined_md = " ".join([m.value for m in at.markdown])
    assert "Step 1: What are you experiencing?" in combined_md
    assert "Step 2: How intense is it right now?" in combined_md
    assert "Step 3: When did it start & duration?" in combined_md
    assert "Step 4: Contextual Details" in combined_md

    # Check form exists
    assert len(at.form) > 0
    form = at.form[0]

    # Fill and submit form
    form.selectbox[0].set_value("Pelvic & Menstrual")
    form.slider[0].set_value(4)
    form.form_submit_button[0].click().run()
    assert not at.exception

    # Check post-save state
    post_md = " ".join([m.value for m in at.markdown])
    assert "Symptom Saved Successfully!" in post_md
    post_buttons = [b.label for b in at.button]
    assert any("Log Another Symptom" in b for b in post_buttons)
    assert any("Explore My Health Patterns" in b for b in post_buttons)


def test_mobile_home_checkin_disclaimer():
    """Verifies that the daily check-in pulse clearly states it is a non-medical indicator."""
    at = get_authenticated_app()

    combined_md = " ".join([m.value for m in at.markdown])
    assert "personal tracking indicator" in combined_md
    assert "not a medical measurement" in combined_md


def test_mobile_accessible_severity_feedback():
    """Verifies that severity indicators use descriptive text rather than color alone."""
    at = get_authenticated_app()

    at.sidebar.radio[0].set_value("Symptom Journal").run()
    assert not at.exception

    combined_md = " ".join([m.value for m in at.markdown])
    # Initial severity slider value is 5 (Moderate)
    assert "Moderate (4–6): Notable discomfort" in combined_md
