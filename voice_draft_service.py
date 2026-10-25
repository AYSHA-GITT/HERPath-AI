"""
HERPath AI - Voice & Spoken Entry Draft Service
recHERsion 2026 | PS1: Women's Healthcare

Provides deterministic natural language extraction of voice transcripts and quick text input
into editable, reviewable draft symptom entries before committing to the SQLite database.
Follows strict clinical safety boundaries: never diagnoses or auto-commits records without
explicit user review and confirmation.
"""

import re
from typing import Dict, Any, Optional, Tuple
from datetime import date

from config import (
    SYMPTOM_TAXONOMY,
    DAILY_IMPACT_LEVELS,
    SLEEP_QUALITIES,
    STRESS_LEVELS,
    CYCLE_PHASES
)


def parse_symptom_voice_draft(transcript: str, default_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Parses a spoken or typed transcript into a structured draft symptom entry
    ready for user review and manual editing before saving.
    """
    if not transcript or not transcript.strip():
        return {
            "symptom": "Unspecified Symptom",
            "category": "General Wellbeing & Energy",
            "severity": 5,
            "duration_hours": 1.0,
            "onset_date": default_date or str(date.today()),
            "status": "Ongoing",
            "impact": "Normal activities modified",
            "notes": "",
            "context": {},
            "parsed_fields": [],
            "raw_transcript": ""
        }

    raw = transcript.strip()
    text = raw.lower()
    parsed_fields = []

    # 1. Symptom & Category Identification
    matched_symptom = None
    matched_category = None

    # Exact or substring match in taxonomy
    for category, symptoms in SYMPTOM_TAXONOMY.items():
        for s in symptoms:
            s_clean = s.lower()
            # Split compound taxonomy names like "Pelvic Pain / Cramping"
            parts = [p.strip() for p in s_clean.replace("/", ",").split(",")]
            for part in parts:
                if len(part) >= 4 and part in text:
                    matched_symptom = s
                    matched_category = category
                    parsed_fields.append(f"Identified Symptom: '{s}' ({category})")
                    break
            if matched_symptom:
                break
        if matched_symptom:
            break

    # Secondary heuristic matches for common spoken colloquialisms
    if not matched_symptom:
        if "headache" in text or "migraine" in text or "head throbbing" in text:
            matched_symptom = "Migraine" if "migraine" in text else "Tension Headache"
            matched_category = "Neurological & Head"
        elif "cramp" in text or "pelvic" in text or "period pain" in text:
            matched_symptom = "Pelvic Pain / Cramping"
            matched_category = "Pelvic & Menstrual"
        elif "hot flash" in text or "night sweat" in text:
            matched_symptom = "Hot Flashes"
            matched_category = "Systemic & Energy"
        elif "tired" in text or "fatigue" in text or "exhaust" in text:
            matched_symptom = "Severe Fatigue / Exhaustion"
            matched_category = "Systemic & Energy"
        elif "nausea" in text or "vomit" in text or "bloat" in text:
            matched_symptom = "Pelvic Pain / Cramping"
            matched_category = "Pelvic & Menstrual"
        elif "brain fog" in text or "foggy" in text:
            matched_symptom = "Brain Fog"
            matched_category = "Systemic & Energy"
        elif "heavy bleeding" in text or "flooding" in text:
            matched_symptom = "Heavy Menstrual Bleeding"
            matched_category = "Pelvic & Menstrual"
        else:
            matched_symptom = "Unspecified Symptom"
            matched_category = "Systemic & Energy"
        parsed_fields.append(f"Colloquial Match: '{matched_symptom}' ({matched_category})")

    # 2. Severity Extraction (1–10)
    severity = 5  # sensible default
    # Pattern 1: Explicit numbers (e.g. "severity 8", "pain level 7", "rated 6", "8 out of 10", "8/10")
    num_matches = re.findall(
        r'(?:severity|pain|level|rated|scale|score|rate)\s*(?:is|was|of|at)?\s*(\d{1,2})',
        text
    )
    if not num_matches:
        num_matches = re.findall(r'(\d{1,2})\s*(?:out of 10|/10)', text)

    if num_matches:
        val = int(num_matches[0])
        if 1 <= val <= 10:
            severity = val
            parsed_fields.append(f"Severity: {severity}/10 (explicit number)")
    else:
        # Qualitative keyword extraction
        if any(w in text for w in ["unbearable", "excruciating", "emergency", "worst", "extreme"]):
            severity = 9
            parsed_fields.append("Severity: 9/10 ('unbearable/extreme')")
        elif any(w in text for w in ["severe", "intense", "heavy", "bad"]):
            severity = 8
            parsed_fields.append("Severity: 8/10 ('severe/intense')")
        elif any(w in text for w in ["moderate", "medium", "noticeable"]):
            severity = 5
            parsed_fields.append("Severity: 5/10 ('moderate')")
        elif any(w in text for w in ["mild", "slight", "light", "a little"]):
            severity = 3
            parsed_fields.append("Severity: 3/10 ('mild/slight')")

    # 3. Duration Extraction (in hours)
    duration_hours = 1.0
    hour_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)', text)
    minute_match = re.search(r'(\d+)\s*(?:minutes?|mins?)', text)
    if hour_match:
        val = float(hour_match.group(1))
        if 0 < val <= 72:
            duration_hours = val
            parsed_fields.append(f"Duration: {duration_hours} hours")
    elif minute_match:
        val = float(minute_match.group(1)) / 60.0
        duration_hours = round(val, 2)
        parsed_fields.append(f"Duration: {duration_hours} hours ({minute_match.group(1)} mins)")
    elif "all day" in text or "whole day" in text:
        duration_hours = 8.0
        parsed_fields.append("Duration: 8.0 hours ('all day')")

    # 4. Functional Impact Extraction
    impact = "Normal activities modified"
    if any(w in text for w in ["bed", "bedrest", "can't get up", "lying down"]):
        impact = "Bedrest required"
        parsed_fields.append("Impact: Bedrest required")
    elif any(w in text for w in ["unable to work", "can't work", "missed work", "stopped working", "couldn't work", "unable to study"]):
        impact = "Unable to work / Study"
        parsed_fields.append("Impact: Unable to work / Study")
    elif any(w in text for w in ["mild", "slight", "inconvenience", "minor"]):
        impact = "Mild inconvenience"
        parsed_fields.append("Impact: Mild inconvenience")
    elif any(w in text for w in ["none", "no impact", "didn't affect"]):
        impact = "None"
        parsed_fields.append("Impact: None")
    else:
        parsed_fields.append("Impact: Normal activities modified (default)")

    # 5. Status Extraction
    status = "Ongoing"
    if any(w in text for w in ["resolved", "better now", "went away", "passed", "stopped", "finished"]):
        status = "Resolved"
        parsed_fields.append("Status: Resolved")
    elif any(w in text for w in ["comes and goes", "intermittent", "periodic"]):
        status = "Intermittent"
        parsed_fields.append("Status: Intermittent")
    else:
        parsed_fields.append("Status: Ongoing")

    # 6. Context Extraction (Sleep, Stress, Menstrual Context)
    context = {}
    if any(w in text for w in ["insomnia", "couldn't sleep", "bad sleep", "poor sleep", "slept poorly", "<5 hrs", "less than 5 hours"]):
        context["sleep"] = "Poor (< 5 hrs)"
        parsed_fields.append("Sleep Context: Poor (< 5 hrs)")
    elif any(w in text for w in ["disrupted sleep", "woke up", "fragmented sleep", "restless"]):
        context["sleep"] = "Disrupted / Fragmented"
        parsed_fields.append("Sleep Context: Disrupted / Fragmented")
    elif any(w in text for w in ["slept well", "good sleep", "restful"]):
        context["sleep"] = "Restful (> 7 hrs)"
        parsed_fields.append("Sleep Context: Restful (> 7 hrs)")

    if any(w in text for w in ["overwhelmed", "extreme stress", "panic", "terrible stress"]):
        context["stress"] = "High / Pressured"
        parsed_fields.append("Stress Context: High / Pressured")
    elif any(w in text for w in ["high stress", "pressured", "stressed", "work stress", "stress"]):
        context["stress"] = "High / Pressured"
        parsed_fields.append("Stress Context: High / Pressured")
    elif any(w in text for w in ["calm", "relaxed", "low stress"]):
        context["stress"] = "Low / Relaxed"
        parsed_fields.append("Stress Context: Low / Relaxed")

    if any(w in text for w in ["luteal", "before period", "pms", "pre-menstrual"]):
        context["cycle_phase"] = "Luteal Phase"
        parsed_fields.append("Cycle Context: Luteal Phase")
    elif any(w in text for w in ["period", "menstrual", "bleeding"]):
        context["cycle_phase"] = "Menstrual Phase"
        parsed_fields.append("Cycle Context: Menstrual Phase")
    elif any(w in text for w in ["ovulation", "mid cycle"]):
        context["cycle_phase"] = "Ovulation"
        parsed_fields.append("Cycle Context: Ovulation")
    elif any(w in text for w in ["follicular", "after period"]):
        context["cycle_phase"] = "Follicular Phase"
        parsed_fields.append("Cycle Context: Follicular Phase")

    return {
        "symptom": matched_symptom,
        "category": matched_category,
        "severity": severity,
        "duration_hours": duration_hours,
        "onset_date": default_date or str(date.today()),
        "status": status,
        "impact": impact,
        "notes": raw,
        "context": context,
        "parsed_fields": parsed_fields,
        "raw_transcript": raw
    }


def get_web_speech_component_js() -> str:
    """
    Returns embedded JavaScript/HTML for browser-based Web Speech API with
    fallback text-input guidance.
    """
    return """
    <script>
    function startVoiceRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            alert("Speech recognition is not supported in this browser. Please use the text input below.");
            return;
        }
        const recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;
        
        const btn = document.getElementById('voice-rec-btn');
        if (btn) btn.innerText = '🔴 Listening... Speak clearly now';
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            const targetInput = window.parent.document.querySelector('textarea[aria-label="Spoken Observation or Text Notes"]');
            if (targetInput) {
                targetInput.value = transcript;
                targetInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
            if (btn) btn.innerText = '🎙️ Start Voice Recording';
        };
        
        recognition.onerror = function(event) {
            if (btn) btn.innerText = '🎙️ Start Voice Recording';
            alert('Voice recognition note: ' + event.error + '. You can type directly in the box below.');
        };
        
        recognition.start();
    }
    </script>
    """
