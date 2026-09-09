# MedQuAD Clinical Assistant — System Architecture Document

**Project:** MedQuAD Clinical Assistant  
**Simulated Customer:** National Institutes of Health (NIH) Clinical Center  
**Environment:** Argolis Sandbox (`fde-medquad-sandbox-dev`)  
**Lead FDE:** Google Cloud AI FDE  
**Status:** Approved Architecture (Sprint 1)

---

## 1. High-Level System Architecture

The MedQuAD Clinical Assistant is built on an asynchronous, multi-agent Supervisor-Worker topology hosted on serverless Google Cloud Run. It combines managed Retrieval-Augmented Generation (RAG) via Vertex AI Search over the authoritative NIH MedQuAD database with deterministic clinical safety guardrails.

```mermaid
graph TD
    User([Clinician / Medical Researcher]) -->|1. Natural Language Query| FE[React Frontend - TypeScript/Vite/Tailwind]
    FE -->|2. Secure Async SSE Request| BE[FastAPI Backend - Cloud Run]
    
    subgraph SecurityPerimeter [GCP Secure Sandbox & VPC-SC Perimeter]
        BE -->|3. Route & Authenticate| IAP[Identity-Aware Proxy / JWT Bearer]
        IAP -->|4. Input Sanitization| MA[Model Armor & PII / DLP Guardrails]
        MA -->|5. Forward Query| CO[Root Orchestrator Agent - Gemini 2.5 Flash]
        
        subgraph AgentTopology [Supervisor-Worker Multi-Agent Topology - Google ADK]
            CO -->|6a. Route Research Task| RA[Researcher Subagent - Gemini 2.5 Pro]
            CO -->|6b. Route Review & Quality Check| RE[Reviewer Subagent - Gemini 3.5 Flash]
            
            RA -->|7. MCP / SSE Tool Protocol| MCP[Model Context Protocol Server]
            MCP -->|8a. Semantic Query| SearchTool[Vertex AI Search Tool]
            MCP -->|8b. Mock EHR / Protocol Query| MockDBTool[Mock Clinical DB Tool]
        end
        
        SearchTool -->|9. Dense Retrieval| VAIS[(Vertex AI Search - MedQuAD Index)]
        VAIS -->|Indexed Documents| GCS[(GCS Bucket: MedQuAD Corpus)]
        MockDBTool -->|Simulated Patient Records| CS[(Cloud SQL PostgreSQL)]
        
        CO -->|10. Persist Session & Summaries| SessionDB[(PostgreSQL Session & Memory Store)]
        BE -->|11. Distributed Spans & Traces| OTEL[OpenTelemetry / Google Cloud Trace]
        BE -->|12. Telemetry & Cost Metrics| BQ[(BigQuery Telemetry Sink)]
    end
```

---

## 2. Multi-Agent Supervisor-Worker Topology (Google ADK)

The multi-agent system decouples high-level clinical routing, deep literature retrieval, and quality assurance into specialized autonomous agents:

```mermaid
sequenceDiagram
    autonumber
    actor Clinician as Clinician / Researcher
    participant FE as React Frontend
    participant Gateway as FastAPI / Guardrails
    participant Root as Root Orchestrator (Gemini 2.5 Flash)
    participant Researcher as Researcher Agent (Gemini 2.5 Pro)
    participant Tools as Search & DB Tools (MCP)
    participant Reviewer as Reviewer Agent (Gemini 3.5 Flash)

    Clinician->>FE: Ask Clinical Research Query
    FE->>Gateway: POST /api/v1/chat (stream=True)
    Gateway->>Gateway: Model Armor check & PII Masking
    Gateway->>Root: Forward sanitized clinical query
    
    Root->>Root: Intent Classification & Category Routing (e.g. Oncology)
    
    alt Diagnostic/Prescription Request
        Root-->>Gateway: Immediate Deterministic Safe Refusal ("Scope Lock")
        Gateway-->>FE: Stream Safe Refusal Notification
    else Valid Research Query
        Root->>Researcher: Delegate Research Task with Context
        loop ReAct Execution Loop
            Researcher->>Tools: Execute Semantic Search (MedQuAD)
            Tools-->>Researcher: Return Top-K Grounded NIH Chunks
            Researcher->>Tools: Query Mock Clinical DB (if protocol lookup needed)
            Tools-->>Researcher: Return Clinical Reference
        end
        Researcher-->>Root: Draft Response with Inline Citations [1], [2]
        
        Root->>Reviewer: Request Verification & Critique Pass
        Reviewer->>Reviewer: 1. Verify Citation Mapping (100% resolution)<br/>2. Fact Grounding Pass (0% Hallucination)<br/>3. Safe Persona Check
        Reviewer-->>Root: Quality Approved Response & Metric Scores
        
        Root-->>Gateway: Final Grounded Response + Citation Metadata
        Gateway-->>FE: Stream Tokens & Split-Pane Citation Data
        FE-->>Clinician: Render Interactive Answer & Side-by-Side NIH Source
    end
```

---

## 3. Clinical Safety & Guardrail Architecture

To adhere to clinical standards and prevent the model from dispensing unauthorized medical diagnosis or treatment advice, the assistant implements a defense-in-depth safety pipeline:

```mermaid
graph LR
    In([Inbound Query]) --> MA[1. Model Armor & DLP Filter]
    MA -->|Check Jailbreak / PII| SL[2. Scope Lock Prefix]
    SL -->|Check Refusal Regex| Router{Prescriptive Query?}
    
    Router -->|Yes| Refusal[Deterministic Safe Refusal Response]
    Router -->|No| ADK[Multi-Agent Generation Loop]
    
    ADK --> OutCheck[3. Output Grounding & Hallucination Check]
    OutCheck --> CitCheck[4. 1:1 Citation Link Verifier]
    CitCheck --> Approved([Grounded Output with Valid NIH Citations])
```

1. **Model Armor & DLP Filter**: Intercepts prompt injection attacks, jailbreak payloads, and masks any simulated PII/PHI.
2. **Scope Lock Prompt Contract**: Hardcoded system constraint forcing the model into an informative research persona and strictly forbidding medical prescriptions or personal health diagnoses.
3. **Deterministic Output Verifier**: Fast regex and semantic validator ensuring refusal language is triggered whenever therapeutic recommendations are requested.
4. **Citation Link Verifier**: Validates that all inline citation markers (`[1]`, `[2]`) resolve directly to valid, retrieved MedQuAD document chunks and URLs.

---

## 4. Grounding & Data Ingestion Pipeline

```mermaid
graph TD
    Raw[Raw NIH MedQuAD XML/JSON Datasets] --> Parser[MedQuAD Parser & Normalizer]
    Parser --> Classifier[Clinical Category Classifier]
    Classifier --> Chunker[Chunking Engine: 500 Tokens / 10% Overlap]
    Chunker --> GCS[(gs://fde-medquad-grounding-corpus-dev/)]
    GCS --> VAIS[(Vertex AI Search - GEAP Agent Engine)]
    
    Chunker --> LocalStore[(Local / CI Mock Vector Corpus)]
```

* **Dataset**: Authoritative NIH MedQuAD question-and-answer pairs covering diseases, treatments, molecular markers, and clinical guidelines.
* **Chunking Strategy**: 500-token chunks with 10% overlap (50 tokens) to ensure semantic continuity without splitting clinical sentences.
* **Dual-Mode Search Engine**:
  * **Production / Cloud Mode**: Managed Vertex AI Search (Discovery Engine) using `text-embedding-004`.
  * **Local / CI Mode**: In-memory vector retriever over `data/sample_medquad.json` for rapid testing and offline developer velocity.

---

## 5. Technology Stack & Infrastructure Mapping

| Layer | Component | Technology / GCP Service | Purpose |
| :--- | :--- | :--- | :--- |
| **Frontend** | Interactive Web UI | React 18, TypeScript, Vite, Tailwind CSS | Split-pane citation viewer, SSE streaming, feedback widgets |
| **API Gateway** | Backend Service | FastAPI, Uvicorn, Python 3.11+ | Asynchronous REST API, SSE streaming, middleware |
| **Agent Orchestration** | Supervisor & Workers | Google ADK, Gemini 2.5 Flash, Gemini 2.5 Pro, Gemini 3.5 Flash | Routing, ReAct research loop, quality control |
| **Tool Protocol** | Tool Server | Model Context Protocol (MCP) over SSE | Standardized, isolated tool execution |
| **Knowledge Engine** | RAG / Grounding | Vertex AI Search (GEAP), Cloud Storage (GCS) | Managed semantic index over NIH MedQuAD corpus |
| **Database** | Memory & Mock EHR | Cloud SQL PostgreSQL | Multi-turn session persistence, mock clinical database |
| **Security** | IAM & Guardrails | GCP Agent Runtime Model Armor, Secret Manager, IAP, KMS | Least-privilege IAM, PII redaction, CMEK encryption |
| **Observability** | Tracing & Telemetry | OpenTelemetry, Cloud Trace, Cloud Logging, BigQuery | Distributed latency tracing, token cost accounting |
| **Infrastructure as Code** | Provisioning | Terraform HCL, Docker, Cloud Run | 100% reproducible serverless deployment |
