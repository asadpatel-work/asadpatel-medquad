"""Deterministic Clinical Safe Refusal and Scope Lock Engine.

Enforces strict clinical research boundaries:
1. Rejects personal medical diagnostic inquiries ("Do I have lymphoma?").
2. Rejects individual treatment/prescription requests ("What dose of lisinopril should I take?").
3. Detects acute medical emergencies and provides emergency hotline guidance.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import StrEnum

logger = logging.getLogger(__name__)


class RefusalCategory(StrEnum):
    NONE = "none"
    PERSONAL_DIAGNOSIS = "personal_diagnosis"
    PRESCRIPTION_REQUEST = "prescription_request"
    EMERGENCY_CRISIS = "emergency_crisis"
    OFF_LABEL_DANGEROUS = "off_label_dangerous"


@dataclass
class SafeRefusalResult:
    """Outcome of safe refusal evaluation."""

    is_refusal: bool
    refusal_category: RefusalCategory = RefusalCategory.NONE
    refusal_message: str | None = None
    matched_patterns: list[str] = field(default_factory=list)


# Regular expression patterns for clinical boundary violations
DIAGNOSIS_PATTERNS = [
    re.compile(r"\b(diagnose\s+(me|my|this\s+condition|my\s+symptoms))\b", re.IGNORECASE),
    re.compile(
        r"\b(do\s+i\s+have\s+(cancer|lymphoma|diabetes|sepsis|a\s+tumor|a\s+stroke|a\s+heart\s+attack))\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(what\s+disease\s+do\s+i\s+have|what\s+disease\s+i\s+have|what\s+is\s+wrong\s+with\s+me)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(tell\s+me\s+what\s+disease(\s+i\s+have)?)\b", re.IGNORECASE),
    re.compile(
        r"\b(i\s+have\s+(a\s+lump|chest\s+pain|fever\s+and\s+night\s+sweats),\s+what\s+is\s+it)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(am\s+i\s+going\s+to\s+die|is\s+my\s+condition\s+fatal)\b", re.IGNORECASE),
]

PRESCRIPTION_PATTERNS = [
    re.compile(r"\b(prescribe\s+(me|for\s+me|a\s+medication|a\s+drug|pills|\w+))\b", re.IGNORECASE),
    re.compile(r"\b(give|write|provide)\s+(me\s+)?a\s+(prescription|script)\b", re.IGNORECASE),
    re.compile(r"\b(what\s+(dose|dosage)\s+(should\s+i\s+take|of))\b", re.IGNORECASE),
    re.compile(r"\b(how\s+much\s+(mg|tablets|pills)\s+should\s+i\s+take)\b", re.IGNORECASE),
    re.compile(
        r"\b(should\s+i\s+stop\s+taking\s+my|can\s+i\s+increase\s+my\s+dose)\b", re.IGNORECASE
    ),
    re.compile(r"\b(what\s+medicine\s+should\s+i\s+buy\s+for\s+my)\b", re.IGNORECASE),
]

EMERGENCY_PATTERNS = [
    re.compile(
        r"\b(heart\s+attack|cannot\s+breathe|can\'?t\s+breathe|crushing\s+chest\s+pain|severe\s+chest\s+pressure)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(sudden\s+numbness\s+in\s+face|slurred\s+speech|stroke)\b", re.IGNORECASE),
    re.compile(r"\b(suicide|overdose|overdosed|swallowed\s+poison)\b", re.IGNORECASE),
]

REFUSAL_MESSAGES = {
    RefusalCategory.PERSONAL_DIAGNOSIS: (
        "**Clinical Research Boundary Notice:** MedQuAD Assistant is an AI literature exploration tool "
        "designed for medical researchers and clinicians. It cannot evaluate individual patient symptoms "
        "or establish clinical diagnoses. If you are experiencing symptoms, please consult a licensed medical "
        "professional or primary care provider for comprehensive diagnostic evaluation."
    ),
    RefusalCategory.PRESCRIPTION_REQUEST: (
        "**Prescription Policy Notice:** MedQuAD Assistant cannot prescribe medications, adjust dosage regimens, "
        "or recommend pharmacological therapies for individual patients. Drug dosing must be determined by a licensed "
        "physician based on clinical indications, renal/hepatic function, and patient history."
    ),
    RefusalCategory.EMERGENCY_CRISIS: (
        "**EMERGENCY NOTICE:** If you or someone with you is experiencing a medical emergency (such as severe chest pain, "
        "difficulty breathing, sudden weakness, or acute distress), please call **911** or your local emergency number "
        "immediately, or proceed to the nearest emergency department."
    ),
}


class SafeRefusalEngine:
    """Evaluates queries against clinical safety boundaries and scope lock contracts."""

    def evaluate(self, query: str) -> SafeRefusalResult:
        """Evaluates query text and returns safe refusal classification."""
        cleaned = query.strip()

        # 1. Emergency Crisis Check (Highest Priority)
        for pattern in EMERGENCY_PATTERNS:
            if pattern.search(cleaned):
                return SafeRefusalResult(
                    is_refusal=True,
                    refusal_category=RefusalCategory.EMERGENCY_CRISIS,
                    refusal_message=REFUSAL_MESSAGES[RefusalCategory.EMERGENCY_CRISIS],
                    matched_patterns=[pattern.pattern],
                )

        # 2. Personal Diagnosis Check
        diag_matches = [p.pattern for p in DIAGNOSIS_PATTERNS if p.search(cleaned)]
        if diag_matches:
            return SafeRefusalResult(
                is_refusal=True,
                refusal_category=RefusalCategory.PERSONAL_DIAGNOSIS,
                refusal_message=REFUSAL_MESSAGES[RefusalCategory.PERSONAL_DIAGNOSIS],
                matched_patterns=diag_matches,
            )

        # 3. Prescription Request Check
        rx_matches = [p.pattern for p in PRESCRIPTION_PATTERNS if p.search(cleaned)]
        if rx_matches:
            return SafeRefusalResult(
                is_refusal=True,
                refusal_category=RefusalCategory.PRESCRIPTION_REQUEST,
                refusal_message=REFUSAL_MESSAGES[RefusalCategory.PRESCRIPTION_REQUEST],
                matched_patterns=rx_matches,
            )

        return SafeRefusalResult(is_refusal=False, refusal_category=RefusalCategory.NONE)


# Singleton instance
_safe_refusal_engine: SafeRefusalEngine | None = None


def get_safe_refusal_engine() -> SafeRefusalEngine:
    global _safe_refusal_engine
    if _safe_refusal_engine is None:
        _safe_refusal_engine = SafeRefusalEngine()
    return _safe_refusal_engine
