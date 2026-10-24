"""
HERPath AI - Fictional Demonstration Data Seeder
recHERsion 2026 | PS1: Women's Healthcare

Generates realistic, completely fictional demonstration records for hackathon evaluation.
Contains NO real patient information or sensitive data.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# Ensure project root is in sys.path
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from database import init_db, add_symptom, clear_profile_symptoms, get_profile, create_profile
from models import SymptomEntry


def seed_demo_data(db_path: Optional[str] = None) -> None:
    """Populates the database with realistic, fictional demonstration profiles and symptom logs."""
    init_db(db_path)
    today = datetime.now().date()

    # Ensure demo profiles exist
    if not get_profile("demo_priya", db_path):
        create_profile("demo_priya", "Priya (PCOS & Migraine Tracking)", {
            "track_menstrual": True,
            "consent_acknowledged": True,
            "focus_areas": ["PCOS", "Migraine", "Energy"]
        }, db_path)

    if not get_profile("demo_ananya", db_path):
        create_profile("demo_ananya", "Ananya (Perimenopause & Sleep)", {
            "track_menstrual": True,
            "consent_acknowledged": True,
            "focus_areas": ["Perimenopause", "Sleep", "Mood"]
        }, db_path)

    if not get_profile("demo_elena", db_path):
        create_profile("demo_elena", "Elena (Endometriosis & Pelvic Health)", {
            "track_menstrual": True,
            "consent_acknowledged": True,
            "focus_areas": ["Pelvic Pain", "Fatigue"]
        }, db_path)

    # 1. Seed Priya: Focus on Migraine, Fatigue, Pelvic Cramping
    clear_profile_symptoms("demo_priya", db_path)
    priya_entries = [
        (28, "Migraine", "Neurological & Head", 7, 8.0, "Resolved", "Moderate (Modified daily plans)", "Throbbing left temple, photophobia. Took prescribed triptan.", "Disrupted / Fragmented", "High / Pressured", "Sluggish / Low", "Follicular (Pre-ovulation)"),
        (25, "Severe Fatigue / Exhaustion", "Systemic & Energy", 5, 12.0, "Resolved", "Mild (Minor inconvenience)", "Heavy brain fog by early afternoon.", "Moderate (5-7 hrs)", "Moderate / Manageable", "Sluggish / Low", "Follicular (Pre-ovulation)"),
        (21, "Migraine", "Neurological & Head", 8, 14.0, "Resolved", "Severe (Unable to perform daily tasks)", "Intense aura with nausea. Had to rest in dark room.", "Severe Insomnia (<5 hrs)", "Extreme / Overwhelming", "Severely Depleted", "Ovulatory (Mid-cycle)"),
        (18, "Severe Abdominal Bloating", "Gastrointestinal & Abdominal", 4, 6.0, "Resolved", "Mild (Minor inconvenience)", "Bloating after dinner.", "Restful (7-9 hrs)", "Low / Relaxed", "Normal", "Ovulatory (Mid-cycle)"),
        (14, "Pelvic Pain / Cramping", "Pelvic & Menstrual", 6, 8.0, "Resolved", "Moderate (Modified daily plans)", "Dull right lower quadrant ache.", "Disrupted / Fragmented", "High / Pressured", "Sluggish / Low", "Luteal (Pre-period)"),
        (10, "Migraine", "Neurological & Head", 6, 6.0, "Resolved", "Moderate (Modified daily plans)", "Moderate frontal headache.", "Disrupted / Fragmented", "High / Pressured", "Sluggish / Low", "Luteal (Pre-period)"),
        (7, "Severe Fatigue / Exhaustion", "Systemic & Energy", 6, 24.0, "Resolved", "Moderate (Modified daily plans)", "Difficulty focusing on work screen.", "Severe Insomnia (<5 hrs)", "High / Pressured", "Severely Depleted", "Luteal (Pre-period)"),
        (4, "Migraine", "Neurological & Head", 7, 10.0, "Resolved", "Moderate (Modified daily plans)", "Throbbing headache preceded by poor sleep night before.", "Disrupted / Fragmented", "High / Pressured", "Sluggish / Low", "Menstrual (Active period)"),
        (2, "Heavy Menstrual Bleeding", "Pelvic & Menstrual", 6, 12.0, "Resolved", "Moderate (Modified daily plans)", "Day 2 of period. Heavier than usual.", "Moderate (5-7 hrs)", "Moderate / Manageable", "Sluggish / Low", "Menstrual (Active period)"),
        (0, "Pelvic Pain / Cramping", "Pelvic & Menstrual", 5, 4.0, "Ongoing", "Mild (Minor inconvenience)", "Lingering menstrual cramps.", "Moderate (5-7 hrs)", "Low / Relaxed", "Normal", "Menstrual (Active period)")
    ]

    for offset, sym, cat, sev, dur, stat, imp, notes, slp, strss, enrgy, cyc in priya_entries:
        entry_date = (today - timedelta(days=offset)).strftime("%Y-%m-%d")
        add_symptom(SymptomEntry(
            id=None,
            profile_id="demo_priya",
            category=cat,
            symptom=sym,
            onset_date=entry_date,
            severity=sev,
            duration_hours=dur,
            status=stat,
            impact=imp,
            notes=notes,
            context={"sleep": slp, "stress": strss, "energy": enrgy, "cycle_phase": cyc}
        ), db_path)

    # 2. Seed Ananya: Perimenopause & Sleep
    clear_profile_symptoms("demo_ananya", db_path)
    ananya_entries = [
        (26, "Hot Flashes", "Systemic & Energy", 6, 1.0, "Resolved", "Moderate (Modified daily plans)", "Intense sudden warmth and facial flushing.", "Disrupted / Fragmented", "Moderate / Manageable", "Normal", "Post-menopausal"),
        (22, "Night Sweats", "Systemic & Energy", 7, 2.0, "Resolved", "Severe (Unable to perform daily tasks)", "Woke up drenched at 3am. Chilled afterward.", "Severe Insomnia (<5 hrs)", "High / Pressured", "Severely Depleted", "Post-menopausal"),
        (18, "Insomnia / Difficulty Falling Asleep", "Mood & Sleep", 6, 5.0, "Resolved", "Moderate (Modified daily plans)", "Tossed and turned until 4am.", "Severe Insomnia (<5 hrs)", "High / Pressured", "Sluggish / Low", "Post-menopausal"),
        (15, "Brain Fog", "Systemic & Energy", 5, 8.0, "Resolved", "Mild (Minor inconvenience)", "Word recall difficulty during morning presentation.", "Moderate (5-7 hrs)", "Moderate / Manageable", "Sluggish / Low", "Post-menopausal"),
        (11, "Hot Flashes", "Systemic & Energy", 5, 0.5, "Resolved", "Mild (Minor inconvenience)", "Afternoon episode during warm meeting room.", "Restful (7-9 hrs)", "Low / Relaxed", "Normal", "Post-menopausal"),
        (8, "Night Sweats", "Systemic & Energy", 6, 2.0, "Resolved", "Moderate (Modified daily plans)", "Disrupted REM sleep cycle.", "Disrupted / Fragmented", "Moderate / Manageable", "Sluggish / Low", "Post-menopausal"),
        (4, "Hot Flashes", "Systemic & Energy", 6, 1.0, "Resolved", "Moderate (Modified daily plans)", "Flushing and mild palpitations.", "Moderate (5-7 hrs)", "Moderate / Manageable", "Normal", "Post-menopausal"),
        (1, "Anxiety / Restlessness", "Mood & Sleep", 5, 6.0, "Ongoing", "Mild (Minor inconvenience)", "Unexplained nervous energy.", "Moderate (5-7 hrs)", "High / Pressured", "Normal", "Post-menopausal")
    ]

    for offset, sym, cat, sev, dur, stat, imp, notes, slp, strss, enrgy, cyc in ananya_entries:
        entry_date = (today - timedelta(days=offset)).strftime("%Y-%m-%d")
        add_symptom(SymptomEntry(
            id=None,
            profile_id="demo_ananya",
            category=cat,
            symptom=sym,
            onset_date=entry_date,
            severity=sev,
            duration_hours=dur,
            status=stat,
            impact=imp,
            notes=notes,
            context={"sleep": slp, "stress": strss, "energy": enrgy, "cycle_phase": cyc}
        ), db_path)

    # 3. Seed Elena: Endometriosis & Pelvic Health
    clear_profile_symptoms("demo_elena", db_path)
    elena_entries = [
        (25, "Pelvic Pain / Cramping", "Pelvic & Menstrual", 8, 12.0, "Resolved", "Severe (Unable to perform daily tasks)", "Deep sharp throbbing pelvic pain radiating to lower back.", "Disrupted / Fragmented", "High / Pressured", "Severely Depleted", "Luteal (Pre-period)"),
        (20, "Severe Abdominal Bloating", "Gastrointestinal & Abdominal", 6, 10.0, "Resolved", "Moderate (Modified daily plans)", "'Endo belly' distention.", "Moderate (5-7 hrs)", "Moderate / Manageable", "Sluggish / Low", "Luteal (Pre-period)"),
        (16, "Pelvic Pain / Cramping", "Pelvic & Menstrual", 7, 8.0, "Resolved", "Severe (Unable to perform daily tasks)", "Painful bowel movement during flare.", "Disrupted / Fragmented", "High / Pressured", "Sluggish / Low", "Luteal (Pre-period)"),
        (12, "Severe Fatigue / Exhaustion", "Systemic & Energy", 6, 24.0, "Resolved", "Moderate (Modified daily plans)", "Body feels weighed down.", "Moderate (5-7 hrs)", "Moderate / Manageable", "Sluggish / Low", "Menstrual (Active period)"),
        (6, "Pelvic Pain / Cramping", "Pelvic & Menstrual", 8, 16.0, "Resolved", "Severe (Unable to perform daily tasks)", "Day 1 of cycle. Heating pad + prescribed NSAID.", "Severe Insomnia (<5 hrs)", "Extreme / Overwhelming", "Severely Depleted", "Menstrual (Active period)"),
        (2, "Pelvic Floor Pressure / Heaviness", "Urinary & Pelvic Floor", 5, 6.0, "Ongoing", "Mild (Minor inconvenience)", "Feeling of downward pressure when standing.", "Restful (7-9 hrs)", "Low / Relaxed", "Normal", "Follicular (Pre-ovulation)")
    ]

    for offset, sym, cat, sev, dur, stat, imp, notes, slp, strss, enrgy, cyc in elena_entries:
        entry_date = (today - timedelta(days=offset)).strftime("%Y-%m-%d")
        add_symptom(SymptomEntry(
            id=None,
            profile_id="demo_elena",
            category=cat,
            symptom=sym,
            onset_date=entry_date,
            severity=sev,
            duration_hours=dur,
            status=stat,
            impact=imp,
            notes=notes,
            context={"sleep": slp, "stress": strss, "energy": enrgy, "cycle_phase": cyc}
        ), db_path)


if __name__ == "__main__":
    seed_demo_data()
    print("Realistic demonstration data populated successfully!")
