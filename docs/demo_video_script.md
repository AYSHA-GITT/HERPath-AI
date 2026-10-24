# HERPath AI — 3-Minute Demonstration Video Script & Walkthrough
## recHERsion 2026 | PS1: Women's Healthcare

This walkthrough script details the exact 3-minute sequence for demonstrating HERPath AI during the hackathon evaluation.

---

### [0:00 – 0:20] Introduction & Problem Context
- **Screen:** Home Dashboard showing "HERPath AI — Women's Health Intelligence & Care Navigation Platform".
- **Speaker:** 
  > *"Welcome to HERPath AI, built for recHERsion 2026. Women face persistent challenges when communicating chronic or fluctuating health symptoms during medical consultations. Conditions like endometriosis, PCOS, hormonal migraines, and perimenopause often experience diagnostic delays of up to a decade. HERPath AI is a privacy-first platform that empowers women to record symptoms, discover explainable patterns, navigate care safely, and generate clinician-ready health summaries."*

---

### [0:20 – 0:50] Smart Symptom Journaling & Live Persistence
- **Action:**
  1. Open sidebar and show active demo profile (e.g. *Priya (PCOS & Migraine Tracking)*).
  2. Click **"Symptom Journal"** in navigation.
  3. Enter a new symptom entry:
     - Category: `Neurological & Head`
     - Symptom: `Migraine`
     - Onset Date: Today
     - Severity: `7` (Severe)
     - Duration: `6.0` hours
     - Status: `Ongoing`
     - Impact: `Moderate (Modified daily plans)`
     - Context: Sleep `Disrupted / Fragmented`, Stress `High / Pressured`
     - Notes: `Left frontal throbbing, photophobia after working under fluorescent lights.`
  4. Click **"Save Symptom Entry"**.
  5. Show the immediate confirmation alert and switch to **"View & Filter Symptom History"** tab to highlight the new record persisted directly in SQLite.
- **Speaker:**
  > *"Users can track symptoms across multiple body systems—not just menstrual cycles. Every entry is validated and immediately persisted in a local SQLite database with profile-scoped isolation, complete with contextual sleep, stress, and impact observations."*

---

### [0:50 – 1:20] Real Health Insights & Explainable Patterns
- **Action:**
  1. Navigate to **"Health Insights"**.
  2. Review the updated KPI cards (total entries, distinct days, average severity, top symptom).
  3. Point to the **Explainable Observation Statements**:
     - Highlight: *"Migraines were recorded 4 times across logged days... Poor sleep was also recorded on 3 of those days."*
     - Emphasize the note: *"These entries show an observable association, not proof of causation."*
  4. Interact with the Plotly Severity Timeline chart and hover over data points.
- **Speaker:**
  > *"Rather than using a black-box machine learning model that makes unvalidated disease predictions, HERPath AI uses a transparent, explainable analytics engine. It calculates factual frequency, severity progression, and contextual co-occurrences grounded directly in stored records, providing clear observations patients can bring to their doctor."*

---

### [1:20 – 1:45] Care Guidance & Safety Navigator
- **Action:**
  1. Navigate to **"Care Navigator"**.
  2. Demonstrate an evaluation scenario:
     - Scenario A: Select `Neurological & Head` -> `Migraine`, severity `9`, and check warning sign: *"Sudden onset 'worst headache of life' (thunderclap)"*.
     - Click **"Evaluate Care Guidance"**.
  3. Show the **Emergency Evaluation Needed** card with immediate instructions, rationale, and local emergency contact numbers.
  4. Briefly switch to a moderate scenario to show how routine clinical consultation guidance is generated when no red flags are present.
- **Speaker:**
  > *"Our Care Navigator enforces a strict, rule-based clinical triage hierarchy based on WHO and NHS guidelines. Critical red flags—such as thunderclap headaches or hemorrhagic bleeding—immediately trigger urgent emergency safety guidance and can never be overridden by AI or delayed by analytics."*

---

### [1:45 – 2:10] Trusted Women's Health Library
- **Action:**
  1. Navigate to **"Women's Health Library"**.
  2. Filter by Category `PCOS Education` or search `iron`.
  3. Expand a card (e.g. *Understanding Polycystic Ovary Syndrome (PCOS)* by WHO or *Iron Deficiency Anemia* by NHS).
  4. Highlight the source organization, key clinical takeaways, and verified source URL.
- **Speaker:**
  > *"Medical misinformation is a major hazard in women's health. HERPath AI includes a curated library of verified educational resources directly citing authorities like the World Health Organization, NHS, and CDC, helping users build credible health literacy."*

---

### [2:10 – 2:30] Clinician-Ready Health Report (PDF Export)
- **Action:**
  1. Navigate to **"My Health Report"**.
  2. Review the live report preview showing the reporting period, entry count, and average severity.
  3. Click **"Download Clinician Health Report (PDF)"**.
  4. Open or preview the downloaded PDF, highlighting the professional header, patient details, structured symptom table, severity trajectory, doctor discussion questions, and clinical disclaimers.
- **Speaker:**
  > *"With one click, HERPath AI compiles a clinician-ready PDF using ReportLab. It summarizes the patient's actual database records, highlights trajectories, and prepares structured questions for their physician, transforming a rushed consultation into a high-value, collaborative appointment."*

---

### [2:30 – 3:00] Architecture, Privacy & Conclusion
- **Action:**
  1. Navigate to **"Privacy and Settings"**.
  2. Show local storage notice, profile controls, and demonstrate switching profiles to prove complete data isolation.
- **Speaker:**
  > *"HERPath AI is built with privacy-by-design: all data is stored locally on the device in SQLite with zero third-party telemetry. All 28 automated test cases pass with a 100% pass rate. HERPath AI bridges the communication gap between women and their healthcare providers. Thank you!"*
