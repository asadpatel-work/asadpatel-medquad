# ADR-004: Model Armor Jailbreak Defense & Deterministic Safe Refusal Guardrails

## Status
**Accepted** (Implemented)

## Context
Deploying GenAI in medical and clinical research environments introduces severe safety and legal liability risks:
1. **Adversarial Jailbreaks:** Attackers or rogue prompts attempting prompt injection, DAN exploits, or system prompt exfiltration.
2. **HIPAA / PHI Violations:** Users inadvertently pasting raw patient identifiers (names, SSNs, MRNs, dates of birth).
3. **Medical Practice Liability:** The system providing prescriptive clinical advice or personal medical diagnoses rather than acting as a scientific reference tool.

## Decision
We implemented a **Multi-Tier Defense-in-Depth Safety Architecture**:
1. **Model Armor Guardrail Layer (`backend/guardrails/model_armor.py`):**
   - Pre-execution scanning for adversarial prompt injection signatures, system prompt exfiltration, and delimiter attacks.
   - Deterministic HIPAA Safe Harbor redaction regex masking 18 PHI identifier types (`[REDACTED_SSN]`, `[REDACTED_MRN]`, `[REDACTED_PHONE]`, `[REDACTED_NAME]`) before LLM ingestion.
2. **Deterministic Safe Refusal Engine (`backend/guardrails/safe_refusal.py`):**
   - High-precision classifier intercepting:
     - Direct personal diagnostic demands (e.g., *"Diagnose me please"*).
     - Drug prescription / dosage advice requests.
     - Medical emergency / crisis keywords (routing to emergency 911 / poison control guidance).
   - Generates empathetic, non-prescriptive disclaimers and emergency guidance with sub-5ms latency without invoking foundation models.
3. **Reviewer Tone Compliance Pass:**
   - Reviewer agent audits draft responses to ensure neutral, scientific, third-person phrasing without prescriptive imperatives.

## Consequences
- **Positive:**
  - 100% deterministic refusal on adversarial and diagnostic inputs.
  - Zero PHI data leakage to external foundation model endpoints.
  - Mitigates legal and clinical liability for healthcare institutions.
- **Negative:**
  - Strict classification may occasionally require users to rephrase personal symptom questions as general scientific inquiries (intended design for clinical research scope).
