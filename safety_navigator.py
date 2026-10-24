"""
HERPath AI - Care Guidance & Safety Navigator
recHERsion 2026 | PS1: Women's Healthcare

Rule-based clinical triage navigator based on established public health guidelines
(ACOG, NHS, WHO, CDC). This module is strictly non-diagnostic and prioritizes
patient safety through transparent, explainable triage hierarchy.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from config import (
    PRIORITY_EMERGENCY,
    PRIORITY_PROMPT,
    PRIORITY_ROUTINE,
    PRIORITY_SELFCARE,
    CLINICAL_DISCLAIMER,
    EMERGENCY_NOTICE
)


@dataclass
class SafetyAssessment:
    priority: str  # EMERGENCY_EVALUATION | PROMPT_EVALUATION | ROUTINE_CONSULTATION | HEALTH_EDUCATION
    title: str
    headline: str
    rationale: List[str]
    recommended_actions: List[str]
    educational_topics: List[str] = field(default_factory=list)
    emergency_contact: Optional[str] = None
    disclaimer: str = CLINICAL_DISCLAIMER


class SafetyNavigator:
    """
    Transparent, rule-based care navigator that evaluates user-reported symptoms
    and warning flags to prioritize safe, timely clinical navigation.
    """

    # Configured Critical Emergency Warning Signs
    EMERGENCY_TRIGGERS = [
        {
            "id": "em-01",
            "trigger_name": "Acute Chest Pain / Respiratory Distress",
            "keywords": ["chest pain", "shortness of breath", "difficulty breathing", "pressure in chest"],
            "severity_min": 7,
            "headline": "Potential Cardiovascular or Respiratory Emergency",
            "rationale": "Severe acute chest discomfort or acute shortness of breath requires immediate emergency clinical evaluation.",
            "actions": [
                "Call local emergency services immediately (112 / 911 / 999).",
                "Do not drive yourself to the emergency department; request emergency medical transit.",
                "Sit in a comfortable, upright resting position while awaiting assistance."
            ]
        },
        {
            "id": "em-02",
            "trigger_name": "Thunderclap Headache / Neurological Deficits",
            "keywords": ["worst headache of life", "thunderclap", "facial droop", "slurred speech", "sudden vision loss", "numbness one side"],
            "severity_min": 8,
            "headline": "Urgent Neurological Warning Sign",
            "rationale": "Headache reaching peak intensity within seconds ('thunderclap') or accompanied by focal neurological signs (speech changes, facial droop, sudden loss of vision) requires urgent emergency evaluation.",
            "actions": [
                "Seek immediate emergency medical attention at the nearest emergency department.",
                "Note the exact time symptoms started to inform emergency triage clinicians."
            ]
        },
        {
            "id": "em-03",
            "trigger_name": "Severe Acute Pelvic Pain with Dizziness or Faintness",
            "keywords": ["acute pelvic pain", "fainting", "dizziness", "shoulder tip pain", "severe pelvic cramps"],
            "severity_min": 8,
            "headline": "Possible Acute Pelvic Emergency",
            "rationale": "Sudden, severe pelvic or abdominal pain accompanied by dizziness, faintness, or pallor may indicate internal bleeding, ectopic pregnancy, or ovarian torsion.",
            "actions": [
                "Proceed immediately to the nearest hospital emergency room.",
                "Inform medical staff if there is any possibility of pregnancy or recent pelvic procedures."
            ]
        },
        {
            "id": "em-04",
            "trigger_name": "Hemorrhagic Menstrual Bleeding with Signs of Shock",
            "keywords": ["soaking two pads per hour", "large blood clots", "lightheadedness", "fainting with bleeding"],
            "severity_min": 7,
            "headline": "Severe Acute Blood Loss Warning",
            "rationale": "Soaking through two or more maxi pads or tampons per hour for consecutive hours accompanied by dizziness or pale skin requires immediate emergency care.",
            "actions": [
                "Seek immediate emergency medical evaluation.",
                "Stay seated or lying down to reduce fall risks from orthostatic hypotension."
            ]
        }
    ]

    # Prompt Medical Evaluation (Within 24-48 Hours)
    PROMPT_TRIGGERS = [
        {
            "id": "pr-01",
            "trigger_name": "New Distinct Breast Lump or Nipple Changes",
            "keywords": ["breast lump", "nipple discharge", "skin dimpling", "inverted nipple"],
            "headline": "Prompt Clinical Breast Evaluation Needed",
            "rationale": "Any new distinct breast lump, localized skin tethering, or bloody nipple discharge requires clinical physical examination and breast imaging (ultrasound/mammogram).",
            "actions": [
                "Schedule a clinical evaluation with your primary physician or gynecologist within 24 to 48 hours.",
                "Avoid repeated aggressive palpation of the tissue."
            ],
            "topics": ["Breast Health"]
        },
        {
            "id": "pr-02",
            "trigger_name": "Dysuria with Flank Pain or Fever",
            "keywords": ["burning urination", "flank pain", "back pain with urination", "chills and urine burn"],
            "headline": "Potential Upper Urinary Tract Involvement",
            "rationale": "Urinary symptoms accompanied by back/flank pain, chills, or fever may suggest pyelonephritis (kidney infection) requiring prompt prescription antimicrobial therapy.",
            "actions": [
                "Contact a doctor or urgent care clinic for a urinalysis and urine culture today.",
                "Maintain adequate fluid hydration."
            ],
            "topics": ["Urinary Health"]
        },
        {
            "id": "pr-03",
            "trigger_name": "Post-Menopausal Bleeding",
            "keywords": ["post-menopausal bleeding", "bleeding after menopause", "spotting after 12 months no period"],
            "headline": "Prompt Gynecological Assessment Required",
            "rationale": "Any vaginal bleeding or spotting occurring more than 12 months after the cessation of menstrual cycles requires clinical investigation to examine endometrial thickness.",
            "actions": [
                "Schedule a gynecological appointment for an evaluation and pelvic ultrasound.",
                "Record the exact frequency and volume of spotting."
            ],
            "topics": ["Menopause", "Menstrual Health"]
        },
        {
            "id": "pr-04",
            "trigger_name": "High Severity Persistent Pain (Severity >= 8)",
            "headline": "Severe Pain Requiring Professional Evaluation",
            "rationale": "Symptom severity recorded at 8 or above significantly impairs functioning and warrants clinical assessment.",
            "actions": [
                "Consult a licensed medical provider promptly.",
                "Prepare your HERPath clinician report summarizing your symptom history."
            ],
            "topics": ["Endometriosis Education", "Pelvic & Menstrual"]
        }
    ]

    @classmethod
    def evaluate(
        cls,
        symptom: str,
        category: str,
        severity: int,
        duration_hours: Optional[float] = None,
        notes: str = "",
        red_flags_checked: Optional[List[str]] = None
    ) -> SafetyAssessment:
        """
        Evaluates symptom characteristics and user-selected warning flags
        against deterministic clinical safety rules.
        """
        red_flags = red_flags_checked or []
        combined_text = f"{symptom} {category} {notes} {' '.join(red_flags)}".lower()

        # Step 1: Check EMERGENCY TRIGGERS
        # Rule 1a: User explicitly checked an emergency flag
        explicit_emergency = any("emergency" in flag.lower() or "faint" in flag.lower() or "worst headache" in flag.lower() for flag in red_flags)
        
        for em in cls.EMERGENCY_TRIGGERS:
            matched_keywords = [kw for kw in em["keywords"] if kw in combined_text]
            if (matched_keywords and severity >= em["severity_min"]) or explicit_emergency:
                return SafetyAssessment(
                    priority=PRIORITY_EMERGENCY,
                    title="EMERGENCY MEDICAL EVALUATION RECOMMENDED",
                    headline=em["headline"],
                    rationale=[
                        em["rationale"],
                        f"Reported symptom severity: {severity}/10.",
                        f"Detected indicators: {', '.join(matched_keywords) if matched_keywords else 'Urgent clinical warning signs selected.'}"
                    ],
                    recommended_actions=em["actions"],
                    educational_topics=["General Wellbeing & Sleep"],
                    emergency_contact="Emergency Contact: 112 (India) / 911 (US) / 999 (UK) or your local hospital emergency room."
                )

        # Step 2: Check PROMPT EVALUATION TRIGGERS (within 24-48 hours)
        for pr in cls.PROMPT_TRIGGERS:
            keywords = pr.get("keywords", [])
            matched = [kw for kw in keywords if kw in combined_text]
            if matched or (pr.get("id") == "pr-04" and severity >= 8):
                return SafetyAssessment(
                    priority=PRIORITY_PROMPT,
                    title="PROMPT MEDICAL EVALUATION RECOMMENDED (24–48 Hours)",
                    headline=pr["headline"],
                    rationale=[
                        pr["rationale"],
                        f"Recorded symptom severity is {severity}/10."
                    ],
                    recommended_actions=pr["actions"],
                    educational_topics=pr.get("topics", ["General Wellbeing & Sleep"])
                )

        # Step 3: Check ROUTINE CLINICAL CONSULTATION
        # Symptoms that are moderate (severity 4-7) or long duration / recurrent
        if severity >= 4 or (duration_hours and duration_hours > 48):
            rationale_points = [
                f"Symptom severity recorded as {severity}/10, indicating notable interference with daily comfort or activities.",
                "While no acute emergency flags were detected in this entry, persistent or recurrent symptoms warrant a structured medical review."
            ]
            if duration_hours and duration_hours > 48:
                rationale_points.append(f"Recorded duration has exceeded {duration_hours:.0f} hours.")

            return SafetyAssessment(
                priority=PRIORITY_ROUTINE,
                title="ROUTINE CLINICAL CONSULTATION RECOMMENDED",
                headline="Discuss These Observations with Your Healthcare Provider",
                rationale=rationale_points,
                recommended_actions=[
                    "Schedule an outpatient appointment with your gynecologist or primary care physician.",
                    "Export and bring your HERPath Clinician Health Report to your consultation.",
                    "Track any triggers, cycle timing, and symptom duration in your journal leading up to your visit."
                ],
                educational_topics=[category]
            )

        # Step 4: HEALTH EDUCATION & SUPPORTIVE SELF-CARE (Mild symptoms 1-3)
        return SafetyAssessment(
            priority=PRIORITY_SELFCARE,
            title="GENERAL HEALTH EDUCATION & SELF-CARE MONITORING",
            headline="Mild Symptom Observation",
            rationale=[
                f"Reported severity is mild ({severity}/10) with no urgent warning signs detected.",
                "Observations at this stage are valuable for tracking baseline patterns over time."
            ],
            recommended_actions=[
                "Continue logging symptoms in your journal if they change in frequency or intensity.",
                "Consider supportive self-care: adequate hydration, restful sleep, and gentle movement.",
                "Consult a healthcare professional if symptoms worsen, persist, or cause concern."
            ],
            educational_topics=[category]
        )

    @classmethod
    def get_supported_emergency_warning_signs(cls) -> List[Dict[str, str]]:
        """Returns standard warning signs for educational checklist."""
        return [
            {"id": "wf-1", "label": "Sudden onset 'worst headache of life' (thunderclap)", "level": "Emergency"},
            {"id": "wf-2", "label": "Acute chest pressure, shortness of breath, or sudden fainting", "level": "Emergency"},
            {"id": "wf-3", "label": "Severe acute lower abdominal / pelvic pain with dizziness", "level": "Emergency"},
            {"id": "wf-4", "label": "Soaking 2+ pads/tampons per hour consecutively with lightheadedness", "level": "Emergency"},
            {"id": "wf-5", "label": "New distinct breast lump, nipple inversion, or discharge", "level": "Prompt"},
            {"id": "wf-6", "label": "Burning during urination with back / flank pain or fever", "level": "Prompt"},
            {"id": "wf-7", "label": "Vaginal bleeding >12 months after menopause", "level": "Prompt"}
        ]
