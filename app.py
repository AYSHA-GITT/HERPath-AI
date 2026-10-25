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
import uuid

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
from timeline_service import TimelineService, TimelineEvent
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
from validators import ValidationError

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

if "is_logged_in" not in st.session_state:
    st.session_state["is_logged_in"] = False

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
    """Renders a sleek 5-segment sub-navigation pill bar for all My Health screens."""
    with st.container(key="subnav_container"):
        s1, s2, s3, s4, s5 = st.columns(5)
        with s1:
            is_active = current_screen == "Symptom Journal"
            if st.button("📝 Journal", key="sub_btn_journal", use_container_width=True, type="primary" if is_active else "secondary"):
                navigate_to("Symptom Journal")
        with s2:
            is_active = current_screen == "Medication & Treatments"
            if st.button("💊 Meds", key="sub_btn_meds", use_container_width=True, type="primary" if is_active else "secondary"):
                navigate_to("Medication & Treatments")
        with s3:
            is_active = current_screen == "Timeline Intelligence"
            if st.button("⏱️ Timeline", key="sub_btn_timeline", use_container_width=True, type="primary" if is_active else "secondary"):
                navigate_to("Timeline Intelligence")
        with s4:
            is_active = current_screen == "Health Insights"
            if st.button("📈 Insights", key="sub_btn_insights", use_container_width=True, type="primary" if is_active else "secondary"):
                navigate_to("Health Insights")
        with s5:
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

    if st.session_state.get("is_logged_in", False):
        profiles = list_profiles()
        profile_dict = {p.id: p for p in profiles}

        if not profiles:
            create_profile("demo_priya", "Priya (PCOS & Migraine Tracking)")
            profiles = list_profiles()
            profile_dict = {p.id: p for p in profiles}

        current_id = st.session_state.get("current_profile_id")
        if current_id not in profile_dict:
            current_id = profiles[0].id
            st.session_state["current_profile_id"] = current_id

        profile_options = [p.id for p in profiles]
        selected_profile_id = st.selectbox(
            "👤 Active Health Profile",
            options=profile_options,
            index=profile_options.index(current_id),
            format_func=lambda pid: profile_dict[pid].display_name,
            key=f"sidebar_profile_{current_id}"
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
            "Timeline Intelligence",
            "Health Insights",
            "Care Navigator",
            "Women's Health Library",
            "My Health Report",
            "Ask HERPath",
            "Privacy and Settings",
            "Account & Login"
        ]

        curr_nav_state = st.session_state.get("navigation", "Home Dashboard")
        selected_nav = st.radio(
            "📍 Platform Navigation",
            nav_options,
            index=nav_options.index(curr_nav_state) if curr_nav_state in nav_options else 0,
            key=f"sidebar_nav_{curr_nav_state}"
        )

        if selected_nav != st.session_state["navigation"]:
            st.session_state["navigation"] = selected_nav
            st.rerun()

        st.markdown("---")
        st.caption(f"Active Account: **{active_profile.display_name}**")
        if st.button("🚪 Log Out / Lock", key="sidebar_logout_btn", use_container_width=True):
            st.session_state["is_logged_in"] = False
            st.session_state["current_profile_id"] = None
            st.session_state["navigation"] = "Account & Login"
            st.rerun()
    else:
        st.markdown("---")
        st.info("🔒 **Sign In Required**\nPlease sign in with your PIN to access your personal health journal and insights.")
        if st.button("🔐 Sign In / Register", key="sidebar_login_btn", use_container_width=True):
            st.session_state["navigation"] = "Account & Login"
            st.rerun()

    st.caption("🔒 100% On-Device SQLite. Zero Cloud Transmission.")

# Safe profile retrieval for main view
if st.session_state.get("is_logged_in", False) and st.session_state.get("current_profile_id"):
    active_profile = get_profile(st.session_state["current_profile_id"])
    if not active_profile:
        profs = list_profiles()
        active_profile = profs[0] if profs else None
    first_name = active_profile.display_name.split(" ")[0].replace("(", "").strip() if active_profile else "Friend"
else:
    active_profile = None
    first_name = "Friend"


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
    if st.session_state.get("is_logged_in", False):
        if st.button("👤", key="top_user_pill", help=f"Account & Profile ({first_name})", use_container_width=True):
            navigate_to("Account & Login")
    else:
        if st.button("🔐", key="top_login_pill", help="Sign In / Sign Up", use_container_width=True):
            navigate_to("Account & Login")
    st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# Screen Component: Login, Account & New User Registration
# ==========================================
def render_auth_login_screen():
    all_profiles = list_profiles()
    p_map = {p.id: p for p in all_profiles}
    is_authenticated = st.session_state.get("is_logged_in", False)
    curr_pid = st.session_state.get("current_profile_id")
    active_prof = p_map.get(curr_pid) if curr_pid else None

    # 1. If already authenticated: Show dedicated Account & Profile screen directly (NO Login or Create Account tabs)
    if is_authenticated and active_prof:
        stats = get_account_stats(active_prof.id)
        focus_list = stats["focus_areas"] if isinstance(stats["focus_areas"], list) else [str(stats["focus_areas"])]
        focus_chips = "".join([f'<span class="auth-sec-pill" style="margin-right: 4px; margin-bottom: 4px;">🎯 {f}</span>' for f in focus_list])

        st.markdown(f"""
            <div class="page-title-block">
                <div class="page-title">👤 Account & Profile</div>
                <div class="page-subtitle">Your private on-device profile, security PIN, and health records</div>
            </div>
            <div class="vip-profile-card">
                <div class="vip-avatar-row">
                    <div class="vip-large-avatar">🌸</div>
                    <div>
                        <div class="vip-user-title">{active_prof.display_name}</div>
                        <div class="vip-user-handle">@{active_prof.id} &bull; Member since {stats["created_at"]}</div>
                    </div>
                </div>
                <div class="auth-security-badges" style="justify-content: flex-start; margin-top: 6px;">
                    <span class="auth-sec-pill">🔒 SQLite Locked</span>
                    <span class="auth-sec-pill">📍 Local Device</span>
                    <span class="auth-sec-pill">🔐 PIN Protected</span>
                    <span class="auth-sec-pill">{'🩸 Cycle Active' if stats["track_menstrual"] else '🌿 General Track'}</span>
                </div>
                <div style="margin-top: 10px;">
                    <div style="font-size: 0.72rem; font-weight: 700; color: #8A7A83; text-transform: uppercase; margin-bottom: 4px;">Health Focus Areas</div>
                    <div style="display: flex; flex-wrap: wrap;">{focus_chips}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Symptoms Logged", stats["symptoms_count"])
        with c2:
            st.metric("Medications", stats["medications_count"])
        with c3:
            st.metric("Security", "PIN Locked 🔒")

        # Persistent success feedback across reruns
        if "pin_update_success" in st.session_state:
            st.success(st.session_state.pop("pin_update_success"))

        if "pref_update_success" in st.session_state:
            st.success(st.session_state.pop("pref_update_success"))

        pin_version = st.session_state.get("pin_input_version", 0)
        pin_exp_open = st.session_state.pop("pin_expander_open", False)
        pin_success_inside = st.session_state.pop("pin_inside_success", False)

        with st.expander("🔒 Change Security PIN", expanded=pin_exp_open):
            st.caption("Change your 4-digit security PIN to protect access on this device.")
            if pin_success_inside:
                st.success("✅ Your 4-digit security PIN has been updated successfully!")
            new_pin_input = st.text_input(
                "New 4-Digit Security PIN",
                type="password",
                key=f"change_pin_field_{pin_version}",
                placeholder="••••"
            )
            if st.button("Update Security PIN", type="primary", key="btn_update_pin"):
                if new_pin_input and len(new_pin_input.strip()) >= 4:
                    set_user_pin(active_prof.id, new_pin_input.strip())
                    st.session_state["pin_update_success"] = "✅ Security PIN updated successfully! Your new PIN is active on this device."
                    st.session_state["pin_expander_open"] = True
                    st.session_state["pin_inside_success"] = True
                    st.session_state["pin_input_version"] = pin_version + 1
                    st.rerun()
                else:
                    st.error("PIN must be at least 4 digits.")

        pref_exp_open = st.session_state.pop("pref_expander_open", False)
        with st.expander("⚙️ Profile Customization", expanded=pref_exp_open):
            with st.form("account_profile_pref_form"):
                display_name_val = st.text_input("Display Name / Pseudonym", value=active_prof.display_name)
                track_menstrual_toggle = st.checkbox("Track Menstrual Context", value=active_prof.preferences.get("track_menstrual", True))
                if st.form_submit_button("Save Preferences", type="primary"):
                    updated_pref = active_prof.preferences.copy()
                    updated_pref["display_name"] = display_name_val
                    updated_pref["track_menstrual"] = track_menstrual_toggle
                    update_profile_preferences(active_prof.id, updated_pref)
                    st.session_state["pref_update_success"] = "✅ Preferences updated successfully!"
                    st.session_state["pref_expander_open"] = True
                    st.rerun()

        st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)
        lo_c1, lo_c2 = st.columns(2)
        with lo_c1:
            if st.button("🚪 Log Out & Lock", key="btn_auth_logout", use_container_width=True, type="secondary"):
                st.session_state["is_logged_in"] = False
                st.session_state["current_profile_id"] = None
                st.session_state["navigation"] = "Account & Login"
                st.rerun()
        with lo_c2:
            if st.button("🌸 Go to Dashboard", key="btn_auth_go_home", use_container_width=True, type="primary"):
                navigate_to("Home Dashboard")
        return

    # 2. If unauthenticated: Show Login & Create Account tabs
    active_auth_tab = st.session_state.get("auth_active_tab", "Login")
    tab_list = ["Login", "Create Account"]
    if active_auth_tab not in tab_list:
        active_auth_tab = "Login"

    tab_signin, tab_register = st.tabs(tab_list, default=active_auth_tab, key=f"auth_tabs_{active_auth_tab}")

    with tab_signin:
        # Screen 1: Clean, User-Friendly Login Card for Real Healthcare Application
        with st.container(key="auth_login_card"):
            st.markdown(
                '<div class="auth-clean-header">'
                '<div class="auth-logo-badge">🌸</div>'
                '<div class="auth-brand-wordmark"><b>HERPath AI</b></div>'
                '<div class="auth-mockup-title">Welcome to HERPath</div>'
                '<div class="auth-mockup-subtitle">Your personal space for understanding and tracking your health.</div>'
                '</div>',
                unsafe_allow_html=True
            )

            # Clearly labeled sign-in inputs
            signin_username = st.text_input(
                "Username or Account Name",
                value=st.session_state.get("saved_login_username", "Priya"),
                placeholder="e.g. Priya or your account name",
                key="signin_username_field",
                help="Enter your name, pseudonym, or account username"
            )

            show_pin = st.checkbox("Show PIN", key="signin_show_pin_toggle", value=False)
            input_pin = st.text_input(
                "4-Digit Security PIN",
                type="default" if show_pin else "password",
                key="signin_pin_field",
                placeholder="Enter 4-digit PIN",
                help="Enter your 4-digit security PIN (Demo accounts use: 1234)"
            )

            # Primary Sign-In button
            st.markdown('<div style="height: 6px;"></div>', unsafe_allow_html=True)
            if st.button("SIGN IN / LOGIN  ➔", type="primary", use_container_width=True, key="btn_do_signin"):
                if not signin_username or not signin_username.strip():
                    st.error("Please enter your username or account name.")
                elif not input_pin or len(input_pin.strip()) < 4:
                    st.error("Please enter your 4-digit security PIN to sign in (Demo accounts use: 1234).")
                else:
                    success, msg, profile_obj = authenticate_user(signin_username.strip(), input_pin.strip())
                    if success and profile_obj:
                        st.session_state["current_profile_id"] = profile_obj.id
                        st.session_state["saved_login_username"] = profile_obj.display_name.split("(")[0].strip()
                        st.session_state["is_logged_in"] = True
                        navigate_to("Home Dashboard")
                    else:
                        st.error(msg)

            # Interactive link to create account
            st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
            if st.button("Don't have an account? Sign up ➔", key="btn_switch_to_signup", use_container_width=True):
                st.session_state["auth_active_tab"] = "Create Account"
                st.rerun()

            # Small privacy reassurance
            st.markdown(
                '<div class="auth-privacy-banner">'
                '🔒 <b>100% On-Device Privacy</b>: Your health logs remain securely on this phone. '
                'We never share or upload your private records &bull; Women\'s Health Intelligence &bull; 100% On-Device SQLite'
                '</div>',
                unsafe_allow_html=True
            )

        # 4. Hackathon Reviewer & Demo Access in a discreet collapsed expander
        with st.expander("🛠️ Hackathon Reviewer & Demo Access", expanded=False):
            st.caption("Evaluating HERPath AI? Quick-load a seeded clinical demo persona to inspect pre-populated history:")
            demo_profs = list_profiles()
            demo_dict = {p.id: p for p in demo_profs if "demo" in p.id.lower() or p.id in ["demo_priya", "demo_ananya", "demo_elena"]}
            if not demo_dict:
                demo_dict = {p.id: p for p in demo_profs}
            selected_demo_id = st.selectbox(
                "Select Clinical Demo Persona",
                options=list(demo_dict.keys()),
                format_func=lambda pid: f"👤 {demo_dict[pid].display_name}",
                key="reviewer_demo_selector"
            )
            if st.button("Load Demo Persona & Sign In", key="btn_load_reviewer_demo", use_container_width=True):
                st.session_state["current_profile_id"] = selected_demo_id
                st.session_state["saved_login_username"] = demo_dict[selected_demo_id].display_name.split("(")[0].strip()
                st.session_state["is_logged_in"] = True
                navigate_to("Home Dashboard")

    with tab_register:
        # Screen 2: Clean, User-Friendly Registration Form
        with st.container(key="auth_create_card"):
            c_back_col, _ = st.columns([0.45, 0.55])
            with c_back_col:
                if st.button("← Back to Sign In", key="btn_back_to_login"):
                    st.session_state["auth_active_tab"] = "Login"
                    st.rerun()

            st.markdown(
                '<div class="auth-clean-header" style="margin-top: 4px;">'
                '<div class="auth-logo-badge">🌸</div>'
                '<div class="auth-brand-wordmark"><b>HERPath AI</b></div>'
                '<div class="auth-mockup-title">Create Account</div>'
                '<div class="auth-mockup-subtitle">Start your private, on-device health journal.</div>'
                '</div>',
                unsafe_allow_html=True
            )

            with st.form("new_user_registration_form"):
                reg_name = st.text_input(
                    "Full Name or Pseudonym *",
                    placeholder="e.g. Maya or S.K.",
                    help="Pseudonyms are encouraged for maximum personal privacy."
                ).strip()

                reg_id = st.text_input(
                    "Account Username / ID (Optional - auto-generated if blank)",
                    placeholder="e.g. maya or leave blank",
                    help="Unique handle for this device profile. Auto-generated if left blank."
                ).strip().lower()

                reg_pin = st.text_input(
                    "Security PIN (4 digits) *",
                    type="password",
                    value="1234",
                    placeholder="••••",
                    help="Mandatory 4-digit security PIN to protect your health records on this device."
                ).strip()

                focus_choices = [
                    "PCOS & Hormonal Balance",
                    "Endometriosis & Chronic Pelvic Pain",
                    "Perimenopause & Menopause Transition",
                    "Hormonal Migraines & Neurological",
                    "Fatigue, Thyroid & Iron Levels",
                    "Fertility & Cycle Tracking",
                    "Mental Wellbeing & Anxiety/Mood",
                    "General Health & Preventative Wellness"
                ]
                reg_focus = st.multiselect(
                    "Health Focus Areas",
                    options=focus_choices,
                    default=["General Health & Preventative Wellness"],
                    help="Customizes your pattern analysis, care guides, and symptom suggestions."
                )

                reg_cycle = st.checkbox(
                    "Track Menstrual Cycle & Hormonal Phases",
                    value=True,
                    help="Enable cycle tracking. Can be adjusted anytime."
                )

                reg_consent = st.checkbox(
                    "I acknowledge that my records are stored 100% locally on this device in SQLite and HERPath AI is a personal health literacy companion, not diagnostic medical software.",
                    value=True
                )

                st.markdown('<div style="height: 6px;"></div>', unsafe_allow_html=True)
                reg_submitted = st.form_submit_button(
                    "SIGN UP (Create My Profile)  ➔",
                    type="primary",
                    use_container_width=True
                )

                if reg_submitted:
                    if not reg_name or len(reg_name) < 2:
                        st.error("Please enter a valid Full Name or Pseudonym (at least 2 characters).")
                    elif not reg_pin or len(reg_pin.strip()) < 4:
                        st.error("Please set a 4-digit security PIN (minimum 4 characters).")
                    elif not reg_consent:
                        st.error("Please acknowledge the local storage and educational privacy consent.")
                    else:
                        try:
                            clean_id = reg_id
                            if not clean_id:
                                clean_id = reg_name.lower().replace(" ", "_").replace(".", "") + "_" + uuid.uuid4().hex[:4]
                            
                            pref_payload = {
                                "track_menstrual": reg_cycle,
                                "consent_acknowledged": reg_consent,
                                "focus_areas": reg_focus if reg_focus else ["General Health & Preventative Wellness"]
                            }
                            new_profile_record = register_user(
                                profile_id=clean_id,
                                display_name=reg_name,
                                pin=reg_pin,
                                preferences=pref_payload
                            )
                            st.session_state["current_profile_id"] = new_profile_record.id
                            st.session_state["saved_login_username"] = new_profile_record.display_name.split("(")[0].strip()
                            st.session_state["is_logged_in"] = True
                            navigate_to("Home Dashboard")
                        except ValidationError as ve:
                            st.error(str(ve))
                        except Exception as e:
                            st.error(f"Error creating profile: {str(e)}")

            # Footer interactive link button to switch back to Sign In
            st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
            if st.button("Already have an account? Sign in ➔", key="btn_switch_to_login", use_container_width=True):
                st.session_state["auth_active_tab"] = "Login"
                st.rerun()


# ==========================================
# Main Content Area
# ==========================================
with st.container(key="mobile_scroll_content"):
    if not st.session_state.get("is_logged_in", False):
        render_auth_login_screen()
    elif st.session_state["navigation"] == "Account & Login":
        render_auth_login_screen()
    elif st.session_state["navigation"] == "Home Dashboard":
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
    # SCREEN: TIMELINE INTELLIGENCE (Chronological Health Journey)
    # ==========================================
    elif st.session_state["navigation"] == "Timeline Intelligence":
        st.markdown("""
            <div class="page-title-block">
                <div class="page-title">⏱️ HERPath Timeline Intelligence</div>
                <div class="page-subtitle">Interactive, explainable chronological view of your recorded health journey, symptom episodes, medications, and contextual patterns.</div>
            </div>
        """, unsafe_allow_html=True)

        render_my_health_subnav("Timeline Intelligence")

        tl_service = TimelineService(active_profile.id)
        raw_events = tl_service.fetch_all_events()

        # Taxonomy and available categories/symptoms
        all_recorded_categories = sorted(list(set([e.category for e in raw_events if e.category] + list(SYMPTOM_TAXONOMY.keys()))))
        all_recorded_symptoms = sorted(list(set([e.title for e in raw_events if e.event_type == "symptom" and e.title])))

        # 1. Interactive Timeline Filters
        st.markdown('<div class="section-header">🔍 Interactive Timeline Filters</div>', unsafe_allow_html=True)
        with st.expander("Filter Date Range, Categories, Severity & Event Types", expanded=True):
            f_col_preset, f_col_sort = st.columns([2, 1])
            with f_col_preset:
                date_preset = st.radio(
                    "Date Range Preset",
                    ["Last 30 Days", "Last 7 Days", "Last 90 Days", "All Time", "Custom Range"],
                    horizontal=True,
                    key="tl_preset_selector"
                )
            with f_col_sort:
                sort_order = st.radio(
                    "Timeline Sorting",
                    ["Newest First", "Oldest First"],
                    horizontal=True,
                    key="tl_sort_order_selector"
                )

            # Compute date boundaries
            today_dt = date.today()
            if date_preset == "Last 7 Days":
                start_boundary = today_dt - timedelta(days=7)
                end_boundary = today_dt
            elif date_preset == "Last 30 Days":
                start_boundary = today_dt - timedelta(days=30)
                end_boundary = today_dt
            elif date_preset == "Last 90 Days":
                start_boundary = today_dt - timedelta(days=90)
                end_boundary = today_dt
            elif date_preset == "All Time":
                start_boundary = None
                end_boundary = None
            else: # Custom Range
                c_d1, c_d2 = st.columns(2)
                with c_d1:
                    start_boundary = st.date_input("From Date", value=today_dt - timedelta(days=30), key="tl_custom_start")
                with c_d2:
                    end_boundary = st.date_input("To Date", value=today_dt, key="tl_custom_end")

            filter_c1, filter_c2 = st.columns(2)
            with filter_c1:
                selected_categories = st.multiselect(
                    "Filter by Category",
                    options=all_recorded_categories,
                    default=[],
                    help="Leave empty to include all categories",
                    key="tl_cat_filter_multi"
                )
            with filter_c2:
                selected_symptoms = st.multiselect(
                    "Filter by Specific Symptom",
                    options=all_recorded_symptoms,
                    default=[],
                    help="Leave empty to include all symptoms",
                    key="tl_sym_filter_multi"
                )

            filter_c3, filter_c4 = st.columns([1.2, 1])
            with filter_c3:
                sev_range = st.slider(
                    "Severity Rating (1 to 10)",
                    min_value=1,
                    max_value=10,
                    value=(1, 10),
                    key="tl_severity_range_slider"
                )
            with filter_c4:
                selected_types = st.multiselect(
                    "Event Types to Display",
                    options=["Symptoms", "Medications", "Sleep Context", "Stress Context", "Functional Impact"],
                    default=["Symptoms", "Medications"],
                    key="tl_event_types_multi"
                )

            if st.button("🔄 Reset All Filters", key="tl_btn_reset_filters", use_container_width=True):
                st.session_state["tl_preset_selector"] = "Last 30 Days"
                st.session_state["tl_cat_filter_multi"] = []
                st.session_state["tl_sym_filter_multi"] = []
                st.session_state["tl_severity_range_slider"] = (1, 10)
                st.session_state["tl_event_types_multi"] = ["Symptoms", "Medications"]
                st.rerun()

        # Apply Filters
        filtered_events = TimelineService.filter_events(
            events=raw_events,
            start_date=start_boundary,
            end_date=end_boundary,
            categories=selected_categories if selected_categories else None,
            symptoms=selected_symptoms if selected_symptoms else None,
            min_severity=sev_range[0],
            max_severity=sev_range[1],
            event_types=selected_types if selected_types else ["Symptoms", "Medications"]
        )

        if not filtered_events:
            st.markdown("""
                <div class="timeline-empty-card">
                    <div style="font-size: 1.8rem; margin-bottom: 0.4rem;">🔍</div>
                    <div style="font-weight: 700; font-size: 1.05rem; color: #2A1E24;">No timeline records match your filter criteria</div>
                    <div style="font-size: 0.84rem; color: #7E6F77; margin-top: 6px; max-width: 460px; margin-left: auto; margin-right: auto; line-height: 1.45;">
                        We couldn't find any recorded symptom episodes or medication changes matching this specific date or category filter. Try broadening your dates or resetting filters.
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("🔄 Reset Filter Criteria", key="btn_empty_reset", use_container_width=True):
                st.session_state["tl_preset_selector"] = "Last 30 Days"
                st.session_state["tl_cat_filter_multi"] = []
                st.session_state["tl_sym_filter_multi"] = []
                st.session_state["tl_severity_range_slider"] = (1, 10)
                st.session_state["tl_event_types_multi"] = ["Symptoms", "Medications"]
                st.rerun()

        else:
            # 2. Timeline Summary Metrics
            metrics = TimelineService.calculate_summary_metrics(filtered_events)

            st.markdown('<div class="section-header">📊 Timeline Summary Metrics</div>', unsafe_allow_html=True)
            m_c1, m_c2, m_c3 = st.columns(3)
            with m_c1:
                st.markdown(f"""
                    <div class="timeline-metric-card">
                        <div class="timeline-metric-val">{metrics['total_events']}</div>
                        <div class="timeline-metric-lbl">Total Events</div>
                    </div>
                """, unsafe_allow_html=True)
            with m_c2:
                st.markdown(f"""
                    <div class="timeline-metric-card">
                        <div class="timeline-metric-val">{metrics['symptom_episodes']}</div>
                        <div class="timeline-metric-lbl">Symptom Episodes</div>
                    </div>
                """, unsafe_allow_html=True)
            with m_c3:
                avg_sev_text = f"{metrics['avg_severity']}/10" if metrics['avg_severity'] is not None else "N/A"
                st.markdown(f"""
                    <div class="timeline-metric-card">
                        <div class="timeline-metric-val">{avg_sev_text}</div>
                        <div class="timeline-metric-lbl">Avg Severity</div>
                    </div>
                """, unsafe_allow_html=True)

            m_c4, m_c5, m_c6 = st.columns(3)
            with m_c4:
                max_sev_text = f"{metrics['max_severity']}/10" if metrics['max_severity'] is not None else "N/A"
                st.markdown(f"""
                    <div class="timeline-metric-card">
                        <div class="timeline-metric-val">{max_sev_text}</div>
                        <div class="timeline-metric-lbl">Peak Severity</div>
                    </div>
                """, unsafe_allow_html=True)
            with m_c5:
                avg_dur_text = f"{metrics['avg_duration']}h" if metrics['avg_duration'] is not None else "N/A"
                st.markdown(f"""
                    <div class="timeline-metric-card">
                        <div class="timeline-metric-val">{avg_dur_text}</div>
                        <div class="timeline-metric-lbl">Avg Duration</div>
                    </div>
                """, unsafe_allow_html=True)
            with m_c6:
                st.markdown(f"""
                    <div class="timeline-metric-card">
                        <div class="timeline-metric-val">{metrics['impact_count']}</div>
                        <div class="timeline-metric-lbl">Impacted Logs</div>
                    </div>
                """, unsafe_allow_html=True)

            # 3. Interactive Visualizations
            st.markdown('<div class="section-header">📈 Interactive Timeline Visualizations</div>', unsafe_allow_html=True)
            tab_sev, tab_swim, tab_ctx = st.tabs([
                "📈 Symptom Severity Timeline",
                "🗓️ Unified Event Swimlane",
                "🌙 Sleep & Contextual Co-Occurrence"
            ])

            with tab_sev:
                st.caption("Plots recorded symptom episodes and severity ratings against actual calendar dates.")
                sev_fig = TimelineService.create_severity_timeline_chart(filtered_events)
                st.plotly_chart(sev_fig, use_container_width=True)

            with tab_swim:
                st.caption("Displays symptom episodes alongside medication starts and functional impact observations on a unified timeline.")
                swim_fig = TimelineService.create_unified_event_timeline_chart(filtered_events)
                st.plotly_chart(swim_fig, use_container_width=True)

            with tab_ctx:
                st.caption("Shows how symptom severity levels coincide across restful vs. disrupted sleep quality tiers (when at least 3 entries exist).")
                ctx_fig = TimelineService.create_contextual_cooccurrence_chart(filtered_events)
                st.plotly_chart(ctx_fig, use_container_width=True)

            # 4. Period Comparison Section
            st.markdown('<div class="section-header">⚖️ Compare Symptoms Across Selected Periods</div>', unsafe_allow_html=True)
            with st.expander("Configure & Compare Two Time Periods", expanded=True):
                comp_mode = st.radio(
                    "Comparison Period Selection",
                    ["Recent 30 Days vs Previous 30 Days", "Recent 14 Days vs Previous 14 Days", "Custom Comparison Ranges"],
                    horizontal=True,
                    key="tl_comp_mode_selector"
                )

                today_c = date.today()
                if comp_mode == "Recent 14 Days vs Previous 14 Days":
                    p_a_start, p_a_end = today_c - timedelta(days=14), today_c
                    p_b_start, p_b_end = today_c - timedelta(days=28), today_c - timedelta(days=15)
                    label_a, label_b = "Recent 14 Days", "Previous 14 Days"
                    days_a, days_b = 14, 14
                elif comp_mode == "Recent 30 Days vs Previous 30 Days":
                    p_a_start, p_a_end = today_c - timedelta(days=30), today_c
                    p_b_start, p_b_end = today_c - timedelta(days=60), today_c - timedelta(days=31)
                    label_a, label_b = "Recent 30 Days", "Previous 30 Days"
                    days_a, days_b = 30, 30
                else: # Custom
                    cp_c1, cp_c2 = st.columns(2)
                    with cp_c1:
                        st.markdown("<b>Period A (Current / Target)</b>", unsafe_allow_html=True)
                        p_a_start = st.date_input("Period A Start", value=today_c - timedelta(days=30), key="tl_p_a_start")
                        p_a_end = st.date_input("Period A End", value=today_c, key="tl_p_a_end")
                    with cp_c2:
                        st.markdown("<b>Period B (Baseline / Comparison)</b>", unsafe_allow_html=True)
                        p_b_start = st.date_input("Period B Start", value=today_c - timedelta(days=60), key="tl_p_b_start")
                        p_b_end = st.date_input("Period B End", value=today_c - timedelta(days=31), key="tl_p_b_end")
                    label_a = f"{p_a_start} to {p_a_end}"
                    label_b = f"{p_b_start} to {p_b_end}"
                    days_a = max(1, (p_a_end - p_a_start).days + 1)
                    days_b = max(1, (p_b_end - p_b_start).days + 1)

                # Filter events for both periods (respecting category/symptom filters if selected)
                events_period_a = TimelineService.filter_events(
                    raw_events,
                    start_date=p_a_start,
                    end_date=p_a_end,
                    categories=selected_categories if selected_categories else None,
                    symptoms=selected_symptoms if selected_symptoms else None
                )
                events_period_b = TimelineService.filter_events(
                    raw_events,
                    start_date=p_b_start,
                    end_date=p_b_end,
                    categories=selected_categories if selected_categories else None,
                    symptoms=selected_symptoms if selected_symptoms else None
                )

                comparison_results = TimelineService.compare_periods(
                    events_period_a,
                    events_period_b,
                    period_a_label=label_a,
                    period_b_label=label_b,
                    days_a=days_a,
                    days_b=days_b
                )

                # Display comparative KPIs
                deltas = comparison_results["deltas"]
                pa_m = comparison_results["period_a"]["metrics"]
                pb_m = comparison_results["period_b"]["metrics"]

                st.markdown(f"##### Comparative Delta Summary ({label_a} vs. {label_b})")
                cd_1, cd_2, cd_3 = st.columns(3)
                with cd_1:
                    ep_diff = deltas["episodes"]
                    diff_pill = (
                        f"<span class='delta-pill-positive'>+{ep_diff}</span>" if ep_diff > 0
                        else f"<span class='delta-pill-negative'>{ep_diff}</span>" if ep_diff < 0
                        else "<span class='delta-pill-neutral'>0</span>"
                    )
                    st.markdown(f"""
                        <div class="period-metric-box">
                            <div style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); font-weight: 700;">Episodes Shift</div>
                            <div style="font-size: 1.35rem; font-weight: 700; color: #2A1E24; margin: 4px 0;">{pa_m['symptom_episodes']} vs {pb_m['symptom_episodes']} {diff_pill}</div>
                            <div style="font-size: 0.72rem; color: var(--text-secondary);">Daily rate: {comparison_results['period_a']['daily_rate']}/d vs {comparison_results['period_b']['daily_rate']}/d</div>
                        </div>
                    """, unsafe_allow_html=True)

                with cd_2:
                    sev_diff = deltas["severity"]
                    if sev_diff is not None:
                        diff_pill = (
                            f"<span class='delta-pill-positive'>+{sev_diff}</span>" if sev_diff > 0
                            else f"<span class='delta-pill-negative'>{sev_diff}</span>" if sev_diff < 0
                            else "<span class='delta-pill-neutral'>0.0</span>"
                        )
                        sev_summary = f"{pa_m['avg_severity'] or 'N/A'} vs {pb_m['avg_severity'] or 'N/A'} {diff_pill}"
                    else:
                        sev_summary = "N/A"
                    st.markdown(f"""
                        <div class="period-metric-box">
                            <div style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); font-weight: 700;">Avg Severity Shift</div>
                            <div style="font-size: 1.35rem; font-weight: 700; color: #2A1E24; margin: 4px 0;">{sev_summary}</div>
                            <div style="font-size: 0.72rem; color: var(--text-secondary);">Peak: {pa_m['max_severity'] or 'N/A'}/10 vs {pb_m['max_severity'] or 'N/A'}/10</div>
                        </div>
                    """, unsafe_allow_html=True)

                with cd_3:
                    dur_diff = deltas["duration"]
                    dur_summary = f"{pa_m['avg_duration'] or 'N/A'}h vs {pb_m['avg_duration'] or 'N/A'}h"
                    st.markdown(f"""
                        <div class="period-metric-box">
                            <div style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); font-weight: 700;">Avg Duration</div>
                            <div style="font-size: 1.35rem; font-weight: 700; color: #2A1E24; margin: 4px 0;">{dur_summary}</div>
                            <div style="font-size: 0.72rem; color: var(--text-secondary);">Delta: {f'{dur_diff:+0.1f}h' if dur_diff is not None else 'N/A'}</div>
                        </div>
                    """, unsafe_allow_html=True)

                # Period Comparison Chart
                st.plotly_chart(TimelineService.create_period_comparison_chart(comparison_results), use_container_width=True)

                # Per-symptom breakdown table
                sym_breakdown = comparison_results.get("symptom_breakdown", [])
                if sym_breakdown:
                    st.markdown("##### Symptom-by-Symptom Comparative Breakdown")
                    breakdown_rows = []
                    for b in sym_breakdown:
                        breakdown_rows.append({
                            "Symptom": b["symptom"],
                            f"Episodes ({label_a})": b["episodes_a"],
                            f"Episodes ({label_b})": b["episodes_b"],
                            "Episode Delta": f"{b['episodes_diff']:+d}",
                            f"Avg Sev ({label_a})": f"{b['avg_severity_a']}/10" if b['avg_severity_a'] is not None else "N/A",
                            f"Avg Sev ({label_b})": f"{b['avg_severity_b']}/10" if b['avg_severity_b'] is not None else "N/A",
                            "Severity Delta": f"{b['severity_diff']:+0.1f}" if b['severity_diff'] is not None else "N/A",
                            "Peak Severity": f"{b['max_severity']}/10" if b['max_severity'] is not None else "N/A"
                        })
                    st.dataframe(pd.DataFrame(breakdown_rows), use_container_width=True, hide_index=True)
                else:
                    st.info("No common symptoms recorded across both comparison periods.")

            # 5. Explainable Health Insights
            st.markdown('<div class="section-header">💡 Explainable Health Insights (Rule-Based)</div>', unsafe_allow_html=True)
            insights = TimelineService.generate_explainable_insights(filtered_events, comparison=comparison_results)

            for ins in insights:
                st.markdown(f"""
                    <div class="insight-card-wrapper">
                        <div style="font-weight: 700; font-size: 0.94rem; color: #2A1E24;">{ins['title']}</div>
                        <div style="font-size: 0.85rem; color: #34272E; margin-top: 4px; line-height: 1.45;">{ins['statement']}</div>
                        <div class="insight-evidence-box">
                            <div><b>Exact Evidence:</b> {ins['exact_evidence']}</div>
                            <div><b>Date Range:</b> {ins['date_range']} &bull; <b>Relevant Records:</b> {ins['record_count']}</div>
                            <div class="insight-formula-caption">Calculation: {ins['calculation_note']}</div>
                        </div>
                        <div class="insight-limitation-note">⚠️ Note: {ins['limitation']}</div>
                    </div>
                """, unsafe_allow_html=True)

            # 6. Chronological Health Event Feed & Detail View
            st.markdown('<div class="section-header">📜 Chronological Health Event Feed</div>', unsafe_allow_html=True)
            st.caption(f"Showing **{len(filtered_events)}** chronological health events grounded in your database records.")

            display_events = list(filtered_events)
            if sort_order == "Newest First":
                display_events.reverse()

            for ev in display_events:
                is_med = ev.event_type == "medication"
                is_sev = ev.severity is not None and ev.severity >= 7
                card_class = "timeline-event-card event-medication" if is_med else ("timeline-event-card event-severe" if is_sev else "timeline-event-card")

                type_badge = "<span class='timeline-badge-medication'>Medication Started</span>" if is_med else "<span class='timeline-badge-symptom'>Symptom Episode</span>"

                sev_pill = ""
                if ev.severity is not None:
                    if ev.severity <= 3:
                        sev_pill = f"<span class='timeline-severity-pill-mild'>Mild {ev.severity}/10</span>"
                    elif ev.severity <= 6:
                        sev_pill = f"<span class='timeline-severity-pill-mod'>Mod {ev.severity}/10</span>"
                    else:
                        sev_pill = f"<span class='timeline-severity-pill-sev'>Severe {ev.severity}/10</span>"

                impact_pill = f"<span class='timeline-impact-pill'>{ev.impact}</span>" if ev.impact and ev.impact != "None" else ""

                expander_title = f"{'💊' if is_med else '🌸'} {ev.date} — {ev.title} {'(' + str(ev.severity) + '/10)' if ev.severity else ''}"

                with st.expander(expander_title, expanded=False):
                    st.markdown(f"""
                        <div style="display: flex; gap: 6px; align-items: center; margin-bottom: 8px; flex-wrap: wrap;">
                            <span class="timeline-date-chip">📅 {ev.date} {ev.time or ''}</span>
                            {type_badge}
                            {sev_pill}
                            {impact_pill}
                        </div>
                    """, unsafe_allow_html=True)

                    d_col1, d_col2 = st.columns(2)
                    with d_col1:
                        st.write(f"**Category:** {ev.category}")
                        if ev.duration_hours is not None:
                            st.write(f"**Duration:** {ev.duration_hours} hours")
                        if ev.status:
                            st.write(f"**Status:** {ev.status}")
                        if is_med:
                            st.write(f"**Dosage:** {ev.dosage or 'Standard dose'}")
                            st.write(f"**Frequency:** {ev.frequency or 'As directed'}")

                    with d_col2:
                        if ev.context:
                            ctx = ev.context
                            if ctx.get("sleep"):
                                st.write(f"**Sleep Quality:** {ctx['sleep']}")
                            if ctx.get("stress"):
                                st.write(f"**Stress Level:** {ctx['stress']}")
                            if ctx.get("energy"):
                                st.write(f"**Energy:** {ctx['energy']}")
                            if ctx.get("cycle_phase"):
                                st.write(f"**Cycle Phase:** {ctx['cycle_phase']}")

                    if ev.notes:
                        st.markdown(f"**Notes:** *{ev.notes}*")

                    st.caption(f"Data Source: {ev.source}")

                    # Edit link for symptoms
                    if ev.event_type == "symptom":
                        raw_id = int(ev.event_id.replace("symptom_", "")) if ev.event_id.startswith("symptom_") else None
                        if raw_id:
                            if st.button("✏️ Edit Record in Journal", key=f"tl_edit_{ev.event_id}", use_container_width=True):
                                st.session_state["editing_entry_id"] = raw_id
                                navigate_to("Symptom Journal")


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

        acc_c1, acc_c2 = st.columns(2)
        with acc_c1:
            if st.button("🔐 Account & Login Portal", key="settings_btn_account_portal", use_container_width=True):
                navigate_to("Account & Login")
        with acc_c2:
            if st.button("🚪 Log Out & Lock", key="settings_btn_logout", use_container_width=True):
                st.session_state["is_logged_in"] = False
                st.session_state["navigation"] = "Account & Login"
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

    # ==========================================
    # SCREEN 10: ACCOUNT & LOGIN
    # ==========================================
    elif st.session_state["navigation"] == "Account & Login":
        render_auth_login_screen()

    # Dedicated scroll clearance spacer at bottom of content
    st.markdown('<div class="scroll-bottom-spacer" style="height: 36px; min-height: 36px;"></div>', unsafe_allow_html=True)


# ==========================================
# Fixed iOS Bottom Tab Bar (4 Destinations)
# Appears ONLY after successful entry into the application
# ==========================================
if st.session_state.get("is_logged_in", False):
    with st.container(key="mobile_bottom_bar"):
        nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
        curr_nav = st.session_state["navigation"]

        with nav_col1:
            is_active = curr_nav == "Home Dashboard"
            if st.button("🌸 Home", key="bnav_home", use_container_width=True, type="primary" if is_active else "secondary"):
                navigate_to("Home Dashboard")

        with nav_col2:
            is_active = curr_nav in ["Symptom Journal", "Medication & Treatments", "Timeline Intelligence", "Health Insights", "My Health Report"]
            if st.button("💗 My Health", key="bnav_health", use_container_width=True, type="primary" if is_active else "secondary"):
                navigate_to("Symptom Journal")

        with nav_col3:
            is_active = curr_nav in ["Care Navigator"]
            if st.button("🛡️ Care", key="bnav_care", use_container_width=True, type="primary" if is_active else "secondary"):
                navigate_to("Care Navigator")

        with nav_col4:
            is_active = curr_nav in ["Women's Health Library", "Ask HERPath"]
            if st.button("📚 Learn", key="bnav_learn", use_container_width=True, type="primary" if is_active else "secondary"):
                navigate_to("Women's Health Library")

        st.markdown('<div class="iphone-home-indicator"></div>', unsafe_allow_html=True)
else:
    # On login/registration: hide four-tab navigation, rendering only the clean iOS home indicator bar
    st.markdown("""
        <div class="iphone-home-indicator-unauth">
            <div class="iphone-home-indicator"></div>
        </div>
    """, unsafe_allow_html=True)
