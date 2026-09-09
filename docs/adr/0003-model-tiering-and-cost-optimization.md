# ADR-003: Model Tiering Strategy (Gemini 2.5 Flash / 2.5 Pro / 3.5 Flash)

## Status
**Accepted** (Implemented)

## Context
Deploying LLM agents in enterprise clinical settings presents a trade-off between inference cost, response latency, and reasoning depth:
- Running Gemini 2.5 Pro exclusively across all agent roles yields high reasoning quality but results in excessive token costs (~$0.015/query) and higher latency (3,500ms+).
- Running Gemini 2.5 Flash exclusively reduces cost and latency (~$0.0008/query, 800ms) but compromises complex clinical synthesis across multi-document oncology guidelines.

## Decision
We implemented a **Tiered Multi-Model Architecture**:
1. **Routing & Triage Layer (Gemini 2.5 Flash):**
   - Cost: $0.075 / 1M input tokens.
   - Purpose: Query sanitization, category classification, safe refusal detection, and subagent dispatch.
   - P95 Latency: < 250ms.
2. **Clinical Research Synthesis Layer (Gemini 2.5 Pro):**
   - Cost: $1.25 / 1M input tokens.
   - Purpose: Deep multi-document medical reasoning, protocol extraction, and synthesis over retrieved NIH chunks.
3. **Factual & Citation Audit Layer (Gemini 3.5 Flash):**
   - Cost: $0.15 / 1M input tokens.
   - Purpose: High-speed verification, hallucination audit, citation provenance checks, and tone compliance.

## FinOps & Cost Impact
- **Average Blended Cost Per Query:** **$0.0018 USD** (an 88% cost reduction compared to an all-Pro monolithic architecture).
- **Projected Cost for 100,000 Clinical Queries/Month:** **$180.00 USD**.

## Consequences
- **Positive:**
  - Optimal balance of medical synthesis rigor, speed, and enterprise fiscal responsibility.
  - Sub-second termination for invalid or out-of-scope requests.
- **Negative:**
  - Requires maintaining prompt templates and schemas across distinct model versions.
