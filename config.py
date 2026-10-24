"""
HERPath AI - Configuration and Constants
recHERsion 2026 | PS1: Women's Healthcare
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"

DATA_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Application Metadata
APP_TITLE = "HERPath AI"
APP_NAME = "HERPath AI — Women's Health Intelligence & Care Navigation Platform"
APP_TAGLINE = "Understand your symptoms. Discover patterns. Take informed next steps."
HACKATHON_EVENT = "recHERsion 2026 — ACM-W, NITK Surathkal | PS1: Women's Healthcare"

# Database & Storage
DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "herpath.db"))
RESOURCES_FILE_PATH = str(DATA_DIR / "health_resources.json")

# Core Disclaimers
CLINICAL_DISCLAIMER = (
    "HERPath AI provides general health information and helps organize personal health observations. "
    "It does not diagnose conditions, predict diseases, or replace professional medical care. "
    "Always consult a qualified healthcare provider regarding symptoms or medical concerns."
)

EMERGENCY_NOTICE = (
    "If you are experiencing sudden severe chest pain, severe shortness of breath, unexplained fainting, "
    "sudden loss of vision, or severe acute abdominal/pelvic pain, seek immediate emergency medical evaluation "
    "(call 112 / 911 / 999 or proceed to the nearest emergency medical department)."
)

# Symptom Categories & Associated Common Terms
SYMPTOM_TAXONOMY = {
    "Pelvic & Menstrual": [
        "Pelvic Pain / Cramping",
        "Heavy Menstrual Bleeding",
        "Irregular Cycles",
        "Spotting / Bleeding Between Periods",
        "Painful Intercourse (Dyspareunia)",
        "Premenstrual Dysphoria",
        "Ovulation Pain (Mittelschmerz)"
    ],
    "Systemic & Energy": [
        "Severe Fatigue / Exhaustion",
        "Brain Fog",
        "Unexplained Muscle / Joint Pain",
        "Hot Flashes",
        "Night Sweats",
        "Persistent Low Energy",
        "Temperature Sensitivity"
    ],
    "Neurological & Head": [
        "Migraine",
        "Tension Headache",
        "Dizziness / Vertigo",
        "Lightheadedness upon Standing",
        "Visual Aura"
    ],
    "Breast Health": [
        "Cyclical Breast Tenderness",
        "Localized Breast Pain",
        "Breast Firmness / Swelling",
        "Nipple Sensitivity / Discharge"
    ],
    "Gastrointestinal & Abdominal": [
        "Severe Abdominal Bloating",
        "Abdominal Cramping",
        "Nausea",
        "Constipation",
        "Diarrhea / Loose Stools",
        "Indigestion / Acid Reflux"
    ],
    "Urinary & Pelvic Floor": [
        "Burning during Urination (Dysuria)",
        "Frequent Urination",
        "Urinary Urgency",
        "Pelvic Floor Pressure / Heaviness"
    ],
    "Mood & Sleep": [
        "Anxiety / Restlessness",
        "Insomnia / Difficulty Falling Asleep",
        "Frequent Night Waking",
        "Irritability",
        "Low Mood / Sadness"
    ]
}

# Contextual Observation Options
SLEEP_QUALITIES = ["Restful (7-9 hrs)", "Moderate (5-7 hrs)", "Disrupted / Fragmented", "Severe Insomnia (<5 hrs)"]
STRESS_LEVELS = ["Low / Relaxed", "Moderate / Manageable", "High / Pressured", "Extreme / Overwhelming"]
ENERGY_LEVELS = ["High / Vibrant", "Normal", "Sluggish / Low", "Severely Depleted"]
CYCLE_PHASES = ["Not tracking / NA", "Follicular (Pre-ovulation)", "Ovulatory (Mid-cycle)", "Luteal (Pre-period)", "Menstrual (Active period)", "Post-menopausal"]
DAILY_IMPACT_LEVELS = ["None", "Mild (Minor inconvenience)", "Moderate (Modified daily plans)", "Severe (Unable to perform daily tasks)"]

# Safety Guidance Priorities
PRIORITY_EMERGENCY = "EMERGENCY_EVALUATION"
PRIORITY_PROMPT = "PROMPT_EVALUATION"
PRIORITY_ROUTINE = "ROUTINE_CONSULTATION"
PRIORITY_SELFCARE = "HEALTH_EDUCATION"
