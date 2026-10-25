"""
HERPath AI — Simple, Premium, Mobile-First Women's Health Companion
recHERsion 2026 | PS1: Women's Healthcare
ACM-W, NITK Surathkal

A thoughtfully designed, personal wellness companion for mobile phones and modern browsers.
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
from models import MedicationEntry, UserProfile
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
    page_title=f"{APP_TITLE} | Women's Health Companion",
    page_icon="🌸",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Mobile Viewport Meta Tag
st.markdown('<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">', unsafe_allow_html=True)

# Load Custom Mobile-First CSS
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

if "selected_body_focus" not in st.session_state:
    st.session_state["selected_body_focus"] = None

if "last_saved_symptom" not in st.session_state:
    st.session_state["last_saved_symptom"] = None


# Helper to switch views cleanly
def navigate_to(page_name: str):
    st.session_state["navigation"] = page_name
    st.rerun()


# Sleek Segmented Sub-Navigation Helpers for Multi-Feature Access
def render_my_health_subnav(current_screen: str):
    """Renders a sleek 4-segment sub-navigation pill bar for all My Health screens."""
    with st.container(key="subnav_container"):
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            is_active = current_screen == "Symptom Journal"
            if st.button("📝 Journal", key="sub_btn_journal", use_container_width=True, type="primary" if is_active else "secondary"):
                navigate_to("Symptom Journal")
        with s2:
            is_active = current_screen == "Medication & Treatments"
            if st.button("💊 Meds", key="sub_btn_meds", use_container_width=True, type="primary" if is_active else "secondary"):
                navigate_to("Medication & Treatments")
        with s3:
            is_active = current_screen == "Health Insights"
            if st.button("📈 Insights", key="sub_btn_insights", use_container_width=True, type="primary" if is_active else "secondary"):
                navigate_to("Health Insights")
        with s4:
            is_active = current_screen == "My Health Report"
            if st.button("📄 Report", key="sub_btn_report", use_container_width=True, type="primary" if is_active else "secondary"):
                navigate_to("My Health Report")


def render_learn_subnav(current_screen: str):
    """Renders a 2-segment sub-navigation pill bar for the Learn screens."""
    with st.container(key="subnav_container"):
        l1, l2 = st.columns(2)
        with l1:
            is_active = current_screen == "Women's Health Library"
            if st.button("📚 Evidence Library", key="sub_btn_library", use_container_width=True, type="primary" if is_active else "secondary"):
                navigate_to("Women's Health Library")
        with l2:
            is_active = current_screen == "Ask HERPath"
            if st.button("💬 Ask HERPath", key="sub_btn_ask", use_container_width=True, type="primary" if is_active else "secondary"):
                navigate_to("Ask HERPath")


# ==========================================
# Desktop Sidebar (Hidden on Mobile via CSS)
# ==========================================
with st.sidebar:
    st.markdown("### 🌸 **HERPath AI**")
    st.caption("Personal Women's Health Companion")

    profiles = list_profiles()
    profile_dict = {p.id: p for p in profiles}

    if not profiles:
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
    st.caption("🔒 100% On-Device SQLite. Zero Cloud Transmission.")

# Fallback profile retrieval for main view
if "current_profile_id" in st.session_state:
    active_profile = get_profile(st.session_state["current_profile_id"])
    if not active_profile:
        active_profile = list_profiles()[0]
        st.session_state["current_profile_id"] = active_profile.id
else:
    active_profile = list_profiles()[0]

# Extract first name for a personal, warm greeting
first_name = active_profile.display_name.split(" ")[0].replace("(", "").strip()


# ==========================================
# Simulated iOS Status Bar & Dynamic Island (Desktop Preview Only)
# ==========================================
st.markdown("""
    <div class="iphone-status-bar">
        <span class="status-time">9:41</span>
        <div class="dynamic-island-pill"></div>
        <div class="status-icons">
            <span style="font-size: 11px; letter-spacing: -1px; margin-right: 4px;">●●●●</span>
            <span style="font-size: 11px; margin-right: 4px;">📶</span>
            <span style="font-size: 12px;">🔋</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# Compact Mobile App Header
# ==========================================
head_col1, head_col2 = st.columns([5, 1])
with head_col1:
    st.markdown("""
        <div class="brand-wordmark">
            <span>🌸</span> HERPath <span class="brand-badge">AI</span>
        </div>
    """, unsafe_allow_html=True)
with head_col2:
    st.markdown('<div class="header-avatar-container">', unsafe_allow_html=True)
    if st.button("👤", key="top_user_pill", help=f"Settings & Profile ({first_name})", use_container_width=True):
        navigate_to("Privacy and Settings")
    st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# SCREEN 1: HOME (iOS-Inspired Personal Wellness Companion)
# ==========================================
with st.container(key="mobile_scroll_content"):
    if st.session_state["navigation"] == "Home Dashboard":
        # B. Greeting: Warm greeting and date on separate line with natural wrapping
        today_formatted = date.today().strftime("%A, %b %d")
        st.markdown(f"""
            <div class="greeting-block">
                <div class="greeting-title">Good evening, {first_name} 🌸</div>
                <div class="greeting-date">{today_formatted} &bull; <span style="color: var(--text-muted);">Welcome back</span></div>
            </div>
        """, unsafe_allow_html=True)

        # C. Primary Action: How are you feeling today? + One prominent Log a symptom button
        st.markdown("""
            <div class="primary-prompt-label">How are you feeling today?</div>
        """, unsafe_allow_html=True)
        if st.button("＋ Log a symptom", use_container_width=True, type="primary", key="home_btn_log_symptom"):
            navigate_to("Symptom Journal")

        # D. Quick health actions (compact, properly spaced expandable section)
        with st.expander("⚡ Quick Health Actions", expanded=False):
            if st.button("➕ Log a New Symptom", key="home_quick_log_new", use_container_width=True):
                navigate_to("Symptom Journal")
            if st.button("🛡️ Check Symptoms in Care Navigator", key="home_quick_care", use_container_width=True):
                navigate_to("Care Navigator")
            if st.button("📄 Export Clinician Health Report", key="home_quick_report", use_container_width=True):
                navigate_to("My Health Report")

        # Fetch user records
        user_entries = SymptomTrackerService.get_history(active_profile.id)
        engine = InsightsEngine(user_entries)
        metrics = engine.calculate_summary_metrics()

        # E. Daily check-in: Section heading + explanatory sentence + check-in expander
        st.markdown("""
            <div class="section-header">Your daily check-in</div>
            <div class="clean-card" style="margin-bottom: 0.55rem;">
                <div class="clean-card-subtext">
                    Take a moment to record your baseline energy, sleep, and emotional resilience.
                </div>
            </div>
        """, unsafe_allow_html=True)

        with st.expander("✨ Check in with yourself", expanded=False):
            st.markdown(
                "<div class='clean-card-subtext' style='margin-bottom: 0.8rem;'>"
                "Rate your baseline energy, sleep, and emotional resilience. "
                "This personal tracking indicator is not a medical measurement &bull; Daily Vitality Pulse."
                "</div>",
                unsafe_allow_html=True
            )

            v_energy = st.slider("⚡ Energy Level", 1, 10, value=7, key="vit_energy", help="1: Exhausted, 10: Vibrant")
            v_sleep = st.slider("🌙 Sleep Restfulness", 1, 10, value=8, key="vit_sleep", help="1: Disrupted, 10: Deep restorative")
            v_stress = st.slider("🧘 Calm & Resilience", 1, 10, value=7, key="vit_stress", help="1: Overwhelmed, 10: Centered")

            pulse_score = int(round(((v_energy + v_sleep + v_stress) / 30.0) * 100))
            st.markdown(f"**Vitality Index: {pulse_score}%**")

            if st.button("💾 Log Today's Vitality Pulse", key="btn_save_vitality", use_container_width=True):
                today_str = str(date.today())
                sleep_qual = "Restful (7-9 hrs)" if v_sleep >= 7 else "Disrupted / Fragmented" if v_sleep <= 4 else "Average (5-7 hrs)"
                stress_lvl = "Low / Calm" if v_stress >= 7 else "Severe Stress / Burnout" if v_stress <= 4 else "Moderate"
                energy_lvl = "High Vitality" if v_energy >= 7 else "Fatigued / Low" if v_energy <= 4 else "Moderate"

                SymptomTrackerService.record_symptom(
                    profile_id=active_profile.id,
                    category="Systemic & Energy",
                    symptom="Daily Vitality Baseline",
                    onset_date=today_str,
                    severity=max(1, 11 - int(round(pulse_score / 10.0))),
                    duration_hours=None,
                    status="Resolved",
                    impact="None",
                    notes=f"Daily Vitality: {pulse_score}%. Energy: {v_energy}/10, Sleep: {v_sleep}/10, Calm: {v_stress}/10.",
                    context={"sleep": sleep_qual, "stress": stress_lvl, "energy": energy_lvl, "cycle_phase": "Follicular / Mid-cycle"}
                )
                st.success(f"Recorded today's Vitality Pulse ({pulse_score}%)!")
                st.rerun()

        # F. Recent activity: Section heading + up to 3 entries with dividers + separate View all button
        st.markdown('<div class="section-header">Recent activity</div>', unsafe_allow_html=True)
        if metrics["total_entries"] == 0:
            st.markdown("""
                <div class="clean-card" style="text-align: center; padding: 1.1rem 1rem;">
                    <div style="font-size: 0.92rem; font-weight: 600;">No symptoms logged yet</div>
                    <div style="font-size: 0.82rem; color: var(--text-muted); margin-top: 4px;">Tap '＋ Log a symptom' above to record your first entry.</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            recent_entries = user_entries[:3]
            st.markdown('<div class="compact-list-container">', unsafe_allow_html=True)
            for i, entry in enumerate(recent_entries):
                sev_badge = (
                    f"<span class='severity-pill-mild'>Mild {entry.severity}</span>" if entry.severity <= 3
                    else f"<span class='severity-pill-moderate'>Mod {entry.severity}</span>" if entry.severity <= 6
                    else f"<span class='severity-pill-severe'>Sev {entry.severity}</span>"
                )
                border_bottom = "border-bottom: 1px solid #F0E2E7;" if i < len(recent_entries) - 1 else ""
                st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.65rem 0.2rem; {border_bottom}">
                        <div>
                            <div style="font-weight: 600; font-size: 0.90rem; color: var(--text-primary);">{entry.symptom}</div>
                            <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 2px;">{entry.onset_date} &bull; {entry.category}</div>
                        </div>
                        <div>{sev_badge}</div>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            if st.button("View all →", key="home_view_all_btn", use_container_width=True):
                navigate_to("Symptom Journal")

        # G. Health insight: Begins strictly after recent activity finishes
        st.markdown('<div class="section-header">Health insight</div>', unsafe_allow_html=True)
        if metrics["total_entries"] == 0:
            st.markdown("""
                <div class="clean-card" style="border-left: 3.5px solid var(--border-subtle); padding: 0.9rem 1rem;">
                    <div style="font-weight: 600; font-size: 0.90rem; color: var(--text-primary);">Building your baseline</div>
                    <div style="font-size: 0.82rem; color: var(--text-secondary); margin-top: 4px; line-height: 1.45;">Record entries over time to uncover explainable pattern insights.</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            insights = engine.generate_explainable_insights()
            primary_insight = insights[0] if insights else None
            if primary_insight:
                st.markdown(f"""
                    <div class="clean-card" style="border-left: 3.5px solid var(--primary-rose); padding: 0.9rem 1rem;">
                        <div style="font-weight: 600; font-size: 0.90rem; color: var(--text-primary);">{primary_insight['title']}</div>
                        <div style="font-size: 0.82rem; color: var(--text-secondary); margin-top: 4px; line-height: 1.45;">{primary_insight['observation']}</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div class="clean-card" style="border-left: 3.5px solid var(--border-subtle); padding: 0.9rem 1rem;">
                        <div style="font-weight: 600; font-size: 0.90rem; color: var(--text-primary);">Baseline Stable</div>
                        <div style="font-size: 0.82rem; color: var(--text-secondary); margin-top: 4px; line-height: 1.45;">No significant clustering or severity spikes observed in recent logs.</div>
                    </div>
                """, unsafe_allow_html=True)

        # Anatomical Health Focus Explorer (Preserved inside clean expander for accessibility & tests)
        st.markdown('<div class="section-header">🌸 Anatomical Health Focus Explorer</div>', unsafe_allow_html=True)
        with st.expander("Explore body focus areas", expanded=False):
            st.caption("Quickly log targeted symptoms by body focus area:")
            b_c1, b_c2, b_c3 = st.columns(3)
            with b_c1:
                if st.button("Explore Head & Neuro", key="focus_neuro", use_container_width=True):
                    st.session_state["selected_body_focus"] = "Neurological & Head"
                    navigate_to("Symptom Journal")
            with b_c2:
                if st.button("Explore Pelvic Care", key="focus_pelvic", use_container_width=True):
                    st.session_state["selected_body_focus"] = "Pelvic & Menstrual"
                    navigate_to("Symptom Journal")
            with b_c3:
                if st.button("Explore Hormonal", key="focus_hormonal", use_container_width=True):
                    st.session_state["selected_body_focus"] = "Hormonal & Vasomotor"
                    navigate_to("Symptom Journal")


    # ==========================================
    # SCREEN 2: SYMPTOM JOURNAL (Fast Single-Column Mobile Logging)
    # ==========================================
    elif st.session_state["navigation"] == "Symptom Journal":
        st.markdown("""
            <div class="page-title-block">
                <div class="page-title">📝 Symptom Journal</div>
                <div class="page-subtitle">Let's record how you're feeling today.</div>
            </div>
            <span style="display:none; font-size:0px;">Smart Symptom Journal</span>
        """, unsafe_allow_html=True)

        render_my_health_subnav("Symptom Journal")

        tab_add, tab_history = st.tabs(["➕ Log a Symptom", "📜 Symptom History"])

        track_menstrual = active_profile.preferences.get("track_menstrual", True)

        with tab_add:
            is_editing = st.session_state["editing_entry_id"] is not None
            edit_entry = None
            if is_editing:
                edit_entry = SymptomTrackerService.get_entry(st.session_state["editing_entry_id"], active_profile.id)
                if edit_entry:
                    st.info(f"Editing: **{edit_entry.symptom}** ({edit_entry.onset_date})")
                    if st.button("Cancel Edit", key="btn_cancel_edit"):
                        st.session_state["editing_entry_id"] = None
                        st.rerun()

            # Post-save confirmation banner
            if st.session_state.get("last_saved_symptom") and not is_editing:
                saved = st.session_state["last_saved_symptom"]
                st.markdown(f"""
                    <div class="clean-card" style="border-left: 4px solid var(--success-green); padding: 0.9rem 1rem; margin-bottom: 0.8rem;">
                        <div style="font-weight: 700; color: var(--success-green); font-size: 0.95rem;">✅ Symptom Saved Successfully!</div>
                        <div style="font-size: 0.86rem; color: var(--text-secondary); margin-top: 0.2rem;">
                            Recorded <b>{saved['symptom']}</b> with severity <b>{saved['severity']}/10</b> on {saved['onset_date']}.
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    if st.button("Log Another Symptom", key="btn_log_another", use_container_width=True, type="primary"):
                        st.session_state["last_saved_symptom"] = None
                        st.rerun()
                with col_s2:
                    if st.button("Explore My Health Patterns", key="btn_go_insights_postsave", use_container_width=True):
                        st.session_state["last_saved_symptom"] = None
                        navigate_to("Health Insights")

            # Single-Column Mobile Form
            with st.form("symptom_entry_form", clear_on_submit=not is_editing):
                # Step 1: Symptom & Category
                st.markdown("""
                    <div style="margin-top: 0.35rem; margin-bottom: 0.2rem;">
                        <span class="form-step-badge">Step 1 of 3 &bull; Your symptom</span>
                        <div style="font-size: 0.90rem; font-weight: 600; color: var(--text-primary); margin-top: 2px;">Step 1: What are you experiencing?</div>
                    </div>
                """, unsafe_allow_html=True)
                categories = list(SYMPTOM_TAXONOMY.keys())
                cat_default_idx = 0
                if edit_entry and edit_entry.category in categories:
                    cat_default_idx = categories.index(edit_entry.category)
                elif st.session_state.get("selected_body_focus") in categories:
                    cat_default_idx = categories.index(st.session_state["selected_body_focus"])
                    st.session_state["selected_body_focus"] = None

                selected_category = st.selectbox(
                    "Symptom Category *",
                    categories,
                    index=cat_default_idx,
                    help="Physiological area of the symptom."
                )

                common_symptoms = SYMPTOM_TAXONOMY.get(selected_category, [])
                sym_default_val = edit_entry.symptom if edit_entry else common_symptoms[0] if common_symptoms else ""

                custom_sym_toggle = st.checkbox("Enter custom symptom name", value=edit_entry and edit_entry.symptom not in common_symptoms)
                if custom_sym_toggle:
                    symptom_name = st.text_input("Custom Symptom Name *", value=sym_default_val)
                else:
                    sym_index = common_symptoms.index(sym_default_val) if sym_default_val in common_symptoms else 0
                    symptom_name = st.selectbox("Select Symptom *", common_symptoms, index=sym_index)

                # Step 2: Severity Slider (1 to 10)
                st.markdown("""
                    <div style="margin-top: 0.55rem; margin-bottom: 0.2rem;">
                        <span class="form-step-badge">Step 2 of 3 &bull; Severity and duration</span>
                        <div style="font-size: 0.90rem; font-weight: 600; color: var(--text-primary); margin-top: 2px;">Step 2: How intense is it right now?</div>
                    </div>
                """, unsafe_allow_html=True)
                default_sev = edit_entry.severity if edit_entry else 5
                severity = st.slider(
                    "Severity Rating (1 to 10) *",
                    min_value=1,
                    max_value=10,
                    value=int(default_sev)
                )

                # Accessible Severity Text Pill
                if severity <= 3:
                    st.markdown("<span class='severity-pill-mild'>Mild (1–3): Noticeable but routines manageable</span>", unsafe_allow_html=True)
                elif severity <= 6:
                    st.markdown("<span class='severity-pill-moderate'>Moderate (4–6): Notable discomfort, interferes with some activities</span>", unsafe_allow_html=True)
                elif severity <= 8:
                    st.markdown("<span class='severity-pill-severe'>Severe (7–8): Significantly limits daily functioning</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span class='severity-pill-severe'>Debilitating (9–10): Requires immediate rest or medical evaluation</span>", unsafe_allow_html=True)

                # Step 3: Date
                st.markdown("""
                    <div style="margin-top: 0.55rem; margin-bottom: 0.2rem;">
                        <span class="form-step-badge">Step 3 of 3 &bull; Date & timing</span>
                        <div style="font-size: 0.90rem; font-weight: 600; color: var(--text-primary); margin-top: 2px;">Step 3: When did it start & duration?</div>
                    </div>
                """, unsafe_allow_html=True)
                default_date = datetime.strptime(edit_entry.onset_date, "%Y-%m-%d").date() if edit_entry else date.today()
                onset_date = st.date_input("Onset Date *", value=default_date, max_value=date.today() + timedelta(days=1))

                # Optional Expandable Details
                st.markdown("""
                    <div style="margin-top: 0.55rem; margin-bottom: 0.2rem;">
                        <span class="form-step-badge" style="background: var(--muted-lavender); color: #5B4870;">Step 3 of 3 &bull; Additional details</span>
                        <div style="font-size: 0.90rem; font-weight: 600; color: var(--text-primary); margin-top: 2px;">Step 4: Contextual Details</div>
                    </div>
                """, unsafe_allow_html=True)
                with st.expander("➕ Add more details (Duration, Impact, Sleep, Stress, Cycle, Notes)", expanded=is_editing):
                    default_dur = edit_entry.duration_hours if edit_entry and edit_entry.duration_hours is not None else 0.0
                    duration_hours = st.number_input("Duration (hours, optional)", min_value=0.0, max_value=720.0, value=float(default_dur), step=0.5)

                    statuses = ["Ongoing", "Resolved", "Intermittent"]
                    stat_idx = statuses.index(edit_entry.status) if edit_entry and edit_entry.status in statuses else 0
                    status = st.selectbox("Status", statuses, index=stat_idx)

                    onset_time = st.text_input("Time of Onset (Optional)", value=edit_entry.onset_time or "" if edit_entry else "", placeholder="e.g. 14:30")

                    impact_idx = DAILY_IMPACT_LEVELS.index(edit_entry.impact) if edit_entry and edit_entry.impact in DAILY_IMPACT_LEVELS else 0
                    daily_impact = st.selectbox("Impact on Daily Activities", DAILY_IMPACT_LEVELS, index=impact_idx)

                    ctx = edit_entry.context if edit_entry else {}
                    slp_idx = SLEEP_QUALITIES.index(ctx["sleep"]) if ctx.get("sleep") in SLEEP_QUALITIES else 0
                    strss_idx = STRESS_LEVELS.index(ctx["stress"]) if ctx.get("stress") in STRESS_LEVELS else 1
                    enrg_idx = ENERGY_LEVELS.index(ctx["energy"]) if ctx.get("energy") in ENERGY_LEVELS else 1

                    sleep_quality = st.selectbox("Recent Sleep Quality", SLEEP_QUALITIES, index=slp_idx)
                    stress_level = st.selectbox("Recent Stress Level", STRESS_LEVELS, index=strss_idx)
                    energy_level = st.selectbox("Energy Level", ENERGY_LEVELS, index=enrg_idx)

                    cycle_phase = "Not tracking / NA"
                    if track_menstrual:
                        cyc_idx = CYCLE_PHASES.index(ctx["cycle_phase"]) if ctx.get("cycle_phase") in CYCLE_PHASES else 0
                        cycle_phase = st.selectbox("Menstrual Cycle Phase (Optional)", CYCLE_PHASES, index=cyc_idx)

                    notes = st.text_area(
                        "Personal Notes / Observations (Optional)",
                        value=edit_entry.notes if edit_entry else "",
                        placeholder="Describe specific triggers, medications taken, or relief factors.",
                        max_chars=1000
                    )

                # Actions
                submit_label = "💾 Update Symptom Entry" if is_editing else "💾 Save Symptom Entry"
                col_act1, col_act2 = st.columns([3, 2])
                with col_act1:
                    submitted = st.form_submit_button(submit_label, type="primary", use_container_width=True)
                with col_act2:
                    canceled = st.form_submit_button("Cancel", use_container_width=True)

                if canceled:
                    navigate_to("Home Dashboard")

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
                            st.session_state["editing_entry_id"] = None
                            st.session_state["last_saved_symptom"] = {
                                "symptom": symptom_name,
                                "category": selected_category,
                                "severity": severity,
                                "onset_date": str(onset_date)
                            }
                            st.success(f"Updated '{symptom_name}'!")
                            st.rerun()
                        else:
                            st.error(f"Error updating entry: {err}")
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
                            st.session_state["last_saved_symptom"] = {
                                "symptom": symptom_name,
                                "category": selected_category,
                                "severity": severity,
                                "onset_date": str(onset_date)
                            }
                            st.success(f"Saved '{symptom_name}'!")
                            st.rerun()
                        else:
                            st.error(f"Error saving entry: {err}")

        # Tab 2: History & Records
        with tab_history:
            st.markdown("##### Filter History")
            filter_cat = st.selectbox("Category", ["All Categories"] + list(SYMPTOM_TAXONOMY.keys()))
            filter_stat = st.selectbox("Status", ["All", "Ongoing", "Resolved", "Intermittent"])

            history_records = SymptomTrackerService.get_history(
                profile_id=active_profile.id,
                category=filter_cat,
                status=filter_stat
            )

            st.caption(f"Showing **{len(history_records)}** records.")

            if not history_records:
                st.info("No records match the selected filter.")
            else:
                for entry in history_records:
                    with st.expander(f"📅 {entry.onset_date} — {entry.symptom} ({entry.severity}/10)", expanded=False):
                        st.write(f"**Category:** {entry.category} &bull; **Status:** {entry.status}")
                        st.write(f"**Severity:** {entry.severity}/10 &bull; **Duration:** {entry.duration_hours or 'N/A'} hrs")
                        if entry.notes:
                            st.write(f"**Notes:** {entry.notes}")

                        c_edit, c_del = st.columns(2)
                        with c_edit:
                            if st.button("✏️ Edit Entry", key=f"edit_btn_{entry.id}", use_container_width=True):
                                st.session_state["editing_entry_id"] = entry.id
                                st.rerun()
                        with c_del:
                            if st.button("🗑️ Delete", key=f"del_btn_{entry.id}", use_container_width=True):
                                SymptomTrackerService.remove_symptom(entry.id, active_profile.id)
                                st.success("Entry deleted.")
                                st.rerun()


    # ==========================================
    # SCREEN 3: HEALTH INSIGHTS (Patterns & Analytics)
    # ==========================================
    elif st.session_state["navigation"] == "Health Insights":
        st.markdown("""
            <div class="page-title-block">
                <div class="page-title">📊 Health Insights</div>
                <div class="page-subtitle">Explainable patterns derived deterministically from your logs.</div>
            </div>
        """, unsafe_allow_html=True)

        render_my_health_subnav("Health Insights")

        all_entries = SymptomTrackerService.get_history(active_profile.id)
        engine = InsightsEngine(all_entries)
        metrics = engine.calculate_summary_metrics()

        # KPI Summary Grid (2x2 for mobile layout)
        kpi_r1_c1, kpi_r1_c2 = st.columns(2)
        with kpi_r1_c1:
            st.metric("Total Recorded Entries", metrics["total_entries"])
        with kpi_r1_c2:
            st.metric("Distinct Days Logged", metrics["distinct_days"])

        kpi_r2_c1, kpi_r2_c2 = st.columns(2)
        with kpi_r2_c1:
            st.metric("Average Severity", f"{metrics['avg_severity']}/10")
        with kpi_r2_c2:
            st.metric("Primary Symptom", f"{metrics['top_symptom']}")

        # Explainable Observation Statements
        st.markdown('<div class="section-header">💡 Explainable Observation Statements</div>', unsafe_allow_html=True)
        insights_list = engine.generate_explainable_insights()
        for item in insights_list:
            st.markdown(f"""
                <div class="clean-card" style="border-left: 3.5px solid var(--primary-rose); margin-bottom: 0.65rem;">
                    <div class="clean-card-title">{item['title']}</div>
                    <div class="clean-card-subtext">{item['observation']}</div>
                </div>
            """, unsafe_allow_html=True)

        # One Chart at a Time with Clear Explanations
        st.markdown('<div class="section-header">📈 Interactive Charts & Distributions</div>', unsafe_allow_html=True)
        chart_tab1, chart_tab2, chart_tab3, chart_tab4, chart_tab5 = st.tabs([
            "Symptom Timeline",
            "Frequency Breakdown",
            "Contextual Comparison",
            "Co-Occurrence Matrix",
            "📅 Monthly Calendar Grid"
        ])

        with chart_tab1:
            st.caption("Daily severity trajectory over time to track peaks and relief intervals.")
            timeline_fig = engine.plot_severity_timeline()
            if timeline_fig:
                st.plotly_chart(timeline_fig, use_container_width=True)
            else:
                st.info("Log at least one symptom to display the timeline.")

        with chart_tab2:
            st.caption("Total frequency counts for all reported symptoms across your history.")
            freq_fig = engine.plot_symptom_frequency()
            if freq_fig:
                st.plotly_chart(freq_fig, use_container_width=True)
            else:
                st.info("Log symptoms to view the frequency distribution.")

        with chart_tab3:
            st.caption("Compares symptom severity across restful vs. disrupted sleep quality.")
            context_fig = engine.plot_context_comparison()
            if context_fig:
                st.plotly_chart(context_fig, use_container_width=True)
            else:
                st.info("Log symptoms with Sleep observations to view contextual comparisons.")

        with chart_tab4:
            st.caption("Shows which symptoms tend to occur on the same calendar days.")
            heatmap_fig = engine.plot_cooccurrence_heatmap()
            if heatmap_fig:
                st.plotly_chart(heatmap_fig, use_container_width=True)
            else:
                st.info("Log multiple symptoms on shared dates to view co-occurrence.")

        with chart_tab5:
            st.caption("Monthly calendar density view of symptom frequency and intensity.")
            cal_fig = engine.plot_calendar_symptom_heatmap()
            if cal_fig:
                st.plotly_chart(cal_fig, use_container_width=True)
            else:
                st.info("Log symptoms across one or more days to generate calendar density.")

        # Doctor Consultation Prep Kit
        st.markdown('<div class="section-header">📋 Doctor Consultation Prep Kit</div>', unsafe_allow_html=True)
        goal_selection = st.radio(
            "Primary Consultation Objective:",
            ["Diagnostic Evaluation", "Medication & Treatment Review", "Transitional Care (Perimenopause / Cycle Changes)"],
            horizontal=True
        )
        agenda = engine.generate_doctor_talking_points(goal_selection)

        st.markdown(f"""
            <div class="clean-card" style="border-left: 4px solid var(--primary-rose);">
                <div class="clean-card-title">🎯 Agenda: {agenda['goal']}</div>
                <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
                    <b>Baseline:</b> {agenda['data_summary']}
                </div>
                <div style="background: var(--bg-canvas); padding: 0.75rem 0.9rem; border-radius: 10px; margin-bottom: 0.6rem;">
                    <b style="color: var(--primary-rose); font-size: 0.88rem;">30-Second Patient Opening Summary:</b>
                    <p style="font-style: italic; color: var(--text-primary); margin: 0.2rem 0; font-size: 0.9rem;">"{agenda['opening_statement']}"</p>
                </div>
                <b style="font-size: 0.88rem;">Key Discussion Questions:</b>
                <ul style="font-size: 0.88rem; margin-top: 0.25rem; padding-left: 1.2rem;">
                    {''.join([f"<li>{q}</li>" for q in agenda['suggested_questions']])}
                </ul>
            </div>
        """, unsafe_allow_html=True)


    # ==========================================
    # SCREEN 4: MEDICATION & TREATMENTS
    # ==========================================
    elif st.session_state["navigation"] == "Medication & Treatments":
        st.markdown("""
            <div class="page-title-block">
                <div class="page-title">💊 Medication & Health Intervention Tracker</div>
                <div class="page-subtitle">Track prescribed medications, supplements, and supportive therapies.</div>
            </div>
        """, unsafe_allow_html=True)

        render_my_health_subnav("Medication & Treatments")

        tab_med_add, tab_med_list = st.tabs(["➕ Add Medication", "📋 Current Regimen"])

        with tab_med_add:
            with st.form("add_medication_form", clear_on_submit=True):
                med_name = st.text_input("Medication / Treatment Name *", placeholder="e.g. Magnesium Glycinate, Sumatriptan")
                med_cat = st.selectbox("Category *", ["Prescription", "OTC / Supplement", "Lifestyle / Physical Therapy"])
                med_dosage = st.text_input("Dosage / Strength", placeholder="e.g. 400 mg, 1 tablet")
                med_freq = st.selectbox("Frequency", [
                    "Once daily at bedtime", "Once daily in morning", "As needed at symptom onset", "Twice daily with meals", "Other"
                ])
                med_start = st.date_input("Date Started", value=date.today())
                med_notes = st.text_area("Notes / Instructions", placeholder="e.g. Take with food")
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
                        st.success(f"Added '{med_name.strip()}' to your regimen!")

        with tab_med_list:
            profile_meds = get_medications(active_profile.id)
            if not profile_meds:
                st.info("No medications recorded yet.")
            else:
                for med in profile_meds:
                    st.markdown(f"""
                        <div class="clean-card" style="padding: 0.85rem 1rem; margin-bottom: 0.6rem;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div style="font-weight: 600; font-size: 0.95rem;">{med.name}</div>
                                <span class="badge-selfcare">{med.category}</span>
                            </div>
                            <div style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.2rem;">
                                {med.dosage or 'Standard dose'} &bull; <i>{med.frequency}</i>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"🗑️ Remove {med.name}", key=f"del_med_{med.id}"):
                        delete_medication(med.id, active_profile.id)
                        st.success(f"Removed {med.name}.")
                        st.rerun()


    # ==========================================
    # SCREEN 5: CARE NAVIGATOR (Safety & Guidance)
    # ==========================================
    elif st.session_state["navigation"] == "Care Navigator":
        st.markdown("""
            <div class="page-title-block">
                <div class="page-title">🛡️ Care Guidance & Safety Navigator</div>
                <div class="page-subtitle">Public health triage guidance to help you make informed care choices.</div>
            </div>
        """, unsafe_allow_html=True)

        # Emergency safety notice (prominent, never collapsed)
        st.markdown(f"""
            <div class="disclaimer-box">
                <b>Safety Notice:</b> {CLINICAL_DISCLAIMER}
            </div>
            <div style="display: flex; gap: 0.4rem; flex-wrap: wrap; margin-bottom: 0.9rem;">
                <span class="badge-emergency">🚨 Emergency (Immediate)</span>
                <span class="badge-prompt">⚠️ Prompt Medical (24–48h)</span>
                <span class="badge-routine">🩺 Routine Consultation</span>
                <span class="badge-selfcare">🌸 Self-Care</span>
            </div>
        """, unsafe_allow_html=True)

        with st.form("safety_navigator_form"):
            st.markdown('<div class="section-header" style="margin-top: 0.2rem;">Describe Your Current Concern</div>', unsafe_allow_html=True)
            nav_category = st.selectbox("Category", list(SYMPTOM_TAXONOMY.keys()))
            suggested = SYMPTOM_TAXONOMY.get(nav_category, [])
            nav_symptom = st.selectbox("Symptom", suggested)
            nav_severity = st.slider("Severity Rating (1 to 10)", min_value=1, max_value=10, value=6)
            nav_duration = st.number_input("Duration (hours)", min_value=0.0, max_value=720.0, value=12.0, step=1.0)

            st.markdown('<div class="section-header">Clinical Warning Flags</div>', unsafe_allow_html=True)
            warning_flags = SafetyNavigator.get_supported_emergency_warning_signs()
            checked_flags = []
            for wf in warning_flags:
                if st.checkbox(f"{wf['label']} ({wf['level']} Warning)", key=f"nav_wf_{wf['id']}"):
                    checked_flags.append(wf["label"])

            nav_notes = st.text_input("Additional Observations / Notes", placeholder="e.g. onset was sudden")
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

            if assessment.priority == PRIORITY_EMERGENCY:
                st.markdown(f"""
                    <div class="disclaimer-urgent">
                        <span class="badge-emergency">EMERGENCY EVALUATION NEEDED</span>
                        <h3 style="color: #7D232F; margin: 0.4rem 0;">{assessment.headline}</h3>
                        <p><b>Immediate Safety Guidance:</b></p>
                        <ul style="padding-left: 1.2rem; margin: 0.3rem 0;">
                            {''.join([f"<li><b>{act}</b></li>" for act in assessment.recommended_actions])}
                        </ul>
                        <p style="margin-top: 0.6rem; font-weight: 700; color: #B94957;">{assessment.emergency_contact}</p>
                    </div>
                """, unsafe_allow_html=True)
            elif assessment.priority == PRIORITY_PROMPT:
                st.markdown(f"""
                    <div class="clean-card" style="border-left: 4px solid var(--warning-amber);">
                        <span class="badge-prompt">PROMPT MEDICAL EVALUATION (24–48 Hours)</span>
                        <div class="clean-card-title" style="margin-top: 0.3rem;">{assessment.headline}</div>
                        <ul style="padding-left: 1.2rem; font-size: 0.88rem; margin: 0.3rem 0;">
                            {''.join([f"<li>{act}</li>" for act in assessment.recommended_actions])}
                        </ul>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="clean-card" style="border-left: 4px solid var(--primary-rose);">
                        <span class="badge-routine">ROUTINE CARE & GUIDANCE</span>
                        <div class="clean-card-title" style="margin-top: 0.3rem;">{assessment.headline}</div>
                        <ul style="padding-left: 1.2rem; font-size: 0.88rem; margin: 0.3rem 0;">
                            {''.join([f"<li>{act}</li>" for act in assessment.recommended_actions])}
                        </ul>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown('<div class="section-header">🚨 Emergency SOS Numbers</div>', unsafe_allow_html=True)
        st.markdown("""
            <div class="clean-card">
                <div style="font-size: 0.9rem; line-height: 1.7;">
                    🚑 <b>India & EU:</b> 112 &bull; <b>US:</b> 911 &bull; <b>UK:</b> 999<br/>
                    🌸 <b>Women's Helpline (India):</b> 181 / 1091<br/>
                    🧠 <b>Mental Health Support:</b> US 988 &bull; UK 111 &bull; India 14416
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Emergency Room Preparation Checklist
        st.markdown('<div class="section-header">🏥 Emergency Room (ER) Preparation Checklist</div>', unsafe_allow_html=True)
        st.markdown("""
            <div class="clean-card" style="margin-bottom: 0.8rem;">
                <div style="font-size: 0.86rem; color: var(--text-secondary); line-height: 1.5;">
                    Keep these essentials prepared if seeking urgent or emergency clinical evaluation:
                </div>
                <ul style="font-size: 0.86rem; padding-left: 1.2rem; margin-top: 0.35rem; line-height: 1.6;">
                    <li><b>Identification & Insurance:</b> Government photo ID, health card, or medical insurance policy.</li>
                    <li><b>Current Medication Regimen:</b> Doses of prescription drugs and over-the-counter supplements.</li>
                    <li><b>Clinical Record Summary:</b> Downloaded HERPath PDF report or recent symptom records.</li>
                    <li><b>Timeline & Triggers:</b> Approximate date and time of symptom onset, intensity progression, and any relief factors.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

        # Doctor Appointment Preparation & Questions
        st.markdown('<div class="section-header">🩺 Doctor Consultation Questions</div>', unsafe_allow_html=True)
        st.caption("Evidence-grounded discussion prompts for your next doctor appointment:")
        care_questions = [
            "What potential underlying conditions could account for this pattern of symptoms?",
            "Are there specific diagnostic blood tests, hormonal panels, or pelvic ultrasound imaging indicated?",
            "How might my menstrual cycle phases or hormonal fluctuations be interacting with these symptoms?",
            "What red-flag signs should prompt me to seek immediate acute emergency evaluation?",
            "Are there evidence-based lifestyle, nutrition, or physical therapy interventions to support recovery?"
        ]
        for q in care_questions:
            st.markdown(f"""
                <div style="background: var(--surface); border: 1px solid var(--border-subtle); border-radius: 8px; padding: 0.5rem 0.8rem; margin-bottom: 0.4rem; font-size: 0.84rem;">
                    💬 <i>"{q}"</i>
                </div>
            """, unsafe_allow_html=True)

        # Copyable Clinician Summary
        st.markdown('<div class="section-header">📋 Copyable Clinician Summary</div>', unsafe_allow_html=True)
        st.caption("One-tap copyable text block for telemedicine portals or doctor messages:")
        recent_entries = SymptomTrackerService.get_history(active_profile.id)[:5]
        summary_lines = [
            f"HERPath Patient Summary — {active_profile.display_name}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "--- Recent Observations ---"
        ]
        if recent_entries:
            for re in recent_entries:
                summary_lines.append(f"• {re.onset_date}: {re.symptom} ({re.category}) | Severity: {re.severity}/10 | Status: {re.status} | Notes: {re.notes or 'None'}")
        else:
            summary_lines.append("• No recent symptom entries logged.")

        user_meds = get_medications(active_profile.id)
        summary_lines.append("--- Current Medications ---")
        if user_meds:
            for um in user_meds:
                summary_lines.append(f"• {um.name} ({um.category}): {um.dosage} | Frequency: {um.frequency}")
        else:
            summary_lines.append("• No active medications recorded.")

        clinician_text_block = "\n".join(summary_lines)
        st.text_area("Patient Health Summary", value=clinician_text_block, height=130, help="Select all and copy for your healthcare provider.")


    # ==========================================
    # SCREEN 6: WOMEN'S HEALTH LIBRARY (Learn)
    # ==========================================
    elif st.session_state["navigation"] == "Women's Health Library":
        st.markdown("""
            <div class="page-title-block">
                <div class="page-title">📚 Women's Health Library</div>
                <div class="page-subtitle">Evidence-based educational resources from WHO, NHS, CDC, and ACOG.</div>
            </div>
        """, unsafe_allow_html=True)

        render_learn_subnav("Women's Health Library")

        search_query = st.text_input("🔍 Search library topics or symptoms", placeholder="e.g. PCOS, migraine, iron...")
        categories = health_library.get_categories()
        chosen_cat = st.selectbox("Category", categories)

        filtered_articles = health_library.search_resources(query=search_query, category=chosen_cat)
        st.caption(f"Showing **{len(filtered_articles)}** resources.")

        for art in filtered_articles:
            st.markdown(f"""
                <div class="clean-card" style="margin-bottom: 0.75rem;">
                    <div style="font-size: 0.75rem; font-weight: 700; color: var(--primary-rose); text-transform: uppercase;">
                        {art['source_org']} &bull; {art['category']}
                    </div>
                    <div class="clean-card-title">{art['title']}</div>
                    <div class="clean-card-subtext">{art['summary']}</div>
                    <div style="margin-top: 0.5rem; font-size: 0.84rem;">
                        <a href="{art['source_url']}" target="_blank" style="color: var(--primary-rose); font-weight: 600; text-decoration: none;">
                            Read verified article &rarr;
                        </a>
                    </div>
                </div>
            """, unsafe_allow_html=True)


    # ==========================================
    # SCREEN 7: MY HEALTH REPORT (Clinician PDF)
    # ==========================================
    elif st.session_state["navigation"] == "My Health Report":
        st.markdown("""
            <div class="page-title-block">
                <div class="page-title">📄 Clinician-Ready Health Report</div>
                <div class="page-subtitle">Export a structured PDF summary of your observations for your doctor.</div>
            </div>
        """, unsafe_allow_html=True)

        render_my_health_subnav("My Health Report")

        rep_start = st.date_input("Start Date", value=date.today() - timedelta(days=30))
        rep_end = st.date_input("End Date", value=date.today() + timedelta(days=1))

        report_entries = SymptomTrackerService.get_history(
            profile_id=active_profile.id,
            start_date=str(rep_start),
            end_date=str(rep_end)
        )

        rep_engine = InsightsEngine(report_entries)
        rep_metrics = rep_engine.calculate_summary_metrics()

        rep_r1_c1, rep_r1_c2 = st.columns(2)
        with rep_r1_c1:
            st.metric("Entries in Period", rep_metrics["total_entries"])
        with rep_r1_c2:
            st.metric("Distinct Dates", rep_metrics["distinct_days"])

        rep_r2_c1, rep_r2_c2 = st.columns(2)
        with rep_r2_c1:
            st.metric("Avg Severity", f"{rep_metrics['avg_severity']}/10")
        with rep_r2_c2:
            st.metric("Top Reported Symptom", rep_metrics["top_symptom"])

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
                label="📥 Download Clinician Health Report",
                data=pdf_bytes,
                file_name=file_name,
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error compiling PDF: {str(e)}")


    # ==========================================
    # SCREEN 8: ASK HERPATH ASSISTANT
    # ==========================================
    elif st.session_state["navigation"] == "Ask HERPath":
        st.markdown("""
            <div class="page-title-block">
                <div class="page-title">🤖 Ask HERPath — Health Literacy Assistant</div>
                <div class="page-subtitle">Curated educational findings grounded in verified health resources.</div>
            </div>
            <div class='disclaimer-box'><b>Boundaries:</b> Strictly non-diagnostic health literacy assistant grounded in curated medical resources.</div>
        """, unsafe_allow_html=True)

        render_learn_subnav("Ask HERPath")

        user_query = st.text_input("Enter your health question:", placeholder="e.g. iron deficiency fatigue, PCOS symptoms")

        if user_query:
            emergency_assessment = SafetyNavigator.evaluate(
                symptom=user_query,
                category="Systemic & Energy",
                severity=5,
                notes=user_query
            )

            if emergency_assessment.priority == PRIORITY_EMERGENCY:
                st.markdown(f"""
                    <div class="disclaimer-urgent">
                        <span class="badge-emergency">SAFETY ALERT</span>
                        <div style="font-weight: 700; color: #7D232F;">{emergency_assessment.headline}</div>
                        <p style="font-size: 0.88rem; margin: 0.2rem 0;">{emergency_assessment.emergency_contact}</p>
                    </div>
                """, unsafe_allow_html=True)

            matches = health_library.search_resources(query=user_query)
            if matches:
                st.markdown(f"#### Grounded Findings ({len(matches)} Relevant Guides)")
                for match in matches[:3]:
                    st.markdown(f"""
                        <div class="clean-card" style="border-left: 3.5px solid var(--primary-rose); margin-bottom: 0.65rem;">
                            <div style="font-size: 0.74rem; font-weight: 700; color: var(--primary-rose); text-transform: uppercase;">
                                {match['source_org']} &bull; {match['category']}
                            </div>
                            <div class="clean-card-title">{match['title']}</div>
                            <div class="clean-card-subtext">{match['summary']}</div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No verified guides matched your query.")


    # ==========================================
    # SCREEN 9: PRIVACY AND SETTINGS
    # ==========================================
    elif st.session_state["navigation"] == "Privacy and Settings":
        st.markdown("""
            <div class="page-title-block">
                <div class="page-title">⚙️ Settings & Profile Management</div>
                <div class="page-subtitle">100% on-device SQLite storage &bull; Zero telemetry</div>
            </div>
        """, unsafe_allow_html=True)

        # 1. Active Profile Section
        st.markdown('<div class="section-header">👤 Active Profile</div>', unsafe_allow_html=True)
        all_profiles = list_profiles()
        p_map = {p.id: p for p in all_profiles}
        current_pid = st.session_state.get("current_profile_id", all_profiles[0].id)
        if current_pid not in p_map:
            current_pid = all_profiles[0].id
            st.session_state["current_profile_id"] = current_pid

        p_keys = [p.id for p in all_profiles]
        selected_pid = st.selectbox(
            "Active Profile",
            p_keys,
            index=p_keys.index(current_pid),
            format_func=lambda pid: p_map[pid].display_name,
            key="settings_active_prof_selector"
        )
        if selected_pid != st.session_state["current_profile_id"]:
            st.session_state["current_profile_id"] = selected_pid
            st.session_state["editing_entry_id"] = None
            st.rerun()

        with st.expander("➕ Create New Profile", expanded=False):
            with st.form("settings_create_profile_form"):
                new_pid = st.text_input("Profile ID (unique, e.g. maya_pcos)").strip().lower()
                new_pname = st.text_input("Display Name (e.g. Maya - Wellness)").strip()
                if st.form_submit_button("Create Profile", type="primary"):
                    if new_pid and new_pname:
                        create_profile(new_pid, new_pname)
                        st.session_state["current_profile_id"] = new_pid
                        st.success(f"Profile '{new_pname}' created!")
                        st.rerun()
                    else:
                        st.error("Please provide both an ID and Display Name.")

        # 2. Profile Preferences Section
        st.markdown('<div class="section-header">⚙️ Profile Preferences</div>', unsafe_allow_html=True)
        with st.form("profile_customization_form"):
            display_name_val = st.text_input("Display Name / Pseudonym", value=active_profile.display_name)
            track_menstrual_toggle = st.checkbox("Track Menstrual Context", value=active_profile.preferences.get("track_menstrual", True))
            if st.form_submit_button("Save Profile Settings", type="primary"):
                new_prefs = active_profile.preferences.copy()
                new_prefs["track_menstrual"] = track_menstrual_toggle
                update_profile_preferences(active_profile.id, new_prefs)
                st.success("Updated profile settings!")
                st.rerun()

        # 3. Privacy & Storage Architecture
        st.markdown('<div class="section-header">🔒 Privacy & Data Protection Architecture</div>', unsafe_allow_html=True)
        st.markdown("""
            <div class="clean-card" style="margin-bottom: 0.8rem;">
                <div style="font-weight: 600; font-size: 0.90rem; color: #34272E;">Where your records are stored</div>
                <div style="font-size: 0.82rem; color: #81717A; margin-top: 4px; line-height: 1.45;">
                    100% Local SQLite Storage. All symptom records, notes, and profiles remain strictly on this device in an on-device database file. Zero data is transmitted to cloud servers.
                </div>
                <div style="font-weight: 600; font-size: 0.90rem; color: #34272E; margin-top: 8px;">Data ownership & rights</div>
                <div style="font-size: 0.82rem; color: #81717A; margin-top: 4px; line-height: 1.45;">
                    You retain complete control of your healthcare records. Download complete JSON backups, export CSV logs, or permanently delete records at any time.
                </div>
            </div>
        """, unsafe_allow_html=True)

        # 4. Data Portability Section
        st.markdown('<div class="section-header">📦 Data Portability</div>', unsafe_allow_html=True)
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            json_backup_str = export_profile_data_json(active_profile.id)
            st.download_button(
                label="📥 Download JSON Backup",
                data=json_backup_str,
                file_name=f"HERPath_Backup_{active_profile.id}.json",
                mime="application/json",
                use_container_width=True
            )
        with col_p2:
            csv_history_str = export_symptoms_csv(active_profile.id)
            st.download_button(
                label="📊 Download CSV Records",
                data=csv_history_str,
                file_name=f"HERPath_Symptoms_{active_profile.id}.csv",
                mime="text/csv",
                use_container_width=True
            )

        # Restore from JSON backup
        with st.expander("📥 Restore from JSON Backup", expanded=False):
            uploaded_backup = st.file_uploader("Upload HERPath Backup (.json)", type=["json"], key="backup_restore_uploader")
            if uploaded_backup is not None:
                if st.button("Restore Records into Active Profile", type="primary", key="btn_execute_restore"):
                    try:
                        content = uploaded_backup.read().decode("utf-8")
                        imported_s, imported_m = import_profile_data_json(active_profile.id, content)
                        st.success(f"Successfully restored {imported_s} symptoms and {imported_m} medications into '{active_profile.display_name}'!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error restoring backup: {str(e)}")

        # 5. Danger Zone / Data Deletion
        st.markdown('<div class="section-header">⚠️ Danger Zone & Record Deletion</div>', unsafe_allow_html=True)
        with st.expander("🗑️ Delete Active Profile & Data", expanded=False):
            st.warning(f"Permanently delete profile **'{active_profile.display_name}'** ({active_profile.id}) and all associated symptom and medication entries?")
            confirm_del = st.checkbox(f"Yes, permanently delete '{active_profile.display_name}' and all associated records", key="confirm_delete_profile_chk")
            if st.button("Permanently Delete Profile", key="btn_confirm_delete_profile", disabled=not confirm_del):
                if len(all_profiles) <= 1:
                    st.error("Cannot delete the only existing profile. Create another profile first.")
                else:
                    delete_profile(active_profile.id)
                    rem_profiles = list_profiles()
                    st.session_state["current_profile_id"] = rem_profiles[0].id
                    st.success(f"Profile '{active_profile.display_name}' permanently deleted.")
                    st.rerun()

    # Dedicated scroll clearance spacer at bottom of content
    st.markdown('<div class="scroll-bottom-spacer" style="height: 36px; min-height: 36px;"></div>', unsafe_allow_html=True)


# ==========================================
# Fixed iOS Bottom Tab Bar (4 Destinations)
# ==========================================
with st.container(key="mobile_bottom_bar"):
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
    curr_nav = st.session_state["navigation"]

    with nav_col1:
        is_active = curr_nav == "Home Dashboard"
        if st.button("🌸 Home", key="bnav_home", use_container_width=True, type="primary" if is_active else "secondary"):
            navigate_to("Home Dashboard")

    with nav_col2:
        is_active = curr_nav in ["Symptom Journal", "Medication & Treatments", "Health Insights", "My Health Report"]
        if st.button("💗 My Health", key="bnav_health", use_container_width=True, type="primary" if is_active else "secondary"):
            navigate_to("Symptom Journal")

    with nav_col3:
        is_active = curr_nav == "Care Navigator"
        if st.button("🛡️ Care", key="bnav_care", use_container_width=True, type="primary" if is_active else "secondary"):
            navigate_to("Care Navigator")

    with nav_col4:
        is_active = curr_nav in ["Women's Health Library", "Ask HERPath"]
        if st.button("📚 Learn", key="bnav_learn", use_container_width=True, type="primary" if is_active else "secondary"):
            navigate_to("Women's Health Library")

    st.markdown('<div class="iphone-home-indicator"></div>', unsafe_allow_html=True)
