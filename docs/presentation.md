# HERPath AI — Hackathon Presentation Outline
## recHERsion 2026 | PS1: Women's Healthcare
**Organized by:** ACM-W, NITK Surathkal  
**Project:** HERPath AI — Women's Health Intelligence & Care Navigation Platform  
**Tagline:** Understand your symptoms. Discover patterns. Take informed next steps.

---

### Slide 1 — Title & Identity
- **Project Title:** HERPath AI
- **Subtitle:** Women's Health Intelligence & Care Navigation Platform
- **Tagline:** *Understand your symptoms. Discover patterns. Take informed next steps.*
- **Event:** recHERsion 2026 | Problem Statement 1: Women's Healthcare
- **Host Institution:** ACM-W, National Institute of Technology Karnataka (NITK), Surathkal
- **Core Concept:** A privacy-conscious digital health companion that helps women systematically track health observations, discover explainable patterns, navigate clinical care safely, and generate clinician-ready health reports.

---

### Slide 2 — The Problem & Real Challenges
- **Diagnostic Delay & Symptom Normalization:** Conditions like endometriosis (7-10 year average delay), PCOS, and perimenopause suffer from systemic under-investigation and dismissal of symptoms.
- **Symptom Recall Burden:** During brief 10-15 minute clinical consultations, patients struggle to recall exact symptom timelines, onset dates, and severity trajectories.
- **Fragmented Health Tracking:** Existing apps focus almost exclusively on menstrual cycle tracking or ovulation, ignoring migraines, fatigue, iron deficiency, pelvic floor health, and mood changes.
- **Medical Misinformation:** Online searches frequently escalate user anxiety with alarmist, unvetted diagnoses or unverified supplements.

---

### Slide 3 — Target Users & Proposed Solution
- **Who Is It For?**
  - Women managing chronic or recurrent symptoms (migraines, severe pelvic discomfort, unexplained fatigue).
  - Individuals navigating transitional health phases (perimenopause, post-menopause, PCOS).
  - Anyone seeking structured documentation to advocate for their health during doctor visits.
- **The HERPath AI Solution:**
  - **Holistic Symptom Journal:** Multi-system tracking (neurological, systemic, pelvic, urinary, mental wellbeing) with optional menstrual context.
  - **Explainable Pattern Discovery:** Deterministic statistics that highlight observable correlations without fabricating medical diagnoses.
  - **Rule-Based Care Navigator:** Public health triage framework (WHO/ACOG/NHS) prioritizing urgent warning signs.
  - **Clinician-Ready Health Reports:** Instant PDF summary exports structured for doctors.

---

### Slide 4 — Functional Features & End-to-End Workflow
1. **Local Profile Selection:** Switch between user profiles with distinct isolated health histories and customizable tracking preferences.
2. **Smart Symptom Journal:** Log onset date, severity (1-10), duration, daily impact, sleep quality, and stress levels with instant database persistence.
3. **Personal Health Insights:** Interactive Plotly timelines and explainable pattern statements based strictly on database records.
4. **Care Guidance & Safety Navigator:** Real-time triage evaluation with transparent rationales and emergency warning flags.
5. **Verified Women's Health Library:** Searchable evidence-based guides from WHO, NHS, CDC, ACOG, and Mayo Clinic.
6. **Clinician Report Generator:** One-click ReportLab PDF export complete with doctor discussion points.

---

### Slide 5 — Technical Architecture & Data Flow
- **Presentation Layer:** Streamlit with custom responsive CSS (soft lavender `#7B61FF`, muted teal `#2A9D8F`, subtle rose `#E76F7C`).
- **Application Services:** Modular Python architecture (`symptom_tracker.py`, `insights_engine.py`, `safety_navigator.py`, `health_library.py`, `report_generator.py`).
- **Data Persistence:** SQLite with WAL mode, parameterized queries, and strict profile-scoped data isolation.
- **Analytics & Visualizations:** Pandas and Plotly for responsive, client-side rendered charts.
- **Document Compilation:** ReportLab for pixel-perfect PDF clinical exports.
- **Zero Third-Party Telemetry:** 100% on-device local storage. No external API keys required.

---

### Slide 6 — Innovation: Explainability, Safety & Privacy
- **Explainable Analytics Over Black Boxes:** Avoids opaque, unvalidated disease-prediction models. Every insight references exact dates, frequency counts, and explicit caveats (*"shows an association, not proof of causation"*).
- **Hardcoded Priority Safety Hierarchy:** Safety decisions cannot be overridden or diluted by language models or analytics. Critical flags (worst headache of life, hemorrhagic bleeding, syncope) escalate immediately to emergency medical care.
- **Privacy by Architecture:** Health observations are among the most sensitive personal data. SQLite stores data locally on the user's device, eliminating cloud breach risks.

---

### Slide 7 — Verification Evidence & Current Limitations
- **Verification Evidence:**
  - Automated test suite: **28 unit tests passing with 100% pass rate**.
  - Verified across database CRUD, foreign-key isolation, input validation, statistical null-handling, triage safety hierarchy, and PDF generation.
  - Real database records drive all charts, KPIs, and reports without mock sample data.
- **Current Prototype Limitations:**
  - Single-device local database (not an enterprise cloud EHR).
  - Not an automated medical diagnostic tool (requires clinical human interpretation).
  - Triage navigator provides structured guidance, not emergency clinical dispatch.

---

### Slide 8 — Future Roadmap & Conclusion
- **Near-Term Roadmap:**
  - Encrypted SQLite database using SQLCipher for at-rest storage encryption.
  - FHIR / HL7 clinical data interoperability for direct export to electronic health record systems.
  - Wearable sensor data ingestion (sleep tracking, resting heart rate, skin temperature).
  - Multi-language localized health literacy libraries.
- **Conclusion:**
  - HERPath AI bridges the critical communication gap between women and their healthcare providers through structured tracking, transparent safety guidance, and actionable clinical summaries.
  - **Empowering women to understand their symptoms, discover patterns, and take informed next steps.**
