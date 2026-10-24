# HERPath AI — Women's Health Intelligence & Care Navigation Platform
### *Understand your symptoms. Discover patterns. Take informed next steps.*

**Event:** recHERsion 2026 | Organized by ACM-W, NITK Surathkal  
**Problem Statement:** PS1 — Women's Healthcare  
**Author:** Full-Stack Health Intelligence Engineering Team

---

## 1. Problem Statement

Women's health challenges are frequently compounded by systemic barriers:
- **Diagnostic Delays:** Conditions such as endometriosis (averaging 7–10 years before diagnosis), polycystic ovary syndrome (PCOS), perimenopause, and autoimmune disorders face normalization or dismissal of symptoms.
- **Symptom Recall & Consultation Burden:** Clinical consultations typically last 10–15 minutes, leaving patients overwhelmed and unable to accurately reconstruct the timeline, severity, and functional impact of fluctuating symptoms.
- **Oversimplified Tracking Tools:** Most market solutions function strictly as calendar-based period trackers, failing to capture holistic symptoms such as hormonal migraines, chronic fatigue, pelvic pain, anemia indicators, and mood disruption.
- **Medical Misinformation:** Online symptom searches often lead to anxiety-inducing, inaccurate, or unverified claims.
- **Ambiguity in Care Navigation:** Users struggle to identify when symptoms warrant routine discussion versus prompt or emergency medical evaluation.

---

## 2. Proposed Solution

**HERPath AI** is an on-device, privacy-conscious digital health intelligence platform that empowers women to systematically capture health observations across multiple physiological systems, uncover explainable patterns without black-box diagnostic claims, receive transparent rule-based care navigation, and generate clinician-ready consultation reports.

### Key Pillars
- **Beyond Period Tracking:** Multi-system coverage including pelvic, neurological, systemic, breast, urinary, metabolic, and mental wellbeing observations.
- **Explainable Health Analytics:** Deterministic statistical insights grounded strictly in real database records, identifying trajectories and contextual co-occurrences.
- **Deterministic Care Navigator:** Hardcoded triage hierarchy prioritizing critical red flags based on WHO, ACOG, and NHS guidance.
- **Clinician-Ready PDF Exports:** Instant generation of structured consultation summaries using ReportLab.
- **Privacy by Architecture:** 100% on-device SQLite storage with zero third-party cloud data transmission.

---

## 3. Features Implemented

| Module | Core Functionality | Status |
|---|---|:---:|
| **1. Multi-Profile & Privacy** | Local profile creation, pseudonyms, isolated records, optional menstrual tracking preference, user-controlled data erasure. | ✅ Complete |
| **2. Smart Symptom Journal** | Full CRUD: Record, edit, delete, view, and filter symptoms. Captures category, severity (1–10), duration, onset date/time, functional impact, and sleep/stress context. | ✅ Complete |
| **3. Personal Health Insights** | Interactive Plotly timelines, symptom frequency distributions, contextual comparisons, and explainable pattern statements based strictly on database records. | ✅ Complete |
| **4. Care Guidance & Safety** | Transparent rule-based clinical triage hierarchy: Emergency Evaluation, Prompt Medical Review (24–48h), Routine Consultation, and Supportive Self-Care. | ✅ Complete |
| **5. Verified Health Library** | Searchable directory of peer-reviewed educational articles from WHO, NHS, CDC, ACOG, and Mayo Clinic. | ✅ Complete |
| **6. Clinician Health Report** | ReportLab PDF generator compiling structured clinical summaries, observation tables, trajectories, and physician discussion questions. | ✅ Complete |
| **7. Ask HERPath Assistant** | Grounded health literacy search over curated medical literature with strict non-diagnostic boundaries and emergency overrides. | ✅ Complete |

---

## 4. Technical Architecture

HERPath AI adopts a clean, layered modular architecture separating presentation, service operations, deterministic safety protocols, analytics engines, and relational storage.

```
HERPath-AI/
├── app.py                     # Streamlit frontend & interactive navigation
├── config.py                  # Taxonomy, clinical constants, and color tokens
├── database.py                # SQLite WAL connection management & scoped CRUD
├── models.py                  # UserProfile & SymptomEntry dataclasses
├── validators.py              # Input validation and bounds checking
├── symptom_tracker.py         # Business logic service layer
├── insights_engine.py         # Statistical analysis & Plotly visualization engine
├── safety_navigator.py        # Rule-based clinical triage hierarchy
├── health_library.py          # Evidence-based health education search
├── report_generator.py        # ReportLab PDF clinical export compiler
├── requirements.txt           # Python dependencies
├── .env.example               # Environment template
├── .gitignore                 # Excludes local databases, caches, and secrets
├── assets/
│   └── styles.css             # Custom design system (lavender, warm white, teal, rose)
├── data/
│   ├── health_resources.json  # Curated literature from WHO, NHS, CDC, ACOG
│   └── seed_data.py           # Realistic, fictional demonstration data seeder
├── tests/
│   ├── test_database.py       # Persistence, CRUD, isolation & cascade tests
│   ├── test_validators.py     # Input boundary & sanitization tests
│   ├── test_insights.py       # Math accuracy & non-diagnostic constraint tests
│   ├── test_safety.py         # Clinical triage & emergency override tests
│   └── test_reports.py        # PDF compilation & rendering tests
└── docs/
    ├── architecture.md        # Detailed system design & schema documentation
    ├── testing.md             # Verification test suite breakdown
    ├── presentation.md        # 8-slide hackathon presentation outline
    └── demo_video_script.md   # 3-minute video walkthrough sequence
```

---

## 5. Technology Stack

- **Frontend & Navigation:** [Streamlit](https://streamlit.io/) (v1.35+) with custom CSS design tokens.
- **Backend & Logic:** Python 3.13 (Modular service architecture).
- **Database:** SQLite 3 with Write-Ahead Logging (WAL) and foreign-key cascade enforcement.
- **Analytics & Data Handling:** [Pandas](https://pandas.pydata.org/) and NumPy.
- **Interactive Visualizations:** [Plotly](https://plotly.com/python/) (Scatter timelines, bar charts).
- **Document Generation:** [ReportLab](https://www.reportlab.com/) (Vector-based PDF compilation).
- **Automated Testing:** [pytest](https://docs.pytest.org/) (28 comprehensive unit tests).

---

## 6. Installation & Setup

### Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- Git

### Step-by-Step Installation

```bash
# 1. Clone repository
git clone https://github.com/ayesha-sharief/HERPath-AI.git
cd HERPath-AI

# 2. (Optional) Create and activate a virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 7. Running the Application

Launch the Streamlit web application:

```bash
python -m streamlit run app.py
```

The application will be accessible in your web browser at:
```
http://localhost:8501
```

---

## 8. Database Initialization & Demonstration Data

The SQLite database schema automatically initializes on the first run of `app.py`.

To seed realistic, completely fictional demonstration data across the three demonstration personas (*Priya - PCOS & Migraines*, *Ananya - Perimenopause*, *Elena - Endometriosis*), run:

```bash
python data/seed_data.py
```

You can also reload demonstration data at any time directly within the UI under **Privacy and Settings -> Reload Fictional Demo Data**.

---

## 9. Automated Testing & Verification

Execute the complete automated test suite:

```bash
python -m pytest -v tests/
```

### Verified Test Coverage (28/28 Passed):
- **Database (`test_database.py`):** Profile isolation, symptom CRUD, update persistence, cascade profile deletion, foreign-key integrity.
- **Validators (`test_validators.py`):** Severity bounds (1–10), duration limits (<=720h), future date handling, sanitization.
- **Insights (`test_insights.py`):** Zero division protection, null duration handling (not treating missing as 0), non-diagnostic constraint verification.
- **Safety Navigator (`test_safety.py`):** Self-care baseline, routine consultation, prompt medical evaluation (24-48h), emergency warning overrides, non-diagnostic boundaries.
- **Report Generator (`test_reports.py`):** Valid PDF byte stream generation for empty, single, and multi-entry records.

---

## 10. Privacy & Responsible Medical Design

1. **On-Device Storage Only:** All health observations, notes, and profiles are saved exclusively in a local SQLite file (`data/herpath.db`). No health records are sent to remote servers or third-party cloud services.
2. **Zero Third-Party Telemetry:** No user analytics, advertising trackers, or fingerprinting scripts are embedded.
3. **No Unvalidated Clinical Claims:** HERPath AI strictly refuses to output definitive disease diagnoses (e.g. *"You have PCOS"*). It presents explainable observational statements with explicit caveats (*"These entries show a possible association, not proof of causation"*).
4. **Emergency Priority Isolation:** Red-flag symptoms (such as thunderclap headaches, severe pelvic collapse, or hemorrhagic blood loss) immediately route the user to emergency services and cannot be bypassed or delayed by language models.

---

## 11. Known Limitations & Future Enhancements

### Current Prototype Limitations
- **Local Single-Device Prototype:** Designed for local evaluation; does not include enterprise multi-tenant cloud authentication.
- **Non-Diagnostic:** Provides organized personal documentation and triage guidance, not clinical diagnoses or prescription recommendations.
- **Manual Input:** Requires user recording of symptoms rather than automated passive biometric telemetry.

### Future Enhancements Roadmap
- **At-Rest Database Encryption:** Integration with SQLCipher for AES-256 local database encryption.
- **Wearable Device Integration:** Apple HealthKit and Fitbit APIs for passive resting heart rate and sleep staging telemetry.
- **EHR Interoperability:** FHIR (Fast Healthcare Interoperability Resources) JSON export for direct transmission into clinical hospital systems.
- **Multilingual Support:** Localization into Hindi, Kannada, Tamil, Spanish, and French for wider health equity.

---

## 12. Acknowledgments & Citations

Educational literature and clinical guidance in HERPath AI are referenced from:
- **World Health Organization (WHO):** PCOS and Endometriosis Fact Sheets.
- **National Health Service (NHS UK):** Iron Deficiency Anaemia & Menstrual Health Guidelines.
- **American College of Obstetricians and Gynecologists (ACOG):** Abnormal Uterine Bleeding FAQs.
- **Centers for Disease Control and Prevention (CDC):** Breast Health Awareness.
- **Mayo Clinic & Johns Hopkins Medicine:** Migraine and Urinary Tract Health Clinical References.

---

**Developed for recHERsion 2026 | ACM-W, NITK Surathkal**
