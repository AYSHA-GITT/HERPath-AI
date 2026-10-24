"""
HERPath AI - Frontend End-to-End Test Suite using Streamlit AppTest
recHERsion 2026 | PS1: Women's Healthcare

Programmatically verifies UI rendering, navigation state transitions,
form inputs, chart elements, and button clicks across all 7 frontend views.
"""

import pytest
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP_FILE = str(Path(__file__).resolve().parent.parent / "app.py")


def test_frontend_home_dashboard():
    """Tests frontend rendering of the Home Dashboard, KPI cards, and header."""
    at = AppTest.from_file(APP_FILE, default_timeout=30)
    at.run()
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
    at = AppTest.from_file(APP_FILE, default_timeout=30)
    at.run()

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
    at = AppTest.from_file(APP_FILE, default_timeout=30)
    at.run()

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
    at = AppTest.from_file(APP_FILE, default_timeout=30)
    at.run()

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
    at = AppTest.from_file(APP_FILE, default_timeout=30)
    at.run()

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
    at = AppTest.from_file(APP_FILE, default_timeout=30)
    at.run()

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
    at = AppTest.from_file(APP_FILE, default_timeout=30)
    at.run()

    # Switch to Privacy and Settings
    at.sidebar.radio[0].set_value("Privacy and Settings").run()
    assert not at.exception

    # Verify Privacy architecture documentation
    combined_md = " ".join([m.value for m in at.markdown])
    assert "Privacy & Data Protection Architecture" in combined_md
    assert "100% Local SQLite Storage" in combined_md or "Local Storage Only" in combined_md


def test_frontend_medication_tracker():
    """Tests navigation to Medication & Treatments view and adding a treatment."""
    at = AppTest.from_file(APP_FILE, default_timeout=30)
    at.run()

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

