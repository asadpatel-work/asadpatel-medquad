# MedQuAD Clinical Research Assistant: Presentation Deck

**Project:** MedQuAD Clinical Research Assistant (Multi-Agent Grounded Literature Synthesis)  
**File Artifact:** [`docs/medquad_capstone_presentation.pptx`](medquad_capstone_presentation.pptx)  
**Format:** 16:9 Widescreen Presentation (Google Slides / PowerPoint compatible)  
**Design Standard:** Generated via `generate-slides` skill (Declarative Action Titles, Category Trackers, Clean Tech Palette, Native Presenter Notes)

---

## Slide 1: Title Slide

### Visual Layout
* **Tag:** `FIELD DELIVERY ENGINEER (FDE) CAPSTONE PRESENTATION`
* **Title:** **MedQuAD Clinical Research Assistant**
* **Subtitle:** Multi-Agent Grounded Literature Synthesis & Clinical Guardrails
* **Metadata:** 
  * Candidate: Asad Patel | Target Role: Field Delivery Engineer (FDE)
  * Platform: Google Cloud (Vertex AI Search, Cloud Run, ADK, Gemini 2.5/3.5)

### Speaker Notes
> *"Good morning. Today I am presenting the MedQuAD Clinical Research Assistant for my Field Delivery Engineer capstone evaluation.*  
> 
> *This system addresses the challenge of clinical literature discovery by combining Google Cloud's Agent Development Kit with Vertex AI Search and deterministic guardrails.*  
> 
> *This presentation covers: the clinical problem, our product capabilities, the end-to-end multi-agent architecture, and our future engineering roadmap."*

---

## Slide 2: Problem Definition

### Header
* **Category Tracker:** `PROBLEM DEFINITION`
* **Action Title:** **Clinical Search Suffers from High Manual Overhead and Unsafe Model Hallucinations**

### Content Cards
#### Card 1: 1. Manual Literature Synthesis Friction
* Clinicians and researchers spend over 35% of working hours manually combing through fragmented medical databases (NIH, NCI, CDC, PubMed).
* Synthesizing an authoritative answer for staging criteria, treatment protocols, or adverse reactions takes ~15 minutes of specialized labor.
* High research friction directly delays clinical trial design, literature review updates, and research grant submissions.
* Knowledge remains locked in static, disconnected XML repositories without centralized semantic search capability.

#### Card 2: 2. Foundation Model Hallucinations & Liability
* Standard off-the-shelf LLMs exhibit an ~18% citation error and hallucination rate on medical literature queries.
* Generic models fabricate plausible clinical claims, non-existent PMIDs, and outdated pharmaceutical dosing guidelines.
* Unguarded models attempt to answer personal diagnosis and prescription questions, creating severe malpractice liability.
* Commercial consumer chatbots lack deterministic 1:1 chunk verification to prove evidence provenance.

### Speaker Notes
> *"Slide 2 establishes the core problem.*  
> 
> *Clinical researchers face two competing challenges:*  
> *First, manual research takes too long. Combing through NIH databases, clinical trials, and FDA inserts consumes over 35% of a researcher's time, averaging 15 minutes per query.*  
> 
> *Second, relying on standard LLMs is dangerous in clinical contexts. Studies show foundation models hallucinate citations roughly 18% of the time, and unguarded models attempt to offer personal medical advice, creating unacceptable legal risk.*  
> 
> *The MedQuAD Assistant bridges this divide by delivering automated literature synthesis with strict 1:1 citation proof and deterministic safety boundaries."*

---

## Slide 3: Product Overview

### Header
* **Category Tracker:** `PRODUCT OVERVIEW`
* **Action Title:** **MedQuAD Delivers Grounded Literature Synthesis with Deterministic Verification**

### Quadrant Cards
#### Top-Left: Authoritative NIH Corpus Grounding
* Indexes 16,400+ verified medical Q&A pairs from NIH, NCI, CDC, and MedlinePlus across 12 clinical domains.
* Structured with 500-token semantic chunks and 10% overlap to preserve clinical context.
* Powered by Google Vertex AI Search with automated circuit-breaker fallback to an in-memory vector store.

#### Top-Right: Deterministic Citation Verification
* Independent Reviewer subagent cross-examines draft responses against retrieved source passages.
* CitationVerifier ensures 100% of bracketed claims map to valid retrieved chunk IDs.
* Ungrounded statements are automatically flagged and removed before streaming to the user.

#### Bottom-Left: Layer 8 Safety & Safe Refusal Engine
* Pre-flight de-identification of 18 HIPAA Safe Harbor identifiers (MRN, SSN, patient names).
* Immediate rejection (<5ms) of personal diagnosis and drug dosing prompts without invoking model tokens.
* Structured response redirects users to certified healthcare providers and emergency services.

#### Bottom-Right: Cost-Effective Model Tiering
* Tiered Gemini deployment: Flash 2.5 for intent/routing, Pro 2.5 for synthesis, Flash 3.5 for audit.
* Blended query cost of ~$0.0035 ($351/month for 100,000 queries) vs. $15.00 manual labor.
* Deployed on Cloud Run with p95 response latency under 3 seconds and zero idle server costs.

### Speaker Notes
> *"Slide 3 outlines what the product actually does and how it operates.*  
> 
> *1. Authoritative Grounding: We indexed 16,400+ verified NIH pairs into Vertex AI Search with 500-token semantic chunks.*  
> 
> *2. Deterministic Verification: Rather than hoping the model doesn't hallucinate, an independent Reviewer agent verifies every bracketed citation against the retrieved chunks, achieving 100% citation precision.*  
> 
> *3. Safe Refusal Engine: If a user enters diagnostic or dosing questions, our boundary engine catches it in under 5ms, returning a clinical disclaimer with zero token waste.*  
> 
> *4. Cost Efficiency: By tiering Gemini models, we keep inference costs to just $0.0035 per query, running serverless on Cloud Run."*

---

## Slide 4: System Architecture

### Header
* **Category Tracker:** `SYSTEM ARCHITECTURE`
* **Action Title:** **Multi-Agent ADK Architecture Decouples Retrieval, Synthesis, and Verification**

### Visual Diagram Architecture Layout

```
[1. Ingress & Perimeter Security Gateway]
  Clinician / UI ──(1. Query)──> Cloud Armor WAF ──(2. Clean)──> Cloud Run Gateway ──(3. Ingest)──> Model Armor
                                                                                                    ├──(Refusal <5ms)──> [Safe Refusal Exit]
                                                                                                    └──(4. Valid Inquiry)──┐
                                                                                                                           │
[2. Google ADK Multi-Agent Core]                                                                                           ▼
  ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
  ▼
  Root Orchestrator (Gemini 2.5 Flash) ──(5. Route)──> Clinical Researcher (Gemini 2.5 Pro) ──(8. Draft)──> Reviewer & QC Gate (Gemini 3.5 Flash)
                                                               │                ▲                                     │
                                                     (6. Query)│                │(7. Chunks)                          │(Telemetry)
                                                               ▼                │                                     ▼
[3. Grounding Data Stores & Observability]             Vertex AI Search (16.4k NIH pairs)                     Cloud Trace & BigQuery
                                                       ClinicalDBTool (Lab Ranges)
                                                       Vector DB Fallback (Circuit Breaker)
```

#### Diagram Component Details:
1. **Tier 1 — Perimeter & Ingress:**
   * **Clinician / UI:** Web App / REST API with streaming SSE and inline citation viewer.
   * **Cloud Armor WAF:** L7 DDoS filtering, IP throttling, bot defense.
   * **Cloud Run Gateway:** Serverless FastAPI container handling authentication and session state.
   * **Model Armor Guardrail:** De-identifies 18 HIPAA Safe Harbor identifiers and filters prompt jailbreaks.
   * **Safe Refusal Engine Exit:** Instant deterministic block (<5ms) on personal medical advice/dosing, returning emergency disclaimers with 0 tokens spent.
2. **Tier 2 — Google ADK Multi-Agent Core:**
   * **Root Orchestrator (Supervisor - Gemini 2.5 Flash):** Classifies query intent, handles safe refusal policies, and enforces immutable `max_iterations=2` loop ceiling.
   * **Clinical Researcher (Worker - Gemini 2.5 Pro):** Performs deep biomedical reasoning, queries grounding tools, and drafts response with inline `[1]`, `[2]` citation tags.
   * **Reviewer & QC Gate (Auditor - Gemini 3.5 Flash):** Operates with zero shared hidden state; runs `CitationVerifier` to validate 100% 1-to-1 chunk ID provenance before streaming release.
3. **Tier 3 — Grounding & Observability:**
   * **Vertex AI Search:** 16,400+ NIH Q&A pairs indexed in 500-token semantic chunks.
   * **ClinicalDBTool:** Structured clinical reference ranges and diagnostic biomarker values.
   * **Vector DB Fallback:** Local in-memory FAISS store for sub-50ms circuit-breaker resilience on 504 timeouts.
   * **Cloud Trace & BigQuery:** OpenTelemetry distributed tracing spans and nightly automated quality evaluation sink.

### Speaker Notes
> *"Slide 4 walks through the technical architecture and request lifecycle:*  
> 
> *1. Ingress & Security: Requests enter via Cloud Armor and FastAPI on Cloud Run. Before touching any model, Model Armor redacts 18 HIPAA Safe Harbor identifiers and filters jailbreak patterns.*  
> 
> *2. Orchestration: The Root Orchestrator (Gemini 2.5 Flash) assesses the query. If it asks for diagnosis or prescriptions, the Safe Refusal Engine catches it in under 5ms. If valid, it delegates to the Researcher.*  
> 
> *3. Research: The Clinical Researcher (Gemini 2.5 Pro) retrieves passages from Vertex AI Search and synthesizes a draft with explicit citations.*  
> 
> *4. Review: The draft is reviewed by an independent Reviewer subagent (Gemini 3.5 Flash) with zero shared state. The CitationVerifier validates every citation against retrieved chunk IDs before release.*  
> 
> *5. Telemetry: Traces are pushed to Cloud Trace, and telemetry data (latency, cost, tokens) is streamed to BigQuery."*

---

## Slide 5: Future Roadmap

### Header
* **Category Tracker:** `FUTURE ROADMAP`
* **Action Title:** **Roadmap Focuses on Clinical Standards, State Persistence, and Multimodal RAG**

### Milestone Cards
#### 1. EHR Standards (Google Cloud Healthcare API)
* Integrate Google Cloud Healthcare API to query de-identified clinical records.
* Parse and ingest FHIR R4 resources (Patient, Condition, Observation, MedicationStatement).
* Enable researchers to cross-reference literature evidence against clinical cohort criteria.

#### 2. Distributed Session Persistence & State Store
* Migrate from ephemeral in-memory conversation state to distributed Cloud Firestore.
* Support multi-turn research threads across container instances with TTL retention.
* Implement multi-region active-active replication for enterprise high availability.

#### 3. Multimodal Clinical RAG (Gemini Vision)
* Expand ingestion pipeline from text-only XML records to diagnostic imaging.
* Ingest DICOM radiology files and pathology slide scans stored in GCS buckets.
* Use Gemini multimodal reasoning to correlate medical imaging with clinical guidelines.

#### 4. Enterprise Access Control & Zero-Trust Perimeter
* Integrate Google Identity-Aware Proxy (IAP) for institutional Single Sign-On (SSO).
* Enforce role-based access control (RBAC) separating researchers, oncologists, and auditors.
* Deploy Private Service Connect (PSC) to isolate backend services inside customer VPCs.

### Speaker Notes
> *"Slide 5 outlines our concrete next engineering milestones:*  
> 
> *1. EHR Integration: Using the Google Cloud Healthcare API to ingest de-identified FHIR R4 records, allowing researchers to contextualize literature findings against patient cohort criteria.*  
> 
> *2. State Persistence: Migrating from local in-memory session cache to distributed Firestore, ensuring research threads survive container restarts across regions.*  
> 
> *3. Multimodal RAG: Leveraging Gemini's multimodal capabilities to analyze DICOM radiology scans alongside literature guidelines.*  
> 
> *4. Enterprise Security: Adding Identity-Aware Proxy for hospital SSO and Private Service Connect to satisfy enterprise zero-trust networking requirements."*
