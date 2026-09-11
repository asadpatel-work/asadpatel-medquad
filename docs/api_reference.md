# MedQuAD Clinical Assistant: API Reference & Developer Guide

This document provides a contract-first integration guide for the **MedQuAD Clinical Assistant REST API**, compliant with OpenAPI 3.1.0 specifications.

The full schema is exported at [`docs/openapi.json`](docs/openapi.json) and served interactively via Swagger UI at `/docs` and ReDoc at `/redoc`.

---

## 1. Authentication & Base URLs

* **Production Base URL:** `https://medquad-backend-dhwfxdn3vq-uc.a.run.app`
* **Local Development Base URL:** `http://localhost:8000`
* **Authentication:** Google Cloud IAM Invoker authorization via OIDC Identity Token or Bearer Token:
  ```bash
  export TOKEN=$(gcloud auth print-identity-token --audiences="https://medquad-backend-dhwfxdn3vq-uc.a.run.app")
  curl -H "Authorization: Bearer ${TOKEN}" https://medquad-backend-dhwfxdn3vq-uc.a.run.app/healthz
  ```

---

## 2. API Endpoints

### 2.1 System Health & Liveness
#### `GET /healthz`
Returns service availability, deployed version, and environment.

**Response `200 OK`:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "production",
  "datastore_id": "medquad-corpus-v1"
}
```

---

### 2.2 Clinical Chat & Reasoning Engine
#### `POST /api/v1/chat`
Invokes the multi-agent supervisor-worker workflow with Model Armor sanitization, NIH knowledge retrieval, and peer review.

**Request Body:**
```json
{
  "message": "What are the clinical staging indicators for Hodgkin Lymphoma?",
  "session_id": "optional-uuid-v4",
  "stream": false
}
```

**Response `200 OK`:**
```json
{
  "session_id": "4b6dfa99-823c-4cf0-8b16-43b9e4a38fae",
  "response": "Hodgkin Lymphoma staging uses the Ann Arbor Staging System [1]...",
  "citations": [
    {
      "id": "CancerGov_QA_q1_c1",
      "title": "Hodgkin Lymphoma - Staging and Diagnosis",
      "url": "https://cancer.gov/types/lymphoma",
      "authoritative_org": "National Cancer Institute (NCI / CancerGov)"
    }
  ],
  "latency_ms": 1420.5,
  "safe_refusal": false
}
```

*Note: For Server-Sent Events (SSE), pass `"stream": true` to receive real-time incremental tokens and agent thought events.*

---

### 2.3 Session Lifecycle
#### `POST /api/v1/sessions`
Creates an isolated clinical consultation session.

#### `GET /api/v1/sessions/{session_id}`
Retrieves consultation history, audit logs, and message traces.

#### `DELETE /api/v1/sessions/{session_id}`
Deletes session history from runtime memory and storage.

---

### 2.4 Clinician Feedback & RLHF Telemetry
#### `POST /api/v1/feedback`
Submits qualitative clinician review ratings (1 for thumbs up, -1 for thumbs down).

**Request Body:**
```json
{
  "session_id": "4b6dfa99-823c-4cf0-8b16-43b9e4a38fae",
  "turn_index": 0,
  "rating": 1,
  "comments": "Accurate staging criteria and verified NIH citations."
}
```

#### `GET /api/v1/feedback/metrics`
Returns aggregate satisfaction metrics.

---

### 2.5 Post-Hoc Conversation Auditing & Validation
#### `POST /api/v1/evaluations/validate`
Executes post-hoc validation across stored conversations assessing faithfulness, clinical relevance, and safety. Invoked automatically every night at 00:00 UTC by Google Cloud Scheduler.

**Request Body:**
```json
{
  "session_id": null,
  "min_faithfulness": 3.5,
  "min_relevance": 3.5
}
```

**Response `200 OK`:**
```json
{
  "timestamp": "2026-09-11T00:00:00Z",
  "total_sessions_audited": 14,
  "total_turns_audited": 42,
  "overall_pass_rate": 1.0,
  "citation_verification_rate": 1.0,
  "safety_refusal_pass_rate": 1.0,
  "status": "passed"
}
```

#### `GET /api/v1/evaluations/reports/latest`
Returns the latest audit summary and markdown report.

---

### 2.6 MedQuAD Corpus Ingestion & Grounding
#### `POST /api/v1/ingestion/run`
Triggers full or incremental parsing of raw NIH MedQuAD XML files, 500-token semantic chunking, GCS upload, and Discovery Engine datastore import.

**Request Body:**
```json
{
  "raw_dir": "data/medquad_raw",
  "sync_vertex": true
}
```

**Response `200 OK`:**
```json
{
  "status": "completed",
  "total_raw_files_scanned": 11274,
  "total_qa_pairs_extracted": 16407,
  "total_chunks_generated": 18920,
  "gcs_uri": "gs://capstone-506616-medquad-corpus/corpus/medquad_documents_20260911_162500.jsonl",
  "datastore_id": "medquad-corpus-v1",
  "discovery_engine_op": "projects/capstone-506616/locations/global/collections/default_collection/dataStores/medquad-corpus-v1/branches/default_branch/operations/import-9923812",
  "duration_seconds": 12.4
}
```

#### `GET /api/v1/ingestion/status`
Returns metadata regarding local and cloud corpus availability.

---

## 3. Python SDK Quickstart

```python
import requests

BASE_URL = "https://medquad-backend-dhwfxdn3vq-uc.a.run.app"
TOKEN = "YOUR_GCP_IDENTITY_TOKEN"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

# 1. Query the clinical assistant
response = requests.post(
    f"{BASE_URL}/api/v1/chat",
    headers=headers,
    json={"message": "What is the recommended treatment for essential hypertension?"},
)

data = response.json()
print("Synthesis:\n", data["response"])
print("\nVerified Citations:")
for c in data["citations"]:
    print(f"- [{c['id']}] {c['title']} ({c['authoritative_org']}): {c['url']}")
```
