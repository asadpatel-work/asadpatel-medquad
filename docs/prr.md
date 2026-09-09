# Production Readiness Review (PRR): MedQuAD Clinical Research Assistant

## 1. System Architecture & Boundaries
* **Service Description:** High-concurrency, grounded multi-agent clinical research assistant utilizing Gemini 2.5 Pro / Flash models over NIH MedQuAD, Vertex AI Search, and MCP tool protocols.
* **Service Tier:** Critical Enterprise Internal Tier (Clinical Informatics & Academic Research).
* **Target SLA / SLO:** 99.9% uptime, p95 latency < 3500ms, 100% citation validity, 0% unhandled prompt injections.

---

## 2. Security & Compliance
* **HIPAA Compliance & DLP:**
  * Client-side & server-side regex/semantic masking for 18 HIPAA Safe Harbor identifiers (SSN, MRN, Name, Phone, Email, DOB).
  * Zero persistent storage of unmasked raw patient identifiable information.
* **Model Armor & Prompt Injection Defense:**
  * Pre-execution inspection blocks jailbreaks, DAN prompts, and instruction overrides before invoking foundation models.
* **IAM & Least Privilege:**
  * Dedicated runtime service account (`sa-medquad-runtime`) scoped with minimal required roles (`roles/aiplatform.user`, `roles/discoveryengine.editor`, `roles/bigquery.dataEditor`, `roles/cloudtrace.agent`).
  * API keys and secrets managed via Google Cloud Secret Manager.

---

## 3. Observability & Telemetry
* **Distributed Tracing:**
  * Instrumenting FastAPI endpoints, subagent delegation spans, tool calls, and LLM requests via OpenTelemetry Python SDK.
  * Spans exported directly to Google Cloud Trace with trace context propagation (`X-Request-ID`, `session_id`).
* **Structured Logging:**
  * Google Cloud Logging formatter emitting structured JSON logs with log severity levels (`INFO`, `WARNING`, `ERROR`).
* **FinOps & Cost Accounting:**
  * Background telemetry pipeline writes token usage (prompt, completion, cached) and calculated query cost to BigQuery table `telemetry.agent_metrics`.

---

## 4. Scalability & Resilience
* **Autoscaling:**
  * Cloud Run containers configured with min instances = 1 (to eliminate cold starts for critical research) and max instances = 10 with automatic scaling on CPU/concurrency.
* **Fallback Mechanisms:**
  * Dual-mode retrieval engine supporting primary Vertex AI Search with local vector store / TF-IDF index fallback.
  * Deterministic high-fidelity synthesis fallback if external API rate limits or network partitions occur.
* **Graceful Degradation:**
  * Circuit breakers and exponential backoff retry logic on all clinical database lookups and external tool endpoints.

---

## 5. Deployment & Release Management
* **Infrastructure as Code:** 100% codified via Terraform (`terraform/main.tf`, `terraform/variables.tf`, `terraform/outputs.tf`).
* **Containerization:** Multi-stage Docker builds for backend and frontend (`Dockerfile.backend`, `Dockerfile.frontend`).
* **Automated CI/CD Gates:**
  * Linting with Ruff (`uv run ruff check .`).
  * Automated testing with Pytest (`uv run pytest --cov=backend`).
  * Quality Gates: Code coverage $\ge 80\%$, ROUGE-L $\ge 0.40$, BLEU $\ge 0.35$, Entity F1 $\ge 0.75$, Safe Refusal $= 100\%$.
