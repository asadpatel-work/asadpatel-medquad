# Project Scope

# GenAI Co-Build Scope Agreement

# Cloud AI FDE Team

## Project Name

MedQuAD Clinical Assistant

## Engagement Type

Onboarding Project 1 (Healthcare Domain)

## Staging Environment

100% Self-Contained in Argolis Sandbox

&nbsp;

---

## Metadata

* **Customer Name**: National Institutes of Health (NIH) Clinical Center (Simulated)  
* **Agreement Date**: June 13, 2026  
* **Agreement Status**: Ready for Execution  
* **Customer Sponsor**: Dr. Elaine Vance (Chief Medical Information Officer, NIH)  
* **Google Sponsor**: GenAI FDE Manager (M1)  
* **Customer Lead**: Dr. Anand Jha (Lead Clinical Researcher, NIH)  
* **Google Lead**: FDE Pod Lead / Onboarding Buddy

&nbsp;

---

## Company Overview

The NIH Clinical Center is a major clinical research hospital utilizing cutting-edge biomedical technologies to translate scientific discoveries into clinical practice. The hospital employs thousands of researchers and clinicians who rely on authoritative medical literature, clinical protocols, and reference databases (such as MedQuAD) to make high-stakes, time-sensitive treatment decisions and write preclinical research dossiers.

&nbsp;

---

## Project Overview

### MedQuAD Clinical Assistant (AI Sandbox Initiative)

Lay the underlying foundation for clinical agentic capabilities by developing a secure, self-contained AI Clinical Research Sandbox.

&nbsp;

This engagement focuses on establishing a secure, scalable "AI Sandbox" inside the onboarding FDE's allocated Argolis Project. It empowers clinical researchers to build and iterate upon medical RAG agents rapidly and safely. The project will bridge the gap between researchers seeking conversational, natural language search over NIH guidelines and the strict regulatory compliance, security, and safety constraints of clinical environments.

&nbsp;

---

## Project Scope

| Scope / Deliverable | Responsible Party |
| :---- | :---- |
| Design of the Multi-Agent RAG Topology: Root Orchestrator with specialized sub-agents (e.g., General Medicine vs. Specialized Disease/Oncology agents). | Google FDE (Noogler) |
| Ingestion Pipeline & Grounding Index: Automated ingestion of the MedQuAD NIH medical Q\&A dataset into Vertex AI Search. | Google FDE (Noogler) |
| External API Tool Integrations: Simulating mock clinical databases and NIH research lookups with robust error-handling, rate-limiting, and retry logic. | Google FDE (Noogler) |
| Security & Safety Integrations: Implementation of SPIFFE-based Agent Identities, Secret Manager, and GCP Agent Runtime Model Armor to redact PII and prevent jailbreaks. | Google FDE (Noogler) |
| Observability Setup: Complete OpenTelemetry (OTEL) and Google Cloud Trace integration for end-to-end latency tracing. | Google FDE (Noogler) |
| Automated Verification: Development of a pytest suite with mocked LLM and Search APIs, achieving \>80% code coverage. | Google FDE (Noogler) |

### Out of Scope

* Direct write-back integrations into live, production Electronic Health Record (EHR) databases.  
* Processing of real, un-sanitized patient health records or active Personally Identifiable Information (PII) beyond mock clinical sandbox data.  
* Deployments beyond the allocated, self-contained Argolis Sandbox environment.

&nbsp;

---

## User Journey

1. **Clinical Query**: A clinical researcher inputs a natural language question (e.g., "What are the primary symptoms and diagnostic markers of Stage II Hodgkin Lymphoma?").  
2. **Intent Classification & Routing**: The Root Orchestrator Agent (ADK) parses the query, identifies the topic, and routes it to the specialized "Oncology" subagent.  
3. **Grounded Retrieval (RAG)**: The subagent invokes its search tool, querying Vertex AI Search loaded with the MedQuAD dataset, and retrieves grounded NIH text snippets.  
4. **Safety Verification**: The retrieved facts are checked against safety guardrails to ensure the response adopts a strictly informative persona and prevents medical diagnosis.  
5. **Grounded Generation**: The agent returns a structured, factual answer containing inline citations pointing back to the original NIH medical document, rendered dynamically in a split-pane source viewer on the frontend.

&nbsp;

---

## Objectives

### Business Objectives

* **Reduce Research Time**: Divert clinicians' time away from manual literature searches, reducing preclinical research compilation time by \>60%.  
* **Demonstrate Agentic Viability**: Demonstrate the viability of minimally hallucination agentic workflows in clinical settings, establishing a path toward automated patient protocol indexing.  
* **Create Sales-Enablement Asset**: Establish an active sales-enablement asset inside the NeuraVibe Demo Library to showcase GCP's capabilities to future healthcare executives.

### Technical Objectives

* **Maintain Medical Boundaries**: Prove that a multi-agent ADK topology can maintain strict medical boundaries using custom system personas.  
* **Validate RAG Accuracy**: Validate the accuracy of managed GEAP Agent Search (Vertex AI Search) RAG pipelines, achieving \>90% Grounding Recall against a clinical evaluation dataset.  
* **Containerized Deployment**: Deploy a 100% self-contained, containerized application to Google Cloud Run utilizing Terraform.

&nbsp;

---

## Timeline

| Sprint | Phase | User Stories | Tasks & Owners |
| :---- | :---- | :---- | :---- |
| **Sprint 1** | **Tactical (Discovery)** | As a developer, I want to initialize my git repo, draft my architecture diagrams, and configure my MedQuAD grounding index in Vertex AI Search. | Initialize Repo, configure GCS & Vertex AI Search schema. (FDE Noogler) |
| **Sprint 2** | **Tactical (Grounding)** | As an engineer, I want to build the automated ingestion pipeline to index MedQuAD XML files into Vertex AI Search and verify citation mapping. | Write parsing scripts, build RAG grounding checks. (FDE Noogler) |
| **Sprint 3** | **Strategic (Orchestration)** | As a developer, I want to build the ADK Root Agent, construct subagents, and configure custom tool-calling against mock literature APIs. | Develop ADK agents, integrate mock API tools. (FDE Noogler) |
| **Sprint 4** | **Strategic (Security & Evals)** | As a developer, I want to integrate Agent Runtime Model Armor and Secret Manager, build OpenTelemetry tracing, and write a pytest suite. | Configure Model Armor, Secret Manager, OpenTelemetry, and write pytests. (FDE Noogler) |
| **Sprint 5** | **Strategic (Deployment)** | As an engineer, I want to containerize my app with Docker, script my Terraform HCL, and deploy to Google Cloud Run. | Write Dockerfile, Terraform, and execute deployment. (FDE Noogler) |
| **Sprint 6** | **Disengagement** | As a builder, I want to run my Product Readiness Review (PRR) readout, sanitize my code, and transition assets to NeuraVibe. | Run PRR readout with Lead, upload clean code to //FDE\_shared. (FDE Noogler) |

&nbsp;

---

## Technical Requirements

### Onboarding (Model A \- In-Environment)

* Provisioning occurs inside the FDE's allocated Argolis Project sandbox.  
* Access to the GTM Cloud-GTM GitHub Enterprise organization.  
* Development completed using JetSki / AGY 2.0 with Gemini 3.5 Flash assistance.

### Data Sources

* **Primary Corpus**: MedQuAD (NIH authorized clinical Q\&A dataset).  
* **Storage**: Staged in GCS buckets feeding directly into Vertex AI Search.  
* **Data Policy**: 100% synthetic or public NIH data. Strictly zero live patient data or actual PII.

### Integration Points

* **GEAP Agent Search (fka Vertex AI Search)**: For fetching grounded literature references with citations.

### Technology Requirements

* **Runtime**: Python 3.11+ / FastAPI  
* **Frontend**: React 18+ / TypeScript / Tailwind CSS  
* **Orchestration**: Google ADK / AGY SDK  
* **Models**: Gemini 2.5 Pro (for clinical reasoning), Gemini 2.5 Flash (for routing), Gemini 3.5 Flash (for coding and evals)  
* **Infrastructure**: Google Cloud Run, Cloud Storage, BigQuery, Secret Manager, VPC Service Controls, OpenTelemetry, Cloud Trace

&nbsp;

---

## Working Methodology and Environment Requirements

This project follows **Model A: In-Environment Development**.

&nbsp;

* **Development Environment**: Complete development staged inside the secure Argolis sandbox.  
* **Tooling**: Access to JetSki IDE and Gemini 3.5 Flash for code generation and refactoring.  
* **Infrastructure**: Dedicated GCP Dev Project (`fde-medquad-sandbox-dev`) with Vertex AI, Cloud Run, GCS, BigQuery, and Secret Manager APIs active.  
* **Identity/IAM**: Granular, SPIFFE-based per-agent identities. Enforced Least-Privilege IAM roles for the service accounts.  
* **Data Policy**: No production EHR data or patient PII.

&nbsp;

---

## Team, Cadence, and Logistics

* **Manager (M1)**: General oversight, milestone gates, and PRR escalation.  
* **Pod Lead / Buddy**: Strategic advisor, code reviews, and PR approvals (50-70% technical contribution).  
* **Core Builder (Noogler)**: Tactical owner of the end-to-end SDLC and final deliverable.  
* **Daily Rhythm**: 15-minute morning standup. Weekly status review and code walkthroughs.  
* **Communication Channel**: Shared Google Chat Space (`fde-onboard-medquad`).

&nbsp;

---

## Success Metrics & Transition Plan

### Success Criteria (The "Definition of Done")

* **Functional Verification**: Average score of 2-Competent across all FDE grading categories.  
  * \>=90% Grounding Recall on the MedQuAD evaluation dataset.  
  * 0% Hallucinations on critical medical facts (Strict Grounding Enforcement).  
  * \<2.5s End-to-End latency on clinical responses.  
* **Operational Verification**: Containerized via Docker, provisioned entirely via Terraform, and successfully deployed to Google Cloud Run.  
* **Observability**: Completed OpenTelemetry and Cloud Trace setup, export to BigQuery telemetry, and operational logging.

### Transition Plan

* **Platform Extraction**: Upon successful completion of Milestone 5, the Noogler enters the mandated 1-week Squad Cooldown.  
* **Sanitation & Harvesting**: The Noogler generalizes the clinical routing configurations, removes domain-specific secrets, and pushes the reusable components to the FDE central repository (`//FDE_shared/agent_engineering/`).  
* **Asset Registration**: The containerized mock environment is published to the NeuraVibe Demo Library and transitioned to the GTM demo operations team for sales enablement.

&nbsp;