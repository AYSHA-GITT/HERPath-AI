"""
HERPath AI — Women's Health Intelligence & Care Navigation Platform
recHERsion 2026 | PS1: Women's Healthcare
ACM-W, NITK Surathkal
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from pathlib import Path
import json

# Internal Modules
from config import (
    APP_TITLE,
    APP_NAME,
    APP_TAGLINE,
    HACKATHON_EVENT,
    CLINICAL_DISCLAIMER,
    EMERGENCY_NOTICE,
    SYMPTOM_TAXONOMY,
    SLEEP_QUALITIES,
    STRESS_LEVELS,
    ENERGY_LEVELS,
    CYCLE_PHASES,
    DAILY_IMPACT_LEVELS,
    PRIORITY_EMERGENCY,
    PRIORITY_PROMPT,
    PRIORITY_ROUTINE,
    PRIORITY_SELFCARE
)
from database import (
    init_db,
    get_profile,
    list_profiles,
    create_profile,
    delete_profile,
    update_profile_preferences,
    clear_profile_symptoms,
    add_medication,
    get_medications,
    delete_medication,
    export_profile_data_json,
    export_symptoms_csv,
    import_profile_data_json
)
from models import MedicationEntry
from symptom_tracker import SymptomTrackerService
from insights_engine import InsightsEngine
from safety_navigator import SafetyNavigator
from health_library import HealthLibrary
from report_generator import ClinicianReportGenerator
from data.seed_data import seed_demo_data

# ==========================================
# Page Configuration & Styling
# ==========================================
st.set_page_config(
    page_title=f"{APP_TITLE} | Women's Health Platform",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom CSS
css_file = Path(__file__).parent / "assets" / "styles.css"
if css_file.exists():
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Ensure Database is initialized
init_db()

# Initialize Health Library
health_library = HealthLibrary()

# ==========================================
# Session State Initialization
# ==========================================
if "current_profile_id" not in st.session_state:
    st.session_state["current_profile_id"] = "demo_priya"

if "navigation" not in st.session_state:
    st.session_state["navigation"] = "Home Dashboard"

if "editing_entry_id" not in st.session_state:
    st.session_state["editing_entry_id"] = None


# Helper to switch pages
def navigate_to(page_name: str):
    st.session_state["navigation"] = page_name
    st.rerun()


# ==========================================
# Sidebar: Profile & Navigation
# ==========================================
with st.sidebar:
    st.markdown("### 🌸 **HERPath AI**")
    st.caption("Women's Health Intelligence & Care Navigation")

    # Profile Selector
    profiles = list_profiles()
    profile_dict = {p.id: p for p in profiles}

    if not profiles:
        # Fallback if no profiles exist
        create_profile("demo_priya", "Priya (PCOS & Migraine Tracking)")
        profiles = list_profiles()
        profile_dict = {p.id: p for p in profiles}

    current_id = st.session_state["current_profile_id"]
    if current_id not in profile_dict:
        current_id = profiles[0].id
        st.session_state["current_profile_id"] = current_id

    profile_options = [p.id for p in profiles]
    selected_profile_id = st.selectbox(
        "👤 Active Health Profile",
        options=profile_options,
        index=profile_options.index(current_id),
        format_func=lambda pid: profile_dict[pid].display_name
    )

    if selected_profile_id != st.session_state["current_profile_id"]:
        st.session_state["current_profile_id"] = selected_profile_id
        st.session_state["editing_entry_id"] = None
        st.rerun()

    active_profile = profile_dict[st.session_state["current_profile_id"]]

    st.markdown("---")

    # Navigation Menu
    nav_options = [
        "Home Dashboard",
        "Symptom Journal",
        "Medication & Treatments",
        "Health Insights",
        "Care Navigator",
        "Women's Health Library",
        "My Health Report",
        "Ask HERPath",
        "Privacy and Settings"
    ]


    selected_nav = st.radio(
        "📍 Platform Navigation",
        nav_options,
        index=nav_options.index(st.session_state["navigation"])
    )

    if selected_nav != st.session_state["navigation"]:
        st.session_state["navigation"] = selected_nav
        st.rerun()

    st.markdown("---")
    st.markdown(
        "<div class='privacy-badge'>🔒 100% Local SQLite Storage</div>",
        unsafe_allow_html=True
    )
    st.caption("No cloud transmission of sensitive records. Single-device prototype.")


# ==========================================
# Main Header
# ==========================================
st.markdown(f"""
    <div class="herpath-header">
        <h1>HERPath AI</h1>
        <p>{APP_TAGLINE} &bull; <i>{HACKATHON_EVENT}</i></p>
    </div>
""", unsafe_allow_html=True)


# ==========================================
# Page 1: Home Dashboard
# ==========================================
if st.session_state["navigation"] == "Home Dashboard":
    st.markdown(f"### Welcome back, **{active_profile.display_name}**")
    st.write(
        "HERPath AI helps you record personal health observations, analyze explainable trajectories, "
        "and prepare clinician-ready summaries without diagnostic assumptions."
    )

    # Fetch user records
    user_entries = SymptomTrackerService.get_history(active_profile.id)
    engine = InsightsEngine(user_entries)
    metrics = engine.calculate_summary_metrics()

    # KPI Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Logged Entries</div>
                <div class="stat-value">{metrics['total_entries']}</div>
                <div class="stat-subtext">Total records</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Tracking Days</div>
                <div class="stat-value">{metrics['distinct_days']}</div>
                <div class="stat-subtext">Distinct dates</div>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Average Severity</div>
                <div class="stat-value">{metrics['avg_severity']} <span style="font-size:1.1rem; color:#8E8A9E;">/10</span></div>
                <div class="stat-subtext">Across all entries</div>
            </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Peak Severity</div>
                <div class="stat-value" style="color: #E76F7C;">{metrics['max_severity']} <span style="font-size:1.1rem; color:#8E8A9E;">/10</span></div>
                <div class="stat-subtext">{metrics['max_severity_symptom'][:14]}</div>
            </div>
        """, unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Ongoing Status</div>
                <div class="stat-value" style="color: #2A9D8F;">{metrics['ongoing_count']}</div>
                <div class="stat-subtext">Active symptoms</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Quick Actions Row
    q1, q2, q3 = st.columns([1.2, 1.2, 1.6])
    with q1:
        if st.button("➕ Log a New Symptom", use_container_width=True, type="primary"):
            navigate_to("Symptom Journal")
    with q2:
        if st.button("🛡️ Check Symptoms in Care Navigator", use_container_width=True):
            navigate_to("Care Navigator")
    with q3:
        if st.button("📄 Export Clinician Health Report", use_container_width=True):
            navigate_to("My Health Report")

    st.markdown("---")

    # Interactive Severity Timeline or Informative Empty State
    if metrics["total_entries"] == 0:
        st.info("ℹ️ **No symptom entries logged yet for this profile.**")
        st.write("Start building your personal health timeline by recording your first symptom or loading demonstration records.")
        if st.button("Record First Symptom Now", type="primary"):
            navigate_to("Symptom Journal")
    else:
        st.markdown("#### 📈 Symptom Severity & Trajectory Timeline")
        timeline_fig = engine.plot_severity_timeline()
        if timeline_fig:
            st.plotly_chart(timeline_fig, use_container_width=True)

        # Recent Entries Section
        st.markdown("#### 🕒 Recent Symptom Entries")
        recent = user_entries[:5]
        recent_data = []
        for r in recent:
            recent_data.append({
                "Date": r.onset_date,
                "Symptom": r.symptom,
                "Category": r.category,
                "Severity": f"{r.severity}/10",
                "Duration": f"{r.duration_hours}h" if r.duration_hours else "—",
                "Status": r.status,
                "Daily Impact": r.impact or "None",
                "Notes": r.notes or "—"
            })
        st.dataframe(pd.DataFrame(recent_data), use_container_width=True, hide_index=True)

    # Educational Highlight Card
    st.markdown("---")
    st.markdown("#### 💡 Clinician Tip & Health Education Highlight")
    rec_resources = health_library.get_recommended_resources_for_symptom("Pelvic & Menstrual")
    if rec_resources:
        highlight = rec_resources[0]
        st.markdown(f"""
            <div class="content-card" style="border-left: 4px solid var(--primary);">
                <div class="resource-source">{highlight['source_org']} &bull; {highlight['category']}</div>
                <div class="content-card-title">{highlight['title']}</div>
                <p style="color: var(--text-secondary); margin-bottom: 0.8rem;">{highlight['summary']}</p>
                <div style="font-size: 0.88rem; color: var(--primary); font-weight: 600;">
                    <a href="{highlight['source_url']}" target="_blank" style="text-decoration: none; color: inherit;">
                        Read verified resource &rarr;
                    </a>
                </div>
            </div>
        """, unsafe_allow_html=True)


# ==========================================
# Page 2: Symptom Journal (Full CRUD)
# ==========================================
elif st.session_state["navigation"] == "Symptom Journal":
    st.markdown("### 📝 Smart Symptom Journal")
    st.write("Record, review, search, and manage your health observations with complete local privacy.")

    tab_add, tab_history = st.tabs(["➕ Record / Edit Symptom", "📜 View & Filter Symptom History"])

    track_menstrual = active_profile.preferences.get("track_menstrual", True)

    # TAB 1: ADD OR EDIT SYMPTOM
    with tab_add:
        is_editing = st.session_state["editing_entry_id"] is not None
        edit_entry = None
        if is_editing:
            edit_entry = SymptomTrackerService.get_entry(st.session_state["editing_entry_id"], active_profile.id)
            if edit_entry:
                st.warning(f"Editing Entry #{edit_entry.id}: **{edit_entry.symptom}** (Date: {edit_entry.onset_date})")
                if st.button("Cancel Edit"):
                    st.session_state["editing_entry_id"] = None
                    st.rerun()
            else:
                st.session_state["editing_entry_id"] = None

        with st.form("symptom_entry_form", clear_on_submit=not is_editing):
            st.markdown("##### 1. Core Symptom Details")
            col_cat, col_sym = st.columns(2)

            categories = list(SYMPTOM_TAXONOMY.keys())
            cat_default_idx = 0
            if edit_entry and edit_entry.category in categories:
                cat_default_idx = categories.index(edit_entry.category)

            with col_cat:
                selected_category = st.selectbox(
                    "Symptom Category *",
                    categories,
                    index=cat_default_idx,
                    help="Categorize the physiological area of the symptom."
                )

            common_symptoms = SYMPTOM_TAXONOMY.get(selected_category, [])
            sym_default_val = edit_entry.symptom if edit_entry else common_symptoms[0] if common_symptoms else ""

            with col_sym:
                custom_sym_toggle = st.checkbox("Enter custom symptom name", value=edit_entry and edit_entry.symptom not in common_symptoms)
                if custom_sym_toggle:
                    symptom_name = st.text_input("Custom Symptom Name *", value=sym_default_val)
                else:
                    sym_index = common_symptoms.index(sym_default_val) if sym_default_val in common_symptoms else 0
                    symptom_name = st.selectbox("Select Symptom *", common_symptoms, index=sym_index)

            col_date, col_time, col_dur, col_stat = st.columns(4)
            with col_date:
                default_date = datetime.strptime(edit_entry.onset_date, "%Y-%m-%d").date() if edit_entry else date.today()
                onset_date = st.date_input("Onset Date *", value=default_date, max_value=date.today() + timedelta(days=1))
            with col_time:
                onset_time = st.text_input("Time of Onset (Optional)", value=edit_entry.onset_time or "" if edit_entry else "", placeholder="e.g. 14:30")
            with col_dur:
                default_dur = edit_entry.duration_hours if edit_entry and edit_entry.duration_hours is not None else 0.0
                duration_hours = st.number_input("Duration (hours, optional)", min_value=0.0, max_value=720.0, value=float(default_dur), step=0.5)
            with col_stat:
                statuses = ["Ongoing", "Resolved", "Intermittent"]
                stat_idx = statuses.index(edit_entry.status) if edit_entry and edit_entry.status in statuses else 0
                status = st.selectbox("Status *", statuses, index=stat_idx)

            st.markdown("##### 2. Severity & Functional Impact")
            default_sev = edit_entry.severity if edit_entry else 5
            severity = st.slider(
                "Severity Rating (1 to 10) *",
                min_value=1,
                max_value=10,
                value=int(default_sev),
                help="1-3: Mild (Noticeable, no disruption); 4-6: Moderate (Interferes with tasks); 7-8: Severe (Significantly limits functioning); 9-10: Debilitating."
            )

            # Severity Pill Feedback
            if severity <= 3:
                st.markdown("<span class='severity-pill-mild'>Mild (1–3): Noticeable but routines manageable</span>", unsafe_allow_html=True)
            elif severity <= 6:
                st.markdown("<span class='severity-pill-moderate'>Moderate (4–6): Notable discomfort, interferes with some activities</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span class='severity-pill-severe'>Severe / Debilitating (7–10): Severely limits daily functioning</span>", unsafe_allow_html=True)

            impact_idx = DAILY_IMPACT_LEVELS.index(edit_entry.impact) if edit_entry and edit_entry.impact in DAILY_IMPACT_LEVELS else 0
            daily_impact = st.selectbox("Impact on Daily Activities", DAILY_IMPACT_LEVELS, index=impact_idx)

            st.markdown("##### 3. Contextual Observations (Optional)")
            col_slp, col_strss, col_enrg = st.columns(3)

            ctx = edit_entry.context if edit_entry else {}
            slp_idx = SLEEP_QUALITIES.index(ctx["sleep"]) if ctx.get("sleep") in SLEEP_QUALITIES else 0
            strss_idx = STRESS_LEVELS.index(ctx["stress"]) if ctx.get("stress") in STRESS_LEVELS else 1
            enrg_idx = ENERGY_LEVELS.index(ctx["energy"]) if ctx.get("energy") in ENERGY_LEVELS else 1

            with col_slp:
                sleep_quality = st.selectbox("Recent Sleep Quality", SLEEP_QUALITIES, index=slp_idx)
            with col_strss:
                stress_level = st.selectbox("Recent Stress Level", STRESS_LEVELS, index=strss_idx)
            with col_enrg:
                energy_level = st.selectbox("Energy Level", ENERGY_LEVELS, index=enrg_idx)

            cycle_phase = "Not tracking / NA"
            if track_menstrual:
                cyc_idx = CYCLE_PHASES.index(ctx["cycle_phase"]) if ctx.get("cycle_phase") in CYCLE_PHASES else 0
                cycle_phase = st.selectbox("Menstrual Cycle Phase (Optional)", CYCLE_PHASES, index=cyc_idx)

            notes = st.text_area(
                "Personal Notes / Observations (Optional)",
                value=edit_entry.notes if edit_entry else "",
                placeholder="Describe specific triggers, medications taken, relief factors, or symptoms for your doctor.",
                max_chars=1000
            )

            submit_label = "💾 Update Symptom Entry" if is_editing else "💾 Save Symptom Entry"
            submitted = st.form_submit_button(submit_label, type="primary")

            if submitted:
                cleaned_dur = float(duration_hours) if duration_hours > 0 else None
                entry_context = {
                    "sleep": sleep_quality,
                    "stress": stress_level,
                    "energy": energy_level,
                    "cycle_phase": cycle_phase
                }

                if is_editing:
                    success, err = SymptomTrackerService.edit_symptom(
                        entry_id=edit_entry.id,
                        profile_id=active_profile.id,
                        category=selected_category,
                        symptom=symptom_name,
                        onset_date=str(onset_date),
                        severity=severity,
                        duration_hours=cleaned_dur,
                        status=status,
                        onset_time=onset_time,
                        impact=daily_impact,
                        notes=notes,
                        context=entry_context
                    )
                    if success:
                        st.success(f"✅ Successfully updated entry #{edit_entry.id} ({symptom_name})!")
                        st.session_state["editing_entry_id"] = None
                        st.rerun()
                    else:
                        st.error(f"❌ Error updating entry: {err}")
                else:
                    success, new_id, err = SymptomTrackerService.record_symptom(
                        profile_id=active_profile.id,
                        category=selected_category,
                        symptom=symptom_name,
                        onset_date=str(onset_date),
                        severity=severity,
                        duration_hours=cleaned_dur,
                        status=status,
                        onset_time=onset_time,
                        impact=daily_impact,
                        notes=notes,
                        context=entry_context
                    )
                    if success:
                        st.success(f"✅ Successfully recorded '{symptom_name}' (ID #{new_id}) to database!")
                        st.rerun()
                    else:
                        st.error(f"❌ Error saving entry: {err}")

    # TAB 2: VIEW & FILTER HISTORY
    with tab_history:
        st.markdown("##### 🔍 Filter Stored Records")
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)

        with col_f1:
            all_cats = ["All Categories"] + list(SYMPTOM_TAXONOMY.keys())
            filter_cat = st.selectbox("Category Filter", all_cats)
        with col_f2:
            filter_stat = st.selectbox("Status Filter", ["All", "Ongoing", "Resolved", "Intermittent"])
        with col_f3:
            filter_start = st.date_input("From Date", value=date.today() - timedelta(days=60))
        with col_f4:
            filter_end = st.date_input("To Date", value=date.today() + timedelta(days=1))

        # Fetch filtered records
        history_records = SymptomTrackerService.get_history(
            profile_id=active_profile.id,
            start_date=str(filter_start),
            end_date=str(filter_end),
            category=filter_cat,
            status=filter_stat
        )

        st.caption(f"Showing **{len(history_records)}** records for profile **{active_profile.display_name}**.")

        if not history_records:
            st.info("No records match the selected filters.")
        else:
            for entry in history_records:
                with st.expander(f"📅 **{entry.onset_date}** — {entry.symptom} (Severity: {entry.severity}/10 &bull; {entry.status})", expanded=False):
                    c_det1, c_det2 = st.columns([3, 1])
                    with c_det1:
                        st.markdown(f"**Category:** {entry.category}")
                        st.markdown(f"**Severity:** {entry.severity}/10 &bull; **Duration:** {entry.duration_hours or 'N/A'} hrs &bull; **Status:** {entry.status}")
                        st.markdown(f"**Impact:** {entry.impact or 'None'}")
                        if entry.context:
                            ctx_str = ", ".join([f"**{k.title()}**: {v}" for k, v in entry.context.items() if v])
                            st.markdown(f"**Context Observations:** {ctx_str}")
                        if entry.notes:
                            st.markdown(f"**Notes:** {entry.notes}")

                    with c_det2:
                        if st.button("✏️ Edit Entry", key=f"edit_btn_{entry.id}", use_container_width=True):
                            st.session_state["editing_entry_id"] = entry.id
                            st.rerun()

                        if st.button("🗑️ Delete", key=f"del_btn_{entry.id}", use_container_width=True, type="secondary"):
                            SymptomTrackerService.remove_symptom(entry.id, active_profile.id)
                            st.success(f"Entry #{entry.id} deleted.")
                            st.rerun()


# ==========================================
# Page: Medication & Treatments Tracker
# ==========================================
elif st.session_state["navigation"] == "Medication & Treatments":
    st.markdown("### 💊 Medication & Health Intervention Tracker")
    st.write(
        "Track prescribed medications, over-the-counter supplements, and supportive therapies "
        "(such as heating pads, tens therapy, or diet adjustments) to build a complete picture of your care routine."
    )

    tab_med_add, tab_med_list = st.tabs(["➕ Add Medication / Intervention", "📋 Current Regimen & History"])

    with tab_med_add:
        with st.form("add_medication_form", clear_on_submit=True):
            st.markdown("##### 1. Treatment Details")
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                med_name = st.text_input("Medication / Treatment Name *", placeholder="e.g. Sumatriptan, Naproxen, Myo-Inositol, Heating Pad")
            with col_m2:
                med_cat = st.selectbox("Category *", ["Prescription", "OTC / Supplement", "Lifestyle / Physical Therapy"])

            col_m3, col_m4, col_m5 = st.columns(3)
            with col_m3:
                med_dosage = st.text_input("Dosage / Strength", placeholder="e.g. 50 mg, 2000 mg, 1 tablet")
            with col_m4:
                med_freq = st.selectbox("Frequency", [
                    "As needed at symptom onset",
                    "Once daily in morning",
                    "Once daily at bedtime",
                    "Twice daily with meals",
                    "During menstruation days 1-3",
                    "Other / Weekly"
                ])
            with col_m5:
                med_start = st.date_input("Date Started", value=date.today())

            med_notes = st.text_area("Clinical Notes / Instructions", placeholder="e.g. Prescribed by gynecologist; take with plenty of water.")

            med_submit = st.form_submit_button("💾 Save Medication / Treatment", type="primary")

            if med_submit:
                if not med_name or not med_name.strip():
                    st.error("Medication or treatment name is required.")
                else:
                    new_med = MedicationEntry(
                        id=None,
                        profile_id=active_profile.id,
                        name=med_name.strip(),
                        category=med_cat,
                        dosage=med_dosage.strip() if med_dosage else "",
                        frequency=med_freq,
                        started_date=str(med_start),
                        notes=med_notes.strip() if med_notes else ""
                    )
                    add_medication(new_med)
                    st.success(f"✅ Successfully added '{med_name.strip()}' to your regimen!")

    with tab_med_list:

        profile_meds = get_medications(active_profile.id)
        st.caption(f"Showing **{len(profile_meds)}** active treatments for **{active_profile.display_name}**.")

        if not profile_meds:
            st.info("No medications or health interventions have been recorded yet.")
        else:
            for med in profile_meds:
                badge_style = "badge-routine" if med.category == "Prescription" else "badge-selfcare" if med.category == "OTC / Supplement" else "badge-prompt"
                st.markdown(f"""
                    <div class="resource-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                            <span class="{badge_style}">{med.category}</span>
                            <span style="font-size: 0.82rem; color: var(--text-muted);">Started: {med.started_date}</span>
                        </div>
                        <div class="content-card-title">{med.name}</div>
                        <p style="font-size: 0.95rem; color: var(--text-secondary); margin-bottom: 0.4rem;">
                            <b>Dosage & Frequency:</b> {med.dosage or 'Standard dose'} &bull; <i>{med.frequency}</i>
                        </p>
                        <p style="font-size: 0.88rem; color: var(--text-muted);">{med.notes or 'No additional instructions.'}</p>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"🗑️ Remove {med.name}", key=f"del_med_{med.id}", type="secondary"):
                    delete_medication(med.id, active_profile.id)
                    st.warning(f"Removed {med.name}.")
                    st.rerun()


# ==========================================
# Page: Personal Health Insights
# ==========================================
elif st.session_state["navigation"] == "Health Insights":

    st.markdown("### 📊 Personal Health Insights & Pattern Discovery")
    st.write(
        "Explainable analytics derived deterministically from your actual logged entries. "
        "HERPath AI highlights observable correlations without generating automated medical diagnoses."
    )

    all_entries = SymptomTrackerService.get_history(active_profile.id)
    engine = InsightsEngine(all_entries)
    metrics = engine.calculate_summary_metrics()

    # Metrics Summary Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Recorded Entries", metrics["total_entries"])
    with m2:
        st.metric("Distinct Days Logged", metrics["distinct_days"])
    with m3:
        st.metric("Average Severity", f"{metrics['avg_severity']}/10")
    with m4:
        st.metric("Primary Symptom", f"{metrics['top_symptom']} ({metrics['top_symptom_count']})")

    st.markdown("---")

    # Explainable Insights Engine Section
    st.markdown("#### 💡 Explainable Observation Statements")
    insights_list = engine.generate_explainable_insights()

    for item in insights_list:
        border_color = "var(--primary)"
        if item.get("type") == "insufficient_data":
            border_color = "var(--amber)"
        elif "correlation" in item.get("type", ""):
            border_color = "var(--teal)"

        st.markdown(f"""
            <div class="content-card" style="border-left: 4px solid {border_color};">
                <div class="content-card-title">{item['title']}</div>
                <p style="font-size: 1rem; color: var(--text-primary); margin-bottom: 0.5rem;">{item['observation']}</p>
                <div style="font-size: 0.86rem; color: var(--text-secondary);">{item.get('context_note', '')}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Visualizations
    st.markdown("#### 📈 Interactive Charts & Distributions")
    tab_chart1, tab_chart2, tab_chart3, tab_chart4 = st.tabs([
        "Symptom Timeline",
        "Frequency Breakdown",
        "Contextual Comparison",
        "Co-Occurrence Matrix"
    ])

    with tab_chart1:
        timeline_fig = engine.plot_severity_timeline()
        if timeline_fig:
            st.plotly_chart(timeline_fig, use_container_width=True)
        else:
            st.info("Log at least one symptom to display the timeline.")

    with tab_chart2:
        freq_fig = engine.plot_symptom_frequency()
        if freq_fig:
            st.plotly_chart(freq_fig, use_container_width=True)
        else:
            st.info("Log symptoms to view the frequency distribution.")

    with tab_chart3:
        context_fig = engine.plot_context_comparison()
        if context_fig:
            st.plotly_chart(context_fig, use_container_width=True)
        else:
            st.info("Log symptoms with Sleep Quality observations to generate contextual comparison charts.")

    with tab_chart4:
        heatmap_fig = engine.plot_cooccurrence_heatmap()
        if heatmap_fig:
            st.plotly_chart(heatmap_fig, use_container_width=True)
        else:
            st.info("Log multiple symptoms across shared dates to generate the co-occurrence matrix.")

    st.markdown("---")

    # Interactive Doctor Consultation Prep Kit
    st.markdown("#### 📋 Interactive Doctor Consultation Prep Kit")
    st.write(
        "Prepare for a high-impact, focused 10-15 minute consultation with your physician. "
        "Select your primary appointment objective to generate tailored talking points grounded in your tracked data."
    )

    goal_selection = st.radio(
        "Primary Consultation Objective:",
        [
            "Diagnostic Evaluation",
            "Medication & Treatment Review",
            "Transitional Care (Perimenopause / Cycle Changes)"
        ],
        horizontal=True
    )

    agenda = engine.generate_doctor_talking_points(goal_selection)

    st.markdown(f"""
        <div class="content-card" style="border-left: 4px solid var(--primary); background: #FAF9FC;">
            <div class="content-card-title">🎯 Appointment Agenda: {agenda['goal']}</div>
            <div style="font-size: 0.88rem; color: var(--text-muted); margin-bottom: 0.6rem;">
                <b>Evidence Baseline:</b> {agenda['data_summary']}
            </div>
            <div style="background: #FFFFFF; padding: 1rem; border-radius: 10px; border: 1px solid var(--border-color); margin-bottom: 0.8rem;">
                <b style="color: var(--primary);">Opening Statement (Your 30-Second Summary):</b>
                <p style="font-style: italic; color: var(--text-primary); margin-top: 0.3rem;">"{agenda['opening_statement']}"</p>
            </div>
            <b>Key Questions to Discuss:</b>
            <ul style="margin-top: 0.4rem; padding-left: 1.2rem; line-height: 1.6;">
                {''.join([f"<li><b>{q}</b></li>" for q in agenda['suggested_questions']])}
            </ul>
        </div>
    """, unsafe_allow_html=True)



# ==========================================
# Page 4: Care Navigator
# ==========================================
elif st.session_state["navigation"] == "Care Navigator":
    st.markdown("### 🛡️ Care Guidance & Safety Navigator")
    st.write(
        "A transparent, rule-based clinical safety navigator grounded in established public health triage frameworks. "
        "Evaluates red flags, persistent discomfort, and routine care needs to help you take safe next steps."
    )

    st.markdown(f"""
        <div class="disclaimer-box">
            <b>Safety Notice:</b> {CLINICAL_DISCLAIMER}
        </div>
    """, unsafe_allow_html=True)

    with st.form("safety_navigator_form"):
        st.markdown("##### 1. Describe Your Current Concern")
        c1, c2 = st.columns(2)

        with c1:
            nav_category = st.selectbox("Category", list(SYMPTOM_TAXONOMY.keys()))
        with c2:
            suggested = SYMPTOM_TAXONOMY.get(nav_category, [])
            nav_symptom = st.selectbox("Symptom", suggested)

        c3, c4 = st.columns(2)
        with c3:
            nav_severity = st.slider("Current Severity Rating (1 to 10)", min_value=1, max_value=10, value=6)
        with c4:
            nav_duration = st.number_input("Duration (hours)", min_value=0.0, max_value=720.0, value=12.0, step=1.0)

        st.markdown("##### 2. Check Any Critical Clinical Warning Flags (Emergency Checklist)")
        warning_flags = SafetyNavigator.get_supported_emergency_warning_signs()
        checked_flags = []
        for wf in warning_flags:
            if st.checkbox(f"{wf['label']} ({wf['level']} Warning)", key=f"nav_wf_{wf['id']}"):
                checked_flags.append(wf["label"])

        nav_notes = st.text_input("Additional Observations / Notes", placeholder="e.g. onset was sudden, accompanied by fever or numbness")

        evaluate_btn = st.form_submit_button("🛡️ Evaluate Care Guidance", type="primary")

    if evaluate_btn:
        assessment = SafetyNavigator.evaluate(
            symptom=nav_symptom,
            category=nav_category,
            severity=nav_severity,
            duration_hours=nav_duration,
            notes=nav_notes,
            red_flags_checked=checked_flags
        )

        st.markdown("<br/>", unsafe_allow_html=True)

        # Render Assessment Box according to Priority Hierarchy
        if assessment.priority == PRIORITY_EMERGENCY:
            st.markdown(f"""
                <div class="disclaimer-urgent">
                    <span class="badge-emergency">EMERGENCY EVALUATION NEEDED</span>
                    <h3 style="color: #7D232F; margin: 0.6rem 0;">{assessment.headline}</h3>
                    <p><b>Immediate Safety Guidance:</b></p>
                    <ul>
                        {''.join([f"<li><b>{act}</b></li>" for act in assessment.recommended_actions])}
                    </ul>
                    <p style="margin-top: 0.8rem; font-weight: 700; color: #B94957;">{assessment.emergency_contact}</p>
                </div>
            """, unsafe_allow_html=True)

        elif assessment.priority == PRIORITY_PROMPT:
            st.markdown(f"""
                <div class="content-card" style="border-left: 5px solid var(--amber);">
                    <span class="badge-prompt">PROMPT MEDICAL EVALUATION (24–48 Hours)</span>
                    <h3 style="color: #9A6014; margin: 0.6rem 0;">{assessment.headline}</h3>
                    <p><b>Recommended Steps:</b></p>
                    <ul>
                        {''.join([f"<li>{act}</li>" for act in assessment.recommended_actions])}
                    </ul>
                </div>
            """, unsafe_allow_html=True)

        elif assessment.priority == PRIORITY_ROUTINE:
            st.markdown(f"""
                <div class="content-card" style="border-left: 5px solid var(--teal);">
                    <span class="badge-routine">ROUTINE CLINICAL CONSULTATION</span>
                    <h3 style="color: var(--teal-dark); margin: 0.6rem 0;">{assessment.headline}</h3>
                    <p><b>Recommended Steps:</b></p>
                    <ul>
                        {''.join([f"<li>{act}</li>" for act in assessment.recommended_actions])}
                    </ul>
                </div>
            """, unsafe_allow_html=True)

        else:
            st.markdown(f"""
                <div class="content-card" style="border-left: 5px solid var(--primary);">
                    <span class="badge-selfcare">HEALTH EDUCATION & SELF-CARE MONITORING</span>
                    <h3 style="color: var(--primary); margin: 0.6rem 0;">{assessment.headline}</h3>
                    <p><b>Supportive Self-Care Guidelines:</b></p>
                    <ul>
                        {''.join([f"<li>{act}</li>" for act in assessment.recommended_actions])}
                    </ul>
                </div>
            """, unsafe_allow_html=True)

        # Transparent Rationale Section
        st.markdown("#### 🔍 Why Is This Guidance Being Shown?")
        for r in assessment.rationale:
            st.markdown(f"- {r}")

        # Linked Educational Resources
        if assessment.educational_topics:
            st.markdown("#### 📚 Recommended Educational Readings")
            for top in assessment.educational_topics:
                recs = health_library.get_recommended_resources_for_symptom(top)
                for r in recs:
                    st.markdown(f"- **[{r['title']}]({r['source_url']})** &bull; *{r['source_org']}* ({r['category']})")

    st.markdown("---")
    st.markdown("#### 🚨 Emergency SOS & Regional Helplines Guide")
    st.write("Keep these immediate emergency contact numbers accessible if you or someone around you experiences acute distress:")

    sos1, sos2, sos3 = st.columns(3)
    with sos1:
        st.markdown("""
            <div class="content-card" style="border-top: 4px solid var(--rose);">
                <b style="color: var(--rose-dark); font-size: 1.1rem;">🚑 National Emergency</b>
                <p style="font-size: 1.4rem; font-weight: 800; color: #1C192B; margin: 0.4rem 0;">112 / 911 / 999</p>
                <div style="font-size: 0.82rem; color: var(--text-muted);">
                    India & EU: <b>112</b> &bull; US: <b>911</b> &bull; UK: <b>999</b><br/>Immediate police, fire, and ambulance dispatch.
                </div>
            </div>
        """, unsafe_allow_html=True)

    with sos2:
        st.markdown("""
            <div class="content-card" style="border-top: 4px solid var(--teal);">
                <b style="color: var(--teal-dark); font-size: 1.1rem;">🌸 Women's Helplines</b>
                <p style="font-size: 1.4rem; font-weight: 800; color: #1C192B; margin: 0.4rem 0;">1091 / 181</p>
                <div style="font-size: 0.82rem; color: var(--text-muted);">
                    India National Women's Helpline: <b>181</b> &bull; Women Police Helpline: <b>1091</b><br/>24/7 confidential safety & medical support.
                </div>
            </div>
        """, unsafe_allow_html=True)

    with sos3:
        st.markdown("""
            <div class="content-card" style="border-top: 4px solid var(--primary);">
                <b style="color: var(--primary); font-size: 1.1rem;">🧠 Mental Health & Advice</b>
                <p style="font-size: 1.4rem; font-weight: 800; color: #1C192B; margin: 0.4rem 0;">988 / 111 / 14416</p>
                <div style="font-size: 0.82rem; color: var(--text-muted);">
                    US Crisis: <b>988</b> &bull; NHS UK: <b>111</b> &bull; India Tele-MANAS: <b>14416</b><br/>Free mental health and clinical advice.
                </div>
            </div>
        """, unsafe_allow_html=True)

    with st.expander("🏥 Emergency Room Preparation Checklist"):
        st.markdown("""
            - [ ] **Identification & Details:** Government ID, insurance or health scheme card.
            - [ ] **Current Medication List:** Bring your bottles or export your HERPath Medication list.
            - [ ] **Symptom Timeline:** Exact time acute onset began, peak severity, and triggers.
            - [ ] **HERPath Clinician Report:** Download your PDF from the 'My Health Report' tab.
            - [ ] **Do Not Drive Alone:** In severe acute conditions (syncope, heavy bleeding, chest pain), call an ambulance or have a trusted adult drive you.
        """)



# ==========================================
# Page 5: Women's Health Library
# ==========================================
elif st.session_state["navigation"] == "Women's Health Library":
    st.markdown("### 📚 Trusted Women's Health Library")
    st.write(
        "A curated directory of evidence-based educational articles from internationally recognized medical authorities "
        "(WHO, NHS, CDC, ACOG, Mayo Clinic, Johns Hopkins Medicine). "
        "These resources provide general health literacy and are strictly educational."
    )

    col_s, col_c = st.columns([2.5, 1.5])
    with col_s:
        search_query = st.text_input("🔍 Search library topics, symptoms, or organizations", placeholder="e.g. PCOS, migraine, iron, sleep...")
    with col_c:
        categories = health_library.get_categories()
        chosen_cat = st.selectbox("Filter by Category", categories)

    filtered_articles = health_library.search_resources(query=search_query, category=chosen_cat)
    st.caption(f"Showing **{len(filtered_articles)}** evidence-based resources.")

    for art in filtered_articles:
        st.markdown(f"""
            <div class="resource-card">
                <div class="resource-source">{art['source_org']} &bull; {art['category']}</div>
                <div class="resource-title">{art['title']}</div>
                <div class="resource-desc">{art['summary']}</div>
                <div style="margin-bottom: 0.6rem;">
                    <b>Key Clinical Points:</b>
                    <ul style="margin-top: 0.3rem; margin-bottom: 0.6rem; padding-left: 1.2rem; font-size: 0.9rem; color: var(--text-secondary);">
                        {''.join([f"<li>{pt}</li>" for pt in art['key_points']])}
                    </ul>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem;">
                    <span style="color: var(--text-muted);">Source: <i>{art['source_title']}</i> (Reviewed: {art.get('last_reviewed', '2024')})</span>
                    <a href="{art['source_url']}" target="_blank" style="color: var(--primary); font-weight: 700; text-decoration: none;">
                        Visit Official Source &rarr;
                    </a>
                </div>
            </div>
        """, unsafe_allow_html=True)


# ==========================================
# Page 6: My Health Report (PDF Export)
# ==========================================
elif st.session_state["navigation"] == "My Health Report":
    st.markdown("### 📄 Clinician-Ready Health Report")
    st.write(
        "Generate a structured, professional PDF summary of your logged health observations for your next doctor's appointment. "
        "Helps you communicate dates, severity trajectories, functional impact, and discussion questions clearly."
    )

    st.markdown("##### 1. Select Reporting Period")
    c_r1, c_r2 = st.columns(2)
    with c_r1:
        rep_start = st.date_input("Start Date", value=date.today() - timedelta(days=30))
    with c_r2:
        rep_end = st.date_input("End Date", value=date.today() + timedelta(days=1))

    # Fetch records in range
    report_entries = SymptomTrackerService.get_history(
        profile_id=active_profile.id,
        start_date=str(rep_start),
        end_date=str(rep_end)
    )

    st.markdown("##### 2. Preview Report Contents")
    rep_engine = InsightsEngine(report_entries)
    rep_metrics = rep_engine.calculate_summary_metrics()

    p1, p2, p3, p4 = st.columns(4)
    with p1:
        st.metric("Entries in Period", rep_metrics["total_entries"])
    with p2:
        st.metric("Distinct Dates", rep_metrics["distinct_days"])
    with p3:
        st.metric("Avg Severity", f"{rep_metrics['avg_severity']}/10")
    with p4:
        st.metric("Top Reported Symptom", rep_metrics["top_symptom"])

    st.markdown("---")

    # Generate and Download Action
    if not report_entries:
        st.warning("⚠️ No symptom records were logged during this date range. You can still export a baseline template, or expand the date range.")

    generator = ClinicianReportGenerator(
        profile=active_profile,
        entries=report_entries,
        start_date=str(rep_start),
        end_date=str(rep_end),
        medications=get_medications(active_profile.id)
    )


    try:
        pdf_bytes = generator.generate_pdf_bytes()
        file_name = f"HERPath_Report_{active_profile.id}_{rep_start}_{rep_end}.pdf"

        st.download_button(
            label="📥 Download Clinician Health Report (PDF)",
            data=pdf_bytes,
            file_name=file_name,
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Error compiling PDF: {str(e)}")

    st.markdown("---")
    st.markdown("##### 3. Recommended Consultation Discussion Questions Preview")
    st.markdown("""
        - *Based on the frequency and severity trajectory of these symptoms, what diagnostic evaluations (hormone profile, ultrasound, ferritin) do you recommend?*
        - *Are there evidence-based pharmacologic or non-pharmacologic interventions for high-severity episodes?*
        - *Do the observed patterns correlate with conditions like PCOS, endometriosis, hormonal migraine, or perimenopause?*
        - *What red-flag signs should prompt an emergency department visit?*
    """)


# ==========================================
# Page 7: Ask HERPath (Grounded Educational Assistant)
# ==========================================
elif st.session_state["navigation"] == "Ask HERPath":
    st.markdown("### 🤖 Ask HERPath — Health Literacy Assistant")
    st.write(
        "Ask general health literacy questions grounded strictly in our curated medical library (WHO, NHS, CDC, ACOG). "
        "Strictly non-diagnostic: will not diagnose diseases, prescribe medication, or replace professional care."
    )

    st.markdown(f"""
        <div class="disclaimer-box">
            <b>Assistant Boundaries:</b> Grounded in curated medical resources. Does not provide clinical triage or personalized diagnoses.
        </div>
    """, unsafe_allow_html=True)

    user_query = st.text_input(
        "Enter your health literacy question:",
        placeholder="e.g. What is the difference between normal cramps and endometriosis? How does iron deficiency affect energy?"
    )

    if user_query:
        # Check emergency safety trigger first!
        emergency_assessment = SafetyNavigator.evaluate(
            symptom=user_query,
            category="Systemic & Energy",
            severity=5,
            notes=user_query
        )

        if emergency_assessment.priority == PRIORITY_EMERGENCY:
            st.markdown(f"""
                <div class="disclaimer-urgent">
                    <span class="badge-emergency">SAFETY ALERT: URGENT WARNING SIGN DETECTED</span>
                    <h3 style="color: #7D232F; margin: 0.5rem 0;">{emergency_assessment.headline}</h3>
                    <p>{emergency_assessment.rationale[0]}</p>
                    <p><b>Please seek emergency medical evaluation immediately.</b> {emergency_assessment.emergency_contact}</p>
                </div>
            """, unsafe_allow_html=True)

        # Retrieve relevant passages from health library
        matches = health_library.search_resources(query=user_query)
        if matches:
            st.markdown(f"#### 📖 Grounded Findings ({len(matches)} Relevant Guides Found)")
            for match in matches[:3]:
                st.markdown(f"""
                    <div class="content-card" style="border-left: 4px solid var(--teal);">
                        <div class="resource-source">{match['source_org']} &bull; {match['category']}</div>
                        <div class="content-card-title">{match['title']}</div>
                        <p>{match['summary']}</p>
                        <b>Verified Educational Takeaways:</b>
                        <ul style="font-size: 0.92rem; margin-top: 0.4rem;">
                            {''.join([f"<li>{pt}</li>" for pt in match['key_points']])}
                        </ul>
                        <div style="font-size: 0.85rem; margin-top: 0.6rem;">
                            <a href="{match['source_url']}" target="_blank" style="color: var(--primary); font-weight: 600;">
                                Read full guide on {match['source_org']} &rarr;
                            </a>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No exact matching verified articles found for this specific query.")
            st.write(
                "HERPath AI only presents information grounded in our verified library to prevent hallucinated medical advice. "
                "You can browse all articles in the **Women's Health Library** or consult a healthcare provider."
            )
            if st.button("Browse Health Library"):
                navigate_to("Women's Health Library")


# ==========================================
# Page 8: Privacy and Settings
# ==========================================
elif st.session_state["navigation"] == "Privacy and Settings":
    st.markdown("### ⚙️ Privacy & Profile Settings")
    st.write("Manage your local profile, data retention preferences, and demo datasets.")

    # Privacy Notice
    st.markdown(f"""
        <div class="content-card">
            <div class="content-card-title">🔒 Privacy & Data Protection Architecture</div>
            <p style="color: var(--text-secondary); line-height: 1.6;">
                HERPath AI is built with privacy-first principles appropriate for sensitive health information:
            </p>
            <ul style="color: var(--text-secondary); line-height: 1.6;">
                <li><b>Local Storage Only:</b> All symptom records and profiles are stored locally in an on-device SQLite database.</li>
                <li><b>No Cloud Sync / Telemetry:</b> No personal health entries, notes, or identities are transmitted to remote servers.</li>
                <li><b>No Third-Party Trackers:</b> Zero analytics cookies, ad-networks, or tracking beacons.</li>
                <li><b>User Controlled Deletion:</b> You can clear your symptom records or erase your profile at any time.</li>
                <li><b>Prototype Boundaries:</b> This prototype runs on a single local device. It is not an enterprise HIPAA or DPDP compliant cloud EHR system.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

    # Profile Configuration
    st.markdown("##### 👤 Profile Customization")
    with st.form("profile_customization_form"):
        display_name_val = st.text_input("Display Name / Pseudonym", value=active_profile.display_name)
        track_menstrual_toggle = st.checkbox(
            "Enable Menstrual & Reproductive Tracking Features",
            value=active_profile.preferences.get("track_menstrual", True),
            help="Optional tracking. Disabling this removes menstrual cycle questions from your symptom journal."
        )

        save_pref_btn = st.form_submit_button("Save Profile Settings")
        if save_pref_btn:
            new_prefs = active_profile.preferences.copy()
            new_prefs["track_menstrual"] = track_menstrual_toggle
            update_profile_preferences(active_profile.id, new_prefs)
            st.success("✅ Profile preferences updated successfully!")
            st.rerun()

    st.markdown("---")

    # Create New Profile
    st.markdown("##### ➕ Create a New Local Profile")
    with st.expander("Add New Profile"):
        with st.form("new_profile_form"):
            new_pid = st.text_input("Profile ID (alphanumeric, no spaces)", placeholder="e.g. user_maya")
            new_name = st.text_input("Profile Name / Pseudonym", placeholder="e.g. Maya S.")
            new_track = st.checkbox("Track Menstrual Context", value=True)
            create_btn = st.form_submit_button("Create Profile")
            if create_btn:
                if not new_pid or not new_name:
                    st.error("Both Profile ID and Display Name are required.")
                else:
                    try:
                        create_profile(new_pid.strip(), new_name.strip(), {"track_menstrual": new_track, "consent_acknowledged": True})
                        st.session_state["current_profile_id"] = new_pid.strip()
                        st.success(f"Created and switched to profile: {new_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating profile: {str(e)}")

    # Data Portability & Backup
    st.markdown("##### 💾 Data Portability & Backup (Privacy First)")
    st.write("Export your complete health logs for spreadsheet analysis or to create an offline backup. You can also restore a previous JSON backup.")

    port1, port2 = st.columns(2)
    with port1:
        json_backup_str = export_profile_data_json(active_profile.id)
        st.download_button(
            label="📥 Download Complete Backup (JSON)",
            data=json_backup_str,
            file_name=f"HERPath_Backup_{active_profile.id}_{date.today()}.json",
            mime="application/json",
            use_container_width=True
        )

    with port2:
        csv_history_str = export_symptoms_csv(active_profile.id)
        st.download_button(
            label="📊 Download Symptoms for Spreadsheets (CSV)",
            data=csv_history_str,
            file_name=f"HERPath_Symptoms_{active_profile.id}_{date.today()}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with st.expander("📤 Restore Data from JSON Backup"):
        uploaded_backup = st.file_uploader("Upload previously exported HERPath JSON backup file", type=["json"])
        if uploaded_backup is not None:
            if st.button("Apply Backup to Active Profile"):
                try:
                    content_str = uploaded_backup.read().decode("utf-8")
                    imported_s, imported_m = import_profile_data_json(active_profile.id, content_str)
                    st.success(f"✅ Successfully restored {imported_s} symptoms and {imported_m} medications into {active_profile.display_name}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error restoring backup: {str(e)}")

    st.markdown("---")

    # Data Actions
    st.markdown("##### 🗄️ Database & Demo Data Controls")

    col_d1, col_d2, col_d3 = st.columns(3)

    with col_d1:
        if st.button("🔄 Reload Fictional Demo Data", use_container_width=True):
            seed_demo_data()
            st.success("Demo profiles and records successfully seeded!")
            st.rerun()

    with col_d2:
        if st.button("🧹 Clear Symptoms for This Profile", use_container_width=True, type="secondary"):
            count = clear_profile_symptoms(active_profile.id)
            st.warning(f"Cleared {count} symptom entries for {active_profile.display_name}.")
            st.rerun()

    with col_d3:
        if st.button("❌ Delete Active Profile", use_container_width=True, type="secondary"):
            if len(list_profiles()) <= 1:
                st.error("Cannot delete the only remaining profile.")
            else:
                delete_profile(active_profile.id)
                st.session_state["current_profile_id"] = list_profiles()[0].id
                st.warning("Profile deleted.")
                st.rerun()
