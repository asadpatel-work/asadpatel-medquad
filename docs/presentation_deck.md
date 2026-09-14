# MedQuAD Clinical Research Assistant: Presentation Deck

**Project:** MedQuAD Clinical Research Assistant (Multi-Agent Grounded RAG)  
**File Artifact:** [`docs/medquad_capstone_presentation.pptx`](medquad_capstone_presentation.pptx)  
**Format:** Google Slides / PowerPoint (16:9 Widescreen, Clean White Enterprise Theme)  
**Pacing:** ~15–20 minutes presentation + Q&A

---

## Slide 1: Problem: Clinical Literature Retrieval & Hallucination Risks

### Slide Content

#### 1. Manual Literature Synthesis Overhead
* Clinicians and researchers spend over 35% of their research time searching disparate medical databases (NIH, NCI, CDC, PubMed).
* Manual collation of staging criteria, treatment protocols, and adverse reactions is slow and error-prone.
* Synthesizing an authoritative answer to a complex clinical question takes an average of 15 minutes of specialized clinician time.
* Information is fragmented across thousands of static XML and PDF files without unified semantic indexing.

#### 2. LLM Hallucinations & Clinical Liability
* Standard off-the-shelf foundation models exhibit an ~18% citation hallucination rate on biomedical literature queries.
* Commercial chatbots generate plausible-sounding but fictitious medical claims, fabricated journal links, and obsolete dosing advice.
* Unguarded models attempt to diagnose conditions or recommend drug doses from user prompts, creating severe medical liability.
* Off-the-shelf models lack a verifiable 1-to-1 provenance mechanism connecting each statement back to an authoritative medical chunk.

### Speaker Notes
> *"Slide 1 outlines the core problem we set out to solve.*  
> 
> *In healthcare, researchers and clinicians face two distinct failure modes when answering clinical questions:*  
> 
> *First, manual retrieval is inefficient. Researchers spend more than a third of their time combing through disparate NIH databases, guidelines, and trial registries. A single literature review can easily take 15 minutes of manual labor.*  
> 
> *Second, simply handing the problem to a generic LLM introduces severe clinical risk. Foundation models hallucinate citations roughly 18% of the time, and unprompted, they will attempt to diagnose or recommend prescriptions, exposing the institution to malpractice liability.*  
> 
> *The goal of this project is to bridge this gap: automate literature synthesis while guaranteeing 100% citation grounding and enforcing strict clinical guardrails."*

---

## Slide 2: Product Overview: MedQuAD Clinical Research Assistant

### Slide Content

#### Authoritative NIH Corpus Grounding
* Indexes 16,400+ verified medical Q&A pairs from NIH, NCI, CDC, and MedlinePlus.
* Preprocessed with 500-token semantic chunking and 10% overlap to preserve clinical context.
* Backed by Google Vertex AI Search with automated fallback to an in-memory vector store.

#### Deterministic Citation Verification
* Every generated statement must map 1:1 to a specific retrieved NIH passage chunk.
* A dedicated Reviewer agent audits citations before output is streamed to the user.
* Enforces 100% citation precision—unverified statements are flagged or excised.

#### Layer 8 Safety & Safe Refusal
* Immediate interception (<5ms) of personal diagnostic and drug dosing demands.
* Pre-flight de-identification of 18 HIPAA Safe Harbor identifiers (MRN, SSN, names).
* Returns structured clinical disclaimers and emergency redirection without wasting LLM tokens.

#### Efficient Model Tiering & Cloud Run
* Tiered Gemini models: Flash 2.5 for routing/safety, Pro 2.5 for synthesis, Flash 3.5 for review.
* Blended inference cost of ~$0.0035 per query ($351/mo for 100,000 queries).
* Deployed serverless on Google Cloud Run with sub-3s p95 latency and zero cold starts.

### Speaker Notes
> *"Slide 2 describes the product and what it actually does.*  
> 
> *The MedQuAD Clinical Assistant is a specialized research tool built on top of 16,400+ authoritative NIH medical records.*  
> 
> *Here are its four defining technical characteristics:*  
> *1. Authoritative Grounding: We chunked and indexed NIH, NCI, and MedlinePlus data using 500-token semantic chunks in Vertex AI Search.*  
> *2. Deterministic Verification: Rather than trusting the model to cite accurately, a dedicated Reviewer subagent cross-examines the draft against retrieved chunk IDs. We enforce 100% citation provenance.*  
> *3. Layer 8 Guardrails: If a user asks for a personal diagnosis or a prescription dose, our Safe Refusal Engine catches it in under 5 milliseconds and responds with a clinical disclaimer, invoking zero LLM tokens.*  
> *4. Practical FinOps: We tiered Gemini models so that routing and review run on lightweight Flash models, reserving Gemini Pro strictly for multi-document synthesis. This brings the total blended cost down to $0.0035 per query."*

---

## Slide 3: System Architecture: ADK Multi-Agent Pipeline

### Slide Content

#### 1. Ingress & Perimeter Defense
`Client Request (HTTPS / SSE) ──> Cloud Armor L7 WAF ──> Cloud Run (FastAPI Gateway) ──> Model Armor (HIPAA PHI Redaction & Injection Filter)`

#### 2. Multi-Agent Core (Supervisor-Worker Pattern)
* **Root Orchestrator (Supervisor - Gemini 2.5 Flash):**
  * Evaluates user intent & domain.
  * SafeRefusalEngine intercepts diagnosis & prescription requests in <5ms.
  * Enforces immutable `max_iterations=2` loop ceiling to prevent runaway costs.
* **Clinical Researcher (Worker - Gemini 2.5 Pro):**
  * Executes semantic search across 16.4k NIH MedQuAD passages.
  * Queries lab reference ranges via ClinicalDBTool.
  * Synthesizes grounded evidence draft with explicit inline `[1]`, `[2]` citations.
* **Reviewer & QC (Quality Gate - Gemini 3.5 Flash):**
  * Operates with zero shared hidden state to avoid confirmation bias.
  * CitationVerifier: checks that every bracketed citation maps to a valid retrieved chunk ID.
  * Blocks ungrounded claims before streaming.

#### 3. Grounding & Data Layer
`Vertex AI Search (16,400+ NIH Records) | Local In-Memory Vector Fallback (Circuit Breaker) | GCS Corpus Bucket`

#### 4. Observability & Continuous Evaluation
`OpenTelemetry Distributed Context ──> Cloud Trace ──> BigQuery Telemetry Sink ──> Cloud Scheduler Nightly Audit Pipeline`

### Speaker Notes
> *"Slide 3 walks through our multi-agent architecture and request lifecycle.*  
> 
> *1. Ingress & Security: Requests enter via Cloud Armor and FastAPI on Cloud Run. Before touching any LLM, our Model Armor engine strips 18 HIPAA Safe Harbor identifiers and filters jailbreak patterns.*  
> 
> *2. Orchestration: The Root Orchestrator (Gemini 2.5 Flash) assesses the request. If the user asks for diagnosis or prescriptions, the Safe Refusal Engine catches it in under 5ms. If it's a valid clinical inquiry, it delegates to the Researcher.*  
> 
> *3. Research: The Clinical Researcher (Gemini 2.5 Pro) retrieves passages from Vertex AI Search and drafts a synthesis with inline citation brackets.*  
> 
> *4. Review: Crucially, that draft is sent to an independent Reviewer subagent (Gemini 3.5 Flash) with zero shared state. The CitationVerifier validates each citation against the retrieved chunks. If valid, it is streamed to the user.*  
> 
> *5. Telemetry: Every span is traced to Google Cloud Trace, and telemetry metrics (latency, token usage, cost) are streamed into BigQuery."*

---

## Slide 4: Future Work: Roadmap & Clinical System Integration

### Slide Content

#### 1. EHR & Standards Integration (Cloud Healthcare API)
* Connect to Google Cloud Healthcare API to query de-identified patient data.
* Ingest and parse FHIR R4 resources (Patient, Condition, Observation, MedicationStatement).
* Enable clinical researchers to compare literature findings against patient cohort criteria.

#### 2. Distributed Session Persistence & State Store
* Migrate from ephemeral in-memory session history to distributed Cloud Firestore.
* Support cross-session multi-turn research conversations with TTL-managed retention.
* Implement multi-region active-active redundancy for continuous availability.

#### 3. Multimodal Clinical RAG (Gemini Vision)
* Expand retrieval from text-only NIH XML documents to medical imagery and scans.
* Ingest DICOM radiology files and histology slides stored in Cloud Storage buckets.
* Use Gemini multimodal reasoning to correlate diagnostic imaging with clinical guidelines.

#### 4. Enterprise Access Control & Zero-Trust Perimeter
* Integrate Google Identity-Aware Proxy (IAP) for institutional Single Sign-On (SSO).
* Enforce role-based access control (RBAC) distinguishing researchers, oncologists, and auditors.
* Deploy Private Service Connect (PSC) to isolate backend services inside customer VPCs.

### Speaker Notes
> *"Slide 4 covers our planned technical roadmap and next engineering steps.*  
> 
> *Now that the core grounded literature engine and multi-agent verification are verified, we have four logical milestones:*  
> 
> *1. EHR Integration: Utilizing the Google Cloud Healthcare API to ingest de-identified FHIR R4 records, allowing researchers to evaluate literature directly in the context of patient cohorts.*  
> 
> *2. Persistent Storage: Migrating from local in-memory session cache to multi-region Firestore, ensuring research threads survive container restarts.*  
> 
> *3. Multimodal RAG: Leveraging Gemini's native multimodal capabilities to analyze DICOM radiology scans alongside literature guidelines.*  
> 
> *4. Enterprise Security: Adding Identity-Aware Proxy for hospital SSO and Private Service Connect to satisfy enterprise zero-trust networking requirements."*
