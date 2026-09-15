"""Model Armor and HIPAA PHI/PII DLP Redaction Guardrail.

Protects multi-agent LLM systems against:
1. Adversarial Prompt Injections and Jailbreak Attacks.
2. Accidental exposure of Protected Health Information (PHI) via automated DLP redaction.

Integrates with the official Google Cloud Model Armor managed service (modelarmor.googleapis.com)
with deterministic local fallback when running offline or in unit test suites.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from backend.core.config import get_settings

logger = logging.getLogger(__name__)

# Heuristics for adversarial prompt injection / jailbreak attempts (offline fallback)
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

# HIPAA Safe Harbor De-identification Regex Patterns (offline fallback)
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
    source: str = "local_fallback"  # "gcp_model_armor" or "local_fallback"


class ModelArmor:
    """Security guardrail layer enforcing prompt sanitization and PII/PHI redaction.

    Supports both Google Cloud Model Armor managed API (modelarmor.googleapis.com)
    and deterministic local regex/heuristic inspection as resilient fallback.
    """

    def __init__(
        self,
        project_id: str | None = None,
        location: str | None = None,
        template_id: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.settings = get_settings()
        self.project_id = (
            project_id
            or self.settings.model_armor_project_id
            or self.settings.gcp_project_id
        )
        self.location = (
            location
            or self.settings.model_armor_location
            or self.settings.gcp_region
        )
        self.template_id = template_id or self.settings.model_armor_template_id
        self._custom_client = client
        self._client: Any = None
        self._initialized = False

    @property
    def is_gcp_configured(self) -> bool:
        """Indicates whether GCP Model Armor template credentials are fully configured."""
        return bool(self.settings.enable_model_armor and self.project_id and self.template_id)

    def _get_client(self) -> Any:
        if self._custom_client is not None:
            return self._custom_client
        if not self._initialized:
            self._initialized = True
            try:
                import google.auth
                from google.api_core.client_options import ClientOptions
                from google.cloud import modelarmor_v1

                endpoint = f"modelarmor.{self.location}.rep.googleapis.com"
                creds = None
                try:
                    import google.auth.transport.requests

                    creds, _ = google.auth.default(
                        scopes=["https://www.googleapis.com/auth/cloud-platform"]
                    )
                    request = google.auth.transport.requests.Request()
                    creds.refresh(request)
                except Exception as e:
                    logger.debug("google.auth.default() refresh error: %s", e)
                    creds = None

                if creds is None:
                    try:
                        import subprocess
                        from google.oauth2 import credentials

                        token = (
                            subprocess.check_output(
                                ["gcloud", "auth", "print-access-token"],
                                stderr=subprocess.DEVNULL,
                            )
                            .decode()
                            .strip()
                            .split("\n")[-1]
                        )
                        if token and token.startswith("ya29."):
                            creds = credentials.Credentials(token)
                    except Exception:
                        pass

                self._client = modelarmor_v1.ModelArmorClient(
                    transport="rest",
                    credentials=creds,
                    client_options=ClientOptions(api_endpoint=endpoint),
                )
                logger.info(
                    "Connected to GCP Model Armor client at %s (template: %s)",
                    endpoint,
                    self.template_id,
                )
            except Exception as e:
                logger.warning(
                    "Could not initialize GCP Model Armor client (%s). Using local fallback.", e
                )
                self._client = None
        return self._client

    def _sanitize_via_gcp(self, input_text: str) -> SanitizationResult | None:
        """Attempts prompt sanitization via Google Cloud Model Armor API."""
        try:
            client = self._get_client()
            if not client:
                return None

            from google.cloud import modelarmor_v1

            template_name = (
                f"projects/{self.project_id}/locations/{self.location}/templates/{self.template_id}"
            )
            req = modelarmor_v1.SanitizeUserPromptRequest(
                name=template_name,
                user_prompt_data=modelarmor_v1.DataItem(text=input_text),
            )
            resp = client.sanitize_user_prompt(request=req)
            result = resp.sanitization_result

            violations: list[str] = []
            jailbreak_detected = False
            redacted_count = 0
            sanitized_text = input_text

            # Inspect filter results
            for filter_name, filter_res in result.filter_results.items():
                # 1. Prompt Injection / Jailbreak check
                if "pi_and_jailbreak" in filter_name or hasattr(
                    filter_res, "pi_and_jailbreak_filter_result"
                ):
                    pj = getattr(filter_res, "pi_and_jailbreak_filter_result", None)
                    if pj and pj.match_state == modelarmor_v1.FilterMatchState.MATCH_FOUND:
                        jailbreak_detected = True
                        violations.append("GCP Model Armor: Prompt Injection / Jailbreak detected.")

                # 2. Sensitive Data Protection (DLP / HIPAA PHI check)
                if "sdp" in filter_name or hasattr(filter_res, "sdp_filter_result"):
                    sdp = getattr(filter_res, "sdp_filter_result", None)
                    if sdp:
                        deid = getattr(sdp, "deidentify_result", None)
                        if deid and deid.data and deid.data.text:
                            sanitized_text = deid.data.text
                            redacted_count = len(deid.info_types) if deid.info_types else 1

            # Overall match state check
            if (
                result.filter_match_state == modelarmor_v1.FilterMatchState.MATCH_FOUND
                and jailbreak_detected
            ):
                return SanitizationResult(
                    is_safe=False,
                    sanitized_text="",
                    jailbreak_detected=True,
                    redacted_phi_count=0,
                    violations=violations,
                    source="gcp_model_armor",
                )

            return SanitizationResult(
                is_safe=True,
                sanitized_text=sanitized_text,
                jailbreak_detected=False,
                redacted_phi_count=redacted_count,
                violations=violations,
                source="gcp_model_armor",
            )
        except Exception as exc:
            logger.warning(
                "GCP Model Armor API call failed (%s). Falling back to local guardrail.", exc
            )
            return None

    def sanitize(self, input_text: str) -> SanitizationResult:
        """Inspects and redacts prompt injections and PHI from inbound queries.

        Attempts GCP Model Armor first if configured; falls back to deterministic local engine.
        """
        if self.is_gcp_configured:
            gcp_result = self._sanitize_via_gcp(input_text)
            if gcp_result is not None:
                return gcp_result

        # Local Fallback
        return self._sanitize_local(input_text)

    def _sanitize_local(self, input_text: str) -> SanitizationResult:
        """Local deterministic DLP and prompt injection guardrail pass."""
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
                source="local_fallback",
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
            source="local_fallback",
        )


# Global singleton
_model_armor_instance: ModelArmor | None = None


def get_model_armor() -> ModelArmor:
    global _model_armor_instance
    if _model_armor_instance is None:
        _model_armor_instance = ModelArmor()
    return _model_armor_instance
