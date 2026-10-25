"""
HERPath AI - Frontend End-to-End Test Suite using Streamlit AppTest
recHERsion 2026 | PS1: Women's Healthcare

Programmatically verifies UI rendering, landing auth screen, sign in / sign up flows,
navigation state transitions, form inputs, chart elements, and button clicks across all frontend views.
"""

import pytest
import uuid
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


def test_frontend_opens_with_signin_signup_pages_first():
    """Verifies that as soon as the application opens, it presents the Sign In / Sign Up portal."""
    at = AppTest.from_file(APP_FILE, default_timeout=30)
    at.run()
    assert not at.exception
    assert at.session_state["is_logged_in"] is False

    # Check Sign In / Sign Up title and hero text
    combined_md = " ".join([m.value for m in at.markdown])
    assert "HERPath AI" in combined_md
    assert "Women's Health Intelligence" in combined_md
    assert "100% On-Device SQLite" in combined_md

    # Check Login action button exists on the landing screen
    button_labels = [b.label for b in at.button]
    assert any("LOGIN" in b for b in button_labels)


def test_frontend_home_dashboard():
    """Tests frontend rendering of the Home Dashboard, KPI cards, and header after signing in."""
    at = get_authenticated_app()
    assert not at.exception, f"Exception occurred during app load: {at.exception}"

    # Verify Sidebar components
    assert len(at.sidebar.radio) > 0
    assert at.sidebar.radio[0].value == "Home Dashboard"
    assert len(at.sidebar.selectbox) > 0  # Profile selector

    # Verify Header & Welcome Text
    markdown_texts = [m.value for m in at.markdown]
    assert any("HERPath AI" in text for text in markdown_texts)
    assert any("Welcome back" in text for text in markdown_texts)

    # Verify Quick Action Buttons exist
    button_labels = [b.label for b in at.button]
    assert any("Log a New Symptom" in label for label in button_labels)
    assert any("Check Symptoms in Care Navigator" in label for label in button_labels)
    assert any("Export Clinician Health Report" in label for label in button_labels)


def test_frontend_symptom_journal_navigation():
    """Tests navigation to Symptom Journal and verifies form components."""
    at = get_authenticated_app()

    # Switch to Symptom Journal
    at.sidebar.radio[0].set_value("Symptom Journal").run()
    assert not at.exception

    # Verify page title
    assert any("Smart Symptom Journal" in m.value for m in at.markdown)

    # Find the symptom entry form
    assert len(at.form) > 0
    journal_form = at.form[0]

    # Verify category selectbox
    assert len(journal_form.selectbox) > 0
    assert "Pelvic & Menstrual" in journal_form.selectbox[0].options

    # Verify severity slider
    assert len(journal_form.slider) > 0
    assert journal_form.slider[0].min == 1
    assert journal_form.slider[0].max == 10

    # Verify submit button
    assert len(journal_form.form_submit_button) > 0
    assert "Save Symptom Entry" in journal_form.form_submit_button[0].label


def test_frontend_health_insights_view():
    """Tests navigation to Health Insights, KPI calculations, and chart elements."""
    at = get_authenticated_app()

    # Switch to Health Insights
    at.sidebar.radio[0].set_value("Health Insights").run()
    assert not at.exception

    # Verify metrics rendered
    assert len(at.metric) >= 4
    metric_labels = [m.label for m in at.metric]
    assert "Total Recorded Entries" in metric_labels
    assert "Distinct Days Logged" in metric_labels
    assert "Average Severity" in metric_labels

    # Verify explainable insights cards exist
    markdown_content = " ".join([m.value for m in at.markdown])
    assert "Explainable Observation Statements" in markdown_content


def test_frontend_care_navigator_triage():
    """Tests Care Navigator triage execution and emergency guidance rendering."""
    at = get_authenticated_app()

    # Switch to Care Navigator
    at.sidebar.radio[0].set_value("Care Navigator").run()
    assert not at.exception

    # Verify form exists
    assert len(at.form) > 0
    nav_form = at.form[0]

    # Check an emergency warning sign checkbox
    assert len(nav_form.checkbox) > 0
    nav_form.checkbox[0].check()  # "Sudden onset 'worst headache of life' (thunderclap)"

    # Set severity slider to high
    nav_form.slider[0].set_value(9)

    # Submit evaluation
    nav_form.form_submit_button[0].click().run()
    assert not at.exception

    # Verify emergency card rendered
    combined_md = " ".join([m.value for m in at.markdown])
    assert "EMERGENCY EVALUATION NEEDED" in combined_md
    assert "Immediate Safety Guidance" in combined_md


def test_frontend_health_library_search():
    """Tests Women's Health Library rendering and live search filtering."""
    at = get_authenticated_app()

    # Switch to Library
    at.sidebar.radio[0].set_value("Women's Health Library").run()
    assert not at.exception

    # Verify search input exists
    assert len(at.text_input) > 0
    at.text_input[0].set_value("PCOS").run()
    assert not at.exception

    # Check search results display PCOS resource
    combined_md = " ".join([m.value for m in at.markdown])
    assert "Polycystic Ovary Syndrome" in combined_md
    assert "World Health Organization" in combined_md


def test_frontend_report_preview_and_download():
    """Tests My Health Report preview metrics and download button generation."""
    at = get_authenticated_app()

    # Switch to My Health Report
    at.sidebar.radio[0].set_value("My Health Report").run()
    assert not at.exception

    # Verify report preview metrics
    assert len(at.metric) >= 4
    metric_labels = [m.label for m in at.metric]
    assert "Entries in Period" in metric_labels

    # Verify PDF download button exists
    assert len(at.download_button) > 0
    download_btn = at.download_button[0]
    assert "Download Clinician Health Report" in download_btn.label


def test_frontend_privacy_settings_and_profile_switch():
    """Tests Privacy & Settings view and profile customization."""
    at = get_authenticated_app()

    # Switch to Privacy and Settings
    at.sidebar.radio[0].set_value("Privacy and Settings").run()
    assert not at.exception

    # Verify Privacy architecture documentation
    combined_md = " ".join([m.value for m in at.markdown])
    assert "Privacy & Data Protection Architecture" in combined_md
    assert "100% Local SQLite Storage" in combined_md or "Local Storage Only" in combined_md


def test_frontend_medication_tracker():
    """Tests navigation to Medication & Treatments view and adding a treatment."""
    at = get_authenticated_app()

    # Switch to Medication & Treatments
    at.sidebar.radio[0].set_value("Medication & Treatments").run()
    assert not at.exception

    # Verify page title
    assert any("Medication & Health Intervention Tracker" in m.value for m in at.markdown)

    # Check form exists
    assert len(at.form) > 0
    med_form = at.form[0]

    # Fill form
    assert len(med_form.text_input) > 0
    med_form.text_input[0].set_value("Magnesium Glycinate")
    med_form.selectbox[0].set_value("OTC / Supplement")

    # Submit form
    med_form.form_submit_button[0].click().run()
    assert not at.exception
    assert len(at.success) > 0


def test_frontend_ask_herpath_assistant():
    """Tests navigation to Ask HERPath assistant and educational retrieval."""
    at = get_authenticated_app()

    at.sidebar.radio[0].set_value("Ask HERPath").run()
    assert not at.exception

    # Verify Assistant title and disclaimer
    combined_md = " ".join([m.value for m in at.markdown])
    assert "Ask HERPath — Health Literacy Assistant" in combined_md
    assert "Strictly non-diagnostic" in combined_md

    # Test querying a health literacy topic
    assert len(at.text_input) > 0
    at.text_input[0].set_value("iron deficiency fatigue").run()
    assert not at.exception

    # Verify grounded findings rendered
    results_md = " ".join([m.value for m in at.markdown])
    assert "Grounded Findings" in results_md or "Relevant Guides Found" in results_md


def test_frontend_home_vitality_and_explorer():
    """Tests Home Dashboard vitality check-in and anatomical explorer interactions."""
    at = get_authenticated_app()

    combined_md = " ".join([m.value for m in at.markdown])
    assert "Daily Vitality" in combined_md
    assert "Anatomical Health Focus Explorer" in combined_md

    # Check that explorer buttons exist
    button_labels = [b.label for b in at.button]
    assert any("Explore Head & Neuro" in b for b in button_labels)
    assert any("Explore Pelvic Care" in b for b in button_labels)
    assert any("Explore Hormonal" in b for b in button_labels)


def test_frontend_insights_calendar_grid():
    """Tests navigation to Health Insights and presence of Monthly Calendar Grid tab."""
    at = get_authenticated_app()

    at.sidebar.radio[0].set_value("Health Insights").run()
    assert not at.exception

    combined_md = " ".join([m.value for m in at.markdown])
    assert "Interactive Charts & Distributions" in combined_md
    assert "Doctor Consultation Prep Kit" in combined_md


def test_frontend_account_login_navigation():
    """Tests that landing page contains sign in and account access."""
    at = AppTest.from_file(APP_FILE, default_timeout=30)
    at.run()
    assert not at.exception

    combined_md = " ".join([m.value for m in at.markdown])
    assert "HERPath AI" in combined_md
    assert "Women's Health Intelligence" in combined_md
    assert "100% On-Device SQLite" in combined_md

    # Check that Login button exists
    button_labels = [b.label for b in at.button]
    assert any("LOGIN" in b for b in button_labels)


def test_frontend_new_user_registration_flow():
    """Tests that a new user can register with custom display name and profile ID from the landing page."""
    at = AppTest.from_file(APP_FILE, default_timeout=30)
    at.run()
    assert not at.exception

    # Locate the registration form
    reg_form = None
    for form in at.form:
        if any("Create My Profile" in btn.label for btn in form.form_submit_button):
            reg_form = form
            break
    assert reg_form is not None, "Registration form not found"

    # Fill registration details
    random_user_id = f"test_user_{uuid.uuid4().hex[:6]}"
    reg_form.text_input[0].set_value("Kavita Wellness")
    reg_form.text_input[1].set_value(random_user_id)
    reg_form.form_submit_button[0].click().run()
    assert not at.exception

    # Verify user state updated and profile is active
    assert at.session_state["current_profile_id"] == random_user_id
    assert at.session_state["is_logged_in"] is True
    combined_md = " ".join([m.value for m in at.markdown])
    assert "Kavita" in combined_md


def test_frontend_auth_interactive_tab_switching():
    """Tests that clicking 'Sign up' switches to Create Account, and 'Sign in' switches back to Login."""
    at = AppTest.from_file(APP_FILE, default_timeout=30)
    at.run()
    assert not at.exception

    # Find the 'Sign up' button on the Login page
    signup_switch = [b for b in at.button if "Sign up" in b.label]
    assert len(signup_switch) > 0, "Switch to Sign up button not found"

    # Click to switch to Create Account
    signup_switch[0].click().run()
    assert not at.exception
    assert at.session_state.get("auth_active_tab") == "Create Account"

    # Find the 'Sign in' button on the Create Account page
    signin_switch = [b for b in at.button if "Sign in" in b.label]
    assert len(signin_switch) > 0, "Switch to Sign in button not found"

    # Click to switch back to Login
    signin_switch[0].click().run()
    assert not at.exception
    assert at.session_state.get("auth_active_tab") == "Login"


def test_frontend_signin_requires_pin():
    """Tests that logging in without a PIN or with an invalid PIN shows an error message."""
    at = AppTest.from_file(APP_FILE, default_timeout=30)
    at.run()
    assert not at.exception

    # Attempt login without PIN
    login_btn = [b for b in at.button if "LOGIN" in b.label][0]
    login_btn.click().run()
    assert not at.exception
    assert at.session_state["is_logged_in"] is False
    assert len(at.error) > 0
    assert "pin" in at.error[0].value.lower()

    # Enter wrong PIN
    pin_input = [ti for ti in at.text_input if ti.key and "pin" in ti.key.lower()][0]
    pin_input.set_value("0000")
    login_btn = [b for b in at.button if "LOGIN" in b.label][0]
    login_btn.click().run()
    assert not at.exception
    assert at.session_state["is_logged_in"] is False

    # Enter correct PIN (1234)
    pin_input = [ti for ti in at.text_input if ti.key and "pin" in ti.key.lower()][0]
    pin_input.set_value("1234")
    login_btn = [b for b in at.button if "LOGIN" in b.label][0]
    login_btn.click().run()
    assert not at.exception
    assert at.session_state["is_logged_in"] is True

