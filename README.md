# MedQuAD Clinical Decision Support Assistant

An enterprise-grade multi-agent clinical decision support system powered by **Google Agent Development Kit (ADK)**, **Gemini 2.5 Pro**, **Gemini 2.5 Flash**, and grounded on the authoritative **NIH MedQuAD** corpus via **Vertex AI Search**.

## Architecture Overview

- **Supervisor Agent (Gemini 2.5 Flash / Google ADK):** Enforces Model Armor security, PII/PHI sanitization, and clinical safety scope locks before orchestrating specialized subagents.
- **Researcher Agent (Gemini 2.5 Pro / Google ADK):** Retrieves authoritative medical passages from the NIH MedQuAD corpus using Vertex AI Search and synthesizes evidence-grounded clinical responses.
- **Reviewer Agent (Gemini 3.5 Flash / Google ADK):** Audits draft responses for strict citation validity, detects hallucinations, and ensures non-prescriptive, objective medical communication.
- **Enterprise Security & Observability:** Google Cloud Model Armor, Identity-Aware Proxy (IAP), Cloud Trace (OpenTelemetry), and BigQuery telemetry.

## Quickstart

```bash
# Install dependencies
uv pip install -e ".[dev]"

# Run tests
pytest tests/unit/ -v

# Run backend locally
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
