# Technical Design Document

# FDE Technical Design Document

## Project Name: MedQuAD Clinical Assistant

**FDE Lead(s):** FDE Noogler (Primary), FDE Onboarding Buddy (Reviewer)  
**Last Updated:** June 13, 2026  
**Status:** Under Review

&nbsp;

---

## Executive Summary

Clinicians and medical researchers at the NIH Clinical Center face significant cognitive load and time constraints when navigating thousands of medical guidelines, disease indicators, and treatment protocols. The MedQuAD Clinical Assistant is a high-performance, asynchronous agentic platform designed to automate clinical information retrieval and research synthesis. Overcoming traditional search inefficiencies, the assistant utilizes a Supervisor-Worker agentic topology to deliver grounded, cited medical research over the authoritative NIH MedQuAD database with sub-second retrieval latency, zero hallucinations, and strict clinical safety filters.

### Core "North Star" Metrics

* **Recall Rate**: \>=90% relevant information retrieval from the MedQuAD grounding index.  
* **Precision Rate**: \>=88% accurate clinical keyword and schema extraction.  
* **Safety Compliance**: 100% deterministic enforcement of "Safe Refusal" non-medical advice guardrails.  
* **Response Time**: p95 latency \<= 2.5 seconds for clinical lookups.

&nbsp;

---

## System Architecture

### High-Level Diagram

```
graph TD
    User([Clinician / Researcher]) -->|1. Natural Language Query| FE[React Frontend - TypeScript/Vite]
    FE -->|2. Asynchronous API Request| BE[FastAPI Backend - Cloud Run]
    
    subgraph Backend [FastAPI Backend - Secure Sandbox]
        BE -->|3. Route & Authenticate| GA[Agent Gateway / AuthN]
        GA -->|4. Sanitize Input| MA[Model Armor & DLP Guardrail]
        MA -->|5. Forward Query| CO[Root Orchestrator Agent - Gemini 2.5 Flash]
        
        CO -->|6a. Delegate Research| RA[Researcher Subagent - Gemini 2.5 Pro]
        CO -->|6b. Delegate Validation| RE[Reviewer Subagent - Gemini 3.5 Flash]

        RA -->|7. Search Tool| VAIS[Vertex AI Search - MedQuAD Index]
        RA -->|8. Fetch Mock Records| MDB[Mock Clinical DB Tool]
    end
    
    MDB -->|Query Simulated Records| CS[Cloud SQL PostgreSQL]
    VAIS -->|Semantic Query| GCS[Google Cloud Storage - MedQuAD Corpus]
    
    BE -->|9. Export Spans/Traces| OTEL[OpenTelemetry / Cloud Trace]
    BE -->|10. Stream Logs/Metrics| BQ[BigQuery Telemetry Sink]
```

### Architecture Principles

* **Modularity**: High-code, decoupled Supervisor-Worker topology using the Google ADK. Individual agents operate as isolated units, allowing models and tools to be swapped seamlessly.  
* **Scalability**: Hosted on serverless Google Cloud Run with high concurrency (max\_instance\_request\_concurrency \= 40\) and automated scaling bounds.  
* **Resilience**: Defensive retry policies with exponential backoff and jitter handle rate limits. Standardized fallbacks allow graceful degradation (e.g., reverting to static medical indexes upon Search endpoint outages).

### Technical Components & Agent Logic

* **Agent Development Kit (ADK)**: Orchestrates the central supervisor (RootOrchestrator) and specialized workers:  
  * **ResearcherAgent**: Owns tool use and semantic search execution over medical datasets.  
  * **ReviewerAgent**: Acts as an independent clinical quality controller, scoring responses before final output.  
* **Reasoning Strategy**: Employs a structured ReAct (Reasoning and Action) execution loop. The agent plans its task manifest, executes API tools, reviews intermediate payloads, and loops until the clinical success criteria are met.  
* **Context & Memory Strategy**: Utilizes an asynchronous PostgreSQL-backed session service. Conversational history and short-term context are managed in active state caches, while long-term session summaries are persisted in the database to prevent token bloat.

### Tooling & External Integrations

* **Tool Registration**: Tool definitions are registered natively inside the ADK framework using explicit Pydantic type schemas to enforce strict parameter bounds.  
* **Model Context Protocol (MCP)**:  
  * **MCP Servers**: Tool logic is encapsulated in isolated MCP servers hosted on Cloud Run.  
  * **Transport**: Standard use of Server-Sent Events (SSE) over secure endpoints to facilitate network-isolated, high-performance tool communication.  
  * **Discovery**: Dynamic discovery of schema elements via standard JSON-RPC capabilities exposed by the MCP client.  
* **Authentication**: Managing external API credentials securely. The MCP server retrieves API tokens at runtime from Google Cloud Secret Manager using its unique service account identity.  
* **Function Calling Logic**: Standardized exception wrappers handle HTTP 429 and 500 errors natively.

&nbsp;

---

## Infrastructure, Security, & IAM

### GCP Project Structure

* **Dev Project ID**: fde-medquad-sandbox-dev  
* **Region**: us-central1 (Core deployment target)  
* **Deployment Topology**: 100% self-contained inside the new hire's allocated sandbox.

### User Authentication (AuthN)

* **Identity Provider**: Single Sign-On (SSO) integrated via Google Workspace Okta.  
* **Access Patterns**: Internal API gateways are protected using Identity-Aware Proxy (IAP), requiring JWT-based bearer authentication on all incoming headers.

### Authorization (AuthZ)

* **Role-Based Access Control (RBAC)**: Group-based access definitions managed via Cloud Identity Groups.  
* **Service Accounts**: The application runs under a custom service account (`medquad-assistant-sa@fde-medquad-sandbox-dev.iam.gserviceaccount.com`). No default Compute Engine service accounts are used.  
* **SPIFFE-based Agent Identities**: Granular, per-agent identities are mapped to workloads to enforce Least Privilege for service-to-service communication.

### Data Protection & Compliance

* **Encryption**: 100% of data is encrypted in transit using TLS 1.3 and at rest using Customer-Managed Encryption Keys (CMEK) managed via Key Management Service (KMS).  
* **VPC Service Controls (VPC-SC)**: A strict service perimeter prevents data exfiltration. Vertex AI, Cloud Run, GCS, and BigQuery are locked inside a secure network boundary.  
* **PII / Sensitive Data**: Structured PII masking pipelines sanitize inbound queries before model ingestion.

### AI Safety & Prompt Management

* **GCP Agent Runtime Model Armor**: Standardized integration of Model Armor filters out prompt injection attacks, jailbreak attempts, and toxic behaviors natively.  
* **Custom Clinical Guardrails**:  
  * **Safe Refusal (Non-Medical Advice)**: A hardcoded prompt prefix ("scope lock") forces the model to refuse diagnostic queries or treatment prescriptions, maintaining a strictly informative research persona.  
  * **Toxicity and Hallucination Checks**: Output hooks analyze LLM output against retrieved chunks using a fast semantic pass.  
* **Prompt Lifecycle**: Prompts are separated from application logic, versioned in a dedicated prompt repository, and retrieved dynamically at startup.  
* **Human-in-the-Loop (HITL)**: Approval gates for high-stakes actions (e.g., financial transactions).

### CI/CD

* Deployed via Cloud Build triggered automatically upon successful Git merges.  
* The pipeline executes ruff formatting checks, lints, and triggers a comprehensive pytest suite (achieving \>80% code coverage) using mocked LLM and Search APIs.

&nbsp;

---

## Data Engineering & Intelligence

### Data Sources & Usage

* **Source Systems**: Raw MedQuAD medical Q\&A XML/JSON files stored in a secure Google Cloud Storage bucket (`gs://fde-medquad-grounding-corpus-dev/`).  
* **Data Profiles**: Unstructured and semi-structured Q\&A datasets.  
* **Access Patterns**: Dynamic, real-time semantic search via the Researcher Agent's search tool.

### Retrieval & Intelligence Strategy

* **Vector Infrastructure**: Gemini Enterprise Agent Search (VAIS) acts as the managed RAG engine.  
* **Embedding Strategy**: Automatic document chunking (500-token chunks with 10% overlap), indexed using Vertex AI's standard semantic embedding model (`text-embedding-004`).

&nbsp;

---

## Testing & Evaluation Framework

The evaluation strategy employs a hybrid approach, combining deterministic/statistical check pipelines with semantic model assessments.

### 1\. Statistical & Heuristic Evaluations (CI/CD Gates)

These tests execute on every pull request using the golden dataset of 150 clinical questions stored in BigQuery, asserting baseline performance without calling expensive models:

&nbsp;

* **ROUGE-L & BLEU Scores**: The system calculates ROUGE-L (recall-focused) and BLEU (precision-focused) scores comparing the generated clinical answer against the authoritative NIH ground-truth text. The build pipeline enforces a threshold of **ROUGE-L \>= 0.40** and **BLEU \>= 0.35**.  
* **Clinical Entity Overlap (F1-Score)**: Extracts key medical entities (symptoms, drug names, diagnoses) from both the output and ground-truth using a lightweight entity matcher. Asserts an entity F1-score of **\>= 0.75**.  
* **Deterministic Citation Check**: A test script parses the markdown output to ensure that:  
  1. All inline citations (e.g. `[1]`) correspond to active, retrieved search result chunk IDs.  
  2. The citation links are valid and not malformed.  
* **Safe Refusal Verification**: Verifies that diagnostic/prescriptive query test cases deterministically trigger standard refusal text (regex check) rather than generating active advice.

### 2\. Semantic Evaluations (Nightly/Ad-hoc)

* **LLM-as-a-Judge**: Automated pipelines execute using Gemini 3.5 Flash to evaluate unstructured quality dimensions:  
  * **Faithfulness**: Verifying the output contains only facts supported by the retrieved context chunks (detecting hallucination).  
  * **Helpfulness**: Scoring whether the structure is clear and directly addresses the query.

&nbsp;

---

## Analytics, Insights & Feedback

### User Behavior & Engagement

* **User Actions**: Frontends log thumbs-up/down feedback and custom comments directly into a Firestore collections table.  
* **Session Metrics**: Tracks session length and recurring usage trends to monitor clinical adoption.

### Operational & Business Intelligence

* **Usage & Cost**: Models log token consumption (prompt, completion, and cached tokens) to BigQuery, enabling precise cost projections.  
* **Performance Trends**: Captures TTFT (Time to First Token) and latency metrics per request.  
* **BI Dashboards**: Exported to Looker to visualize "North Star" performance and financial metrics.

### Observability & Audit

* **Logging**: FastAPI backend produces structured JSON logs containing trace IDs, exported directly to Cloud Logging.  
* **Audit Trails**: Immutable logs capture all sensitive transactions and data retrievals, ensuring compliance with clinical auditing requirements.

&nbsp;