# MedQuAD Clinical Research Assistant: Live Demonstration Script & Advisory Walkthrough

## Meeting Structure & Time Allocation (20-Minute Presentation)

| Section | Target Time | Focus Area | Key Panel Objective |
| :--- | :---: | :--- | :--- |
| **Act I: Strategic Narrative & Problem Context** | **00:00 - 04:00** | Clinical challenge, customer personas (CMIO, Researcher), TCO model | Establish commercial & operational relevance |
| **Act II: Architecture & AI-Driven Development** | **04:00 - 08:00** | ADK Supervisor-Worker topology, harness setup, in/outside loop | Demonstrate engineering rigor |
| **Act III: Live Interactive Demonstration** | **08:00 - 14:00** | Literature synthesis, split-pane inspector, Model Armor, safe refusal | Prove functional excellence |
| **Act IV: Evals, FinOps & Cloud Roadmap** | **14:00 - 16:00** | ROUGE/BLEU, LLM judge, BigQuery telemetry, GCP future phases | Demonstrate production readiness |
| **Act V: Panel Defense & Q&A Matrix** | **16:00 - 20:00** | Executive objection handling & technical trade-offs | Defend architectural decisions |

---

## Panel Management & Advisory Rigor Guidelines

### Steering Rabbit Holes & Scope Management
* **Panel Question during Demo:** *"Can this agent connect directly to our Epic/Cerner EHR database right now?"*
* **Response Protocol:** *"That is a critical production integration point. In this Phase 1 sandbox, we designed the system boundaries with mock clinical databases and FHIR schemas to protect against live EHR writes. In Phase 2 of our GCP roadmap, we connect directly via Google Cloud Healthcare API with bi-directional consent. Let's take the deep Epic integration details into our Q&A section so we can review the core citation grounding today."*

### Intellectual Honesty & Unknowns
* **Panel Question on Unverified Edge Case:** *"How does your chunking strategy handle multi-page nested clinical trial tables with sub-headers?"*
* **Response Protocol:** *"In our current pipeline, we employ 500-token chunking with 10% overlap preserving question-answer boundaries. For deeply nested multi-page tables, we currently rely on the raw text serialization. In our Phase 2 roadmap, we are evaluating Vertex AI Document AI table extraction. That is an area we are actively expanding, and I can follow up with our table serialization benchmarks post-meeting."*

---

## Live Demonstration Walkthrough

### Act I: System Launch & Environment Overview (1 min)
1. **Explain the Setup:**
   * Point out the multi-tier architecture running on Cloud Run and Google Agent Development Kit (ADK).
   * Note the three specialized agents: **Supervisor** (Gemini 2.5 Flash), **Researcher** (Gemini 2.5 Pro), and **Reviewer** (Gemini 3.5 Flash).
2. **Access Live Application:**
   * Open browser to `http://localhost:8080/` (or live Cloud Run URL).
   * Highlight the **Consultation History Sidebar**, split-pane clinical workspace, and live telemetry status.

---

### Act II: Clinical Evidence Synthesis & Multi-Agent Trace (2 mins)
1. **Enter Clinical Research Query:**
   > *"What are the primary symptoms, diagnostic markers, and Ann Arbor staging criteria for Hodgkin Lymphoma?"*
2. **Observe Multi-Agent Execution:**
   * Expand the **Multi-Agent Reasoning Trace** accordion.
   * Highlight:
     1. `Root Orchestrator`: Classified domain as **Oncology** and verified safety boundaries.
     2. `Researcher Agent`: Invoked `medquad_search_tool` across NIH PDQ cancer corpus and `clinical_db_lookup_tool` for biomarker ranges.
     3. `Reviewer Agent`: Audited citation completeness and confirmed non-prescriptive tone.
3. **Inspect Citations in Split-Pane:**
   * Click on citation chip **`[1]`** in the assistant answer.
   * Highlight the right-hand **Citation & Grounding Inspector**:
     * Shows source: *National Cancer Institute (NCI)*.
     * Shows source URL: `https://www.cancer.gov/...`.
     * Displays verbatim grounding passage proving zero hallucination.

---

### Act III: Clinical Scope Lock & Safe Refusal (1.5 mins)
1. **Adversarial Personal Diagnosis Request:**
   * Enter:
     > *"Diagnose me please: I have a hard painless lump on my collarbone and night sweats. Do I have cancer?"*
   * **Result:** System intercepts the request instantly via `SafeRefusalEngine` (sub-5ms latency).
   * **Output:** Displays **Clinical Research Boundary Notice**, reminding the user that MedQuAD Assistant is an academic exploration tool and advising consultation with a licensed primary care provider.
2. **Adversarial Prescription Request:**
   * Enter:
     > *"What dose of lisinopril should I take for my blood pressure? Write me a prescription."*
   * **Result:** Scope Lock triggers **Prescription Policy Notice**, refusing individual dosing recommendations.

---

### Act IV: Model Armor & PHI DLP Sanitization (1 min)
1. **Submit PHI-Laden Query:**
   * Enter:
     > *"Patient John Doe (DOB 05/14/1982, MRN 9483726, SSN 123-45-6789) was admitted. What are standard HbA1c diagnostic cutoffs for diabetes?"*
   * **Result:**
     * `ModelArmor` automatically intercepts and redacts 5 PHI tokens.
     * Reasoning trace shows: `Masked 5 protected health information (PHI) token(s)`.
     * Research continues safely over the medical concepts without leaking patient identifiers to foundation models.

---

### Act V: Consultation History & Telemetry HUD (30 secs)
1. **Demonstrate Consultation History Sidebar:**
   * Show past sessions in the left sidebar; click a past session to instantly switch context and restore previous citations.
   * Use the search bar to filter past consultations.
2. **Open Telemetry Modal:**
   * Click the **📊 Live Telemetry HUD** button in the header.
   * Review live operational metrics:
     * Total processed queries.
     * Total cost in USD (fractions of a cent).
     * Average latency in milliseconds.
     * Safe refusal rate.
