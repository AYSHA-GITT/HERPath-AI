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
| **1. Authentication & Onboarding** | Dedicated Login & Registration portal for new & existing users, salted SHA-256 PIN security, custom health focus tags, cycle tracking toggle, and 1-click demo persona access. | ✅ Complete |
| **2. Multi-Profile & Privacy** | Local profile creation, pseudonyms, isolated records, optional menstrual tracking preference, user-controlled data erasure. | ✅ Complete |
| **3. Smart Symptom Journal** | Full CRUD: Record, edit, delete, view, and filter symptoms. Captures category, severity (1–10), duration, onset date/time, functional impact, and sleep/stress context. | ✅ Complete |
| **4. Medication & Treatments** | Track prescriptions, OTC supplements, and lifestyle therapies (dosage, frequency, started date) linked with active profiles. | ✅ Complete |
| **5. Timeline Intelligence** | Interactive chronological health journey: multi-dimensional filters (date range presets, custom dates, categories, symptoms, severity slider, event types), dual-period symptom comparison with observation rate per day, explainable rule-based pattern insights, and 3 Plotly charts (severity trajectory, unified event swimlane, contextual co-occurrence). | ✅ Complete |
| **6. Smart Clinical Summary** | Converts actual health history into a structured, doctor-ready consultation briefing: 6 dedicated sections (Overview, Symptom Patterns & Trajectory, Lifestyle & Functional Impact, Treatment Chronology with neutral non-causal phrasing, Patient Concerns, and Doctor Discussion Checklist), multi-preset reporting periods (7d, 30d, 90d, custom), 1-click clipboard plain-text export, and 1–2 page professional PDF compilation. | ✅ Complete |
| **7. Personal Health Insights** | Interactive Plotly timelines, symptom frequency distributions, contextual comparisons, co-occurrence heatmaps, and explainable pattern statements. | ✅ Complete |
| **8. Doctor Consultation Kit** | Interactive 10-minute visit prep tool generating opening statements and evidence-grounded questions tailored to appointment goals. | ✅ Complete |
| **9. Care Guidance & Safety** | Transparent rule-based clinical triage hierarchy (Emergency, Prompt, Routine, Self-Care) plus Regional Emergency SOS Helplines (112, 1091, 181, 911, 999). | ✅ Complete |
| **10. Verified Health Library** | Searchable directory of peer-reviewed educational articles from WHO, NHS, CDC, ACOG, and Mayo Clinic. | ✅ Complete |
| **11. Clinician Health Report** | ReportLab PDF generator compiling structured clinical summaries, observation tables, active medications, trajectories, and physician discussion questions. | ✅ Complete |
| **12. Data Portability & Backup** | Privacy-first data portability: One-click complete JSON backup export, spreadsheet CSV export, and JSON restore functionality. | ✅ Complete |
| **13. Ask HERPath Assistant** | Grounded health literacy search over curated medical literature with strict non-diagnostic boundaries and emergency overrides. | ✅ Complete |


---

## 4. Technical Architecture

HERPath AI adopts a clean, layered modular architecture separating presentation, service operations, deterministic safety protocols, analytics engines, and relational storage.

```
HERPath-AI/
├── app.py                     # Streamlit frontend & interactive navigation
├── auth.py                    # Privacy-first salted SHA-256 auth & user registration
├── config.py                  # Taxonomy, clinical constants, and color tokens
├── database.py                # SQLite WAL connection management & scoped CRUD
├── models.py                  # UserProfile, SymptomEntry & Medication dataclasses
├── validators.py              # Input validation and bounds checking
├── symptom_tracker.py         # Business logic service layer
├── timeline_service.py        # HERPath Timeline Intelligence & period analytics engine
├── clinical_summary_service.py# Smart Clinical Summary synthesis & consultation engine
├── insights_engine.py         # Statistical analysis & Plotly visualization engine
├── safety_navigator.py        # Rule-based clinical triage hierarchy
├── health_library.py          # Evidence-based health education search
├── report_generator.py        # ReportLab PDF clinical export compiler
├── requirements.txt           # Python dependencies
├── .env.example               # Environment template
├── .gitignore                 # Excludes local databases, caches, and secrets
├── assets/
│   └── styles.css             # Custom design system, timeline components & iOS shell
├── data/
│   ├── health_resources.json  # Curated literature from WHO, NHS, CDC, ACOG
│   └── seed_data.py           # Realistic, fictional demonstration data seeder
├── tests/
│   ├── test_auth.py           # Salted PIN hashing & user registration unit tests
│   ├── test_database.py       # Persistence, CRUD, isolation & cascade tests
│   ├── test_validators.py     # Input boundary & sanitization tests
│   ├── test_timeline.py       # HERPath Timeline Intelligence comprehensive test suite
│   ├── test_clinical_summary.py # Smart Clinical Summary & consultation kit tests
│   ├── test_insights.py       # Math accuracy & non-diagnostic constraint tests
│   ├── test_safety.py         # Clinical triage & emergency override tests
│   ├── test_reports.py        # PDF compilation & rendering tests
│   ├── test_backend_e2e.py    # Service layer & data pipeline integration tests
│   ├── test_frontend_e2e.py   # Streamlit AppTest UI interaction & auth tests
│   └── test_mobile_redesign.py# Mobile bottom bar & form flow tests
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
- **Authentication & Security:** Salted SHA-256 PIN/password hashing with on-device SQLite storage.
- **Database:** SQLite 3 with Write-Ahead Logging (WAL) and foreign-key cascade enforcement.
- **Analytics & Data Handling:** [Pandas](https://pandas.pydata.org/) and NumPy.
- **Interactive Visualizations:** [Plotly](https://plotly.com/python/) (Scatter timelines, bar charts).
- **Document Generation:** [ReportLab](https://www.reportlab.com/) (Vector-based PDF compilation).
- **Automated Testing:** [pytest](https://docs.pytest.org/) (99 comprehensive unit, integration & AppTest E2E tests).

---

## 6. Installation & Setup

### Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- Git

### Step-by-Step Installation

```bash
# 1. Clone repository
git clone https://github.com/AYSHA-GITT/HERPath-AI.git
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

### Verified Test Coverage (82/82 Passed):
- **Timeline Intelligence (`test_timeline.py`):** Verified chronological sorting, date-range filtering, category & symptom filtering, severity sliders, missing values handling without zero-coercion, dual-period comparison with observation rates per day, empty periods, sleep/stress contextual thresholds, profile isolation, medication grounding, and Plotly figure generation.
- **Frontend End-to-End (`test_frontend_e2e.py`):** Verified rendering, navigation, form inputs, triage emergency cards, library search, and report download buttons across all views using Streamlit AppTest.
- **Mobile Redesign (`test_mobile_redesign.py`):** Verified iOS bottom tab bar, quick logging flows, and single-column mobile layout.
- **Authentication & Security (`test_auth.py`):** Verified salted SHA-256 PIN security, new user registration, profile isolation, and login authentication.
- **Backend End-to-End (`test_backend_e2e.py`):** Verified full profile lifecycle, zero cross-profile data leakage, analytics mathematical precision, triage rule hierarchy, and ReportLab PDF compilation.
- **Database (`test_database.py`):** Profile isolation, symptom CRUD, update persistence, cascade profile deletion, foreign-key integrity.
- **Validators (`test_validators.py`):** Severity bounds (1–10), duration limits (<=720h), future date handling, sanitization.
- **Insights (`test_insights.py`):** Zero division protection, null duration handling (not treating missing as 0), non-diagnostic constraint verification.
- **Safety Navigator (`test_safety.py`):** Self-care baseline, routine consultation, prompt medical evaluation (24-48h), emergency warning overrides, non-diagnostic boundaries.
- **Report Generator (`test_reports.py`):** Valid PDF byte stream generation for empty, single, and multi-entry records.

---

## 9. HERPath Timeline Intelligence & Dual-Period Analytics

**HERPath Timeline Intelligence** unifies the user's recorded health observations and interventions into an interactive, explainable, and privacy-preserving chronological stream.

### Key Capabilities:
1. **Unified Chronological Health Journey:** Seamlessly interleaves symptom episodes with medication starts, recorded severity (1–10), duration, functional impact, and sleep/stress context.
2. **Multi-Dimensional Interactive Filtering:**
   - **Date Presets & Custom Ranges:** Quick toggles for *Last 7 Days*, *Last 30 Days*, *Last 90 Days*, *All Time*, or custom date boundaries.
   - **Category & Specific Symptom Filtering:** Multi-select filtering across anatomical and physiological symptom taxonomy.
   - **Severity Slider (1–10):** Focus on mild, moderate, or severe episodes.
   - **Event Types:** Filter by Symptoms, Medications, Sleep Context, Stress Context, or Functional Disruption.
   - **Reset Filter Action & Empty State:** Graceful handling when no records match filter criteria.
3. **Dual-Period Comparison Analytics:**
   - Compares two date ranges (e.g., *Recent 30 Days vs. Previous 30 Days* or custom periods).
   - Calculates raw episode shifts, observation rates per day (accounting for unequal period lengths), average severity deltas, peak severity, and average duration shifts.
   - Interactive grouped Plotly bar chart comparing episodes and severity.
   - Symptom-by-symptom comparative breakdown table.
4. **Explainable Health Pattern Insights:**
   - Rule-based analysis layer grounded exclusively in verified database values.
   - Every insight displays the observation, exact evidence count, date range, mathematical formula, and clinical safety limitation disclaimer.
   - **Medical Safety Rules:** Strict refusal to infer clinical diagnoses or declare physiological causation (*"co-occurred with"*, *"was recorded alongside"*).
5. **Interactive Plotly Visualizations:**
   - **Symptom Severity Timeline:** Scatter and spline trajectory against real dates with color-coded severity zones (Mild, Moderate, Severe).
   - **Unified Event Swimlane:** Chronological multi-track view of symptoms, medication start dates, and functional disruptions.
   - **Contextual Sleep Comparison:** Severity distribution across reported sleep quality tiers when sufficient data exists ($n \ge 3$).
6. **Chronological Event Feed & Detail View:**
   - Expandable event cards with severity pills, impact badges, sleep/stress ratings, medication dosages, and notes.
   - Integrated with existing CRUD services, enabling direct 1-click editing in the Symptom Journal.

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
