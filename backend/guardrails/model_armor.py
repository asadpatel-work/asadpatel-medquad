"""Model Armor and HIPAA PHI/PII DLP Redaction Guardrail.

Protects multi-agent LLM systems against:
1. Adversarial Prompt Injections and Jailbreak Attacks.
2. Accidental exposure of Protected Health Information (PHI) via automated DLP redaction.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Heuristics for adversarial prompt injection / jailbreak attempts
JAILBREAK_PATTERNS = [
    re.compile(r"\b(ignore\s+(all\s+)?(previous|prior)\s+instructions)\b", re.IGNORECASE),
    re.compile(r"\b(disregard\s+(system\s+)?(prompt|rules|constraints))\b", re.IGNORECASE),
    re.compile(
        r"\b(you\s+are\s+now\s+(in\s+)?(dan|developer|jailbreak|unrestricted|uncensored)\s+mode)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(you\s+are\s+now\s+dan)\b", re.IGNORECASE),
    re.compile(r"\b(system\s+override\s*:\s*disable\s+safety)\b", re.IGNORECASE),
    re.compile(r"\b(reveal\s+(your\s+)?(system\s+prompt|hidden\s+instructions))\b", re.IGNORECASE),
    re.compile(
        r"\b(pretend\s+you\s+(have\s+no\s+(rules|safety|guardrails)|are\s+an?\s+uncensored))\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(admin\s+mode\s+enabled|bypass\s+model\s+armor)\b", re.IGNORECASE),
    re.compile(r"\b(ignore\s+medical\s+ethics)\b", re.IGNORECASE),
]

# HIPAA Safe Harbor De-identification Regex Patterns
PHI_PATTERNS = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
    (re.compile(r"\b(?:MRN|mrn)[-:\s]*([A-Z0-9]{6,10})\b", re.IGNORECASE), "MRN: [REDACTED_MRN]"),
    (re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[REDACTED_PHONE]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (
        re.compile(
            r"\b(?:DOB|dob|Date of Birth)[-:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", re.IGNORECASE
        ),
        "DOB: [REDACTED_DOB]",
    ),
    (
        re.compile(r"\b(?:Patient|patient)[-:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)\b"),
        "Patient: [REDACTED_NAME]",
    ),
]


@dataclass
class SanitizationResult:
    """Outcome of Model Armor input security audit."""

    is_safe: bool
    sanitized_text: str
    jailbreak_detected: bool = False
    redacted_phi_count: int = 0
    violations: list[str] = field(default_factory=list)


class ModelArmor:
    """Security guardrail layer enforcing prompt sanitization and PII/PHI redaction."""

    def sanitize(self, input_text: str) -> SanitizationResult:
        """Inspects and redacts prompt injections and PHI from inbound queries."""
        violations: list[str] = []
        jailbreak_found = False

        # 1. Prompt Injection Audit
        for pattern in JAILBREAK_PATTERNS:
            if pattern.search(input_text):
                jailbreak_found = True
                violations.append(f"Prompt injection pattern detected: {pattern.pattern}")
                logger.warning("Model Armor intercepted jailbreak attempt: '%s'", input_text[:100])

        if jailbreak_found:
            return SanitizationResult(
                is_safe=False,
                sanitized_text="",
                jailbreak_detected=True,
                redacted_phi_count=0,
                violations=violations,
            )

        # 2. PHI Redaction
        sanitized = input_text
        redaction_count = 0

        for pattern, replacement in PHI_PATTERNS:
            matches = pattern.findall(sanitized)
            if matches:
                redaction_count += len(matches)
                sanitized = pattern.sub(replacement, sanitized)

        if redaction_count > 0:
            logger.info("Model Armor redacted %d PHI tokens from input text.", redaction_count)

        return SanitizationResult(
            is_safe=True,
            sanitized_text=sanitized,
            jailbreak_detected=False,
            redacted_phi_count=redaction_count,
            violations=violations,
        )


# Global singleton
_model_armor_instance: ModelArmor | None = None


def get_model_armor() -> ModelArmor:
    global _model_armor_instance
    if _model_armor_instance is None:
        _model_armor_instance = ModelArmor()
    return _model_armor_instance
