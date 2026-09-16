"""Google Cloud Identity-Aware Proxy (IAP) Authentication & JWT Verification.

Enforces Zero-Trust Institutional Single Sign-On (SSO) by validating:
1. `X-Goog-Authenticated-User-Email` header passed by Google Front End.
2. `X-Goog-IAP-JWT-Assertion` cryptographically signed by Google's private key.
3. Token audience claim matching the Google Cloud Backend Service ID.
4. Token issuer matching https://cloud.google.com/iap.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import requests
from fastapi import HTTPException, Request, status
from google.auth import jwt as google_jwt

from backend.core.config import get_settings

logger = logging.getLogger(__name__)

# Public URL for Google Cloud IAP public keys
IAP_JWK_URL = "https://www.gstatic.com/iap/verify/public_key"
IAP_KEY_CACHE_TTL_SECONDS = 3600  # 1 hour cache


@dataclass
class AuthenticatedClinician:
    """Represents a validated clinician identity forwarded through Google Cloud IAP."""

    email: str
    user_id: str
    is_authenticated: bool = True
    auth_source: str = "google_iap"  # "google_iap", "dev_bypass", or "anonymous"
    claims: dict[str, Any] = field(default_factory=dict)

    @property
    def display_name(self) -> str:
        if "@" in self.email:
            return self.email.split("@")[0].replace(".", " ").title()
        return self.email


class IAPVerifier:
    """Validates Google Cloud IAP cryptographically signed JWT assertion tokens."""

    def __init__(self, keys_url: str = IAP_JWK_URL, cache_ttl: int = IAP_KEY_CACHE_TTL_SECONDS) -> None:
        self.keys_url = keys_url
        self.cache_ttl = cache_ttl
        self._keys_cache: dict[str, str] = {}
        self._last_fetched_time: float = 0.0

    def get_public_keys(self) -> dict[str, str]:
        """Fetches and caches Google IAP public key certificates."""
        now = time.time()
        if not self._keys_cache or (now - self._last_fetched_time) > self.cache_ttl:
            try:
                resp = requests.get(self.keys_url, timeout=5)
                resp.raise_for_status()
                self._keys_cache = resp.json()
                self._last_fetched_time = now
                logger.info("Successfully fetched %d Google IAP public keys", len(self._keys_cache))
            except Exception as e:
                logger.warning("Failed to fetch Google IAP public keys from %s: %s", self.keys_url, e)
                if not self._keys_cache:
                    return {}
        return self._keys_cache

    def verify_token(
        self,
        token: str,
        expected_audience: str | None = None,
        expected_issuer: str = "https://cloud.google.com/iap",
    ) -> dict[str, Any]:
        """Cryptographically verifies an IAP JWT assertion and returns decoded claims."""
        certs = self.get_public_keys()
        if not certs:
            raise ValueError("Unable to obtain Google IAP public verification keys")

        # Verify signature, expiration, and audience using google.auth.jwt
        audience_to_verify = expected_audience if expected_audience else None
        claims = google_jwt.decode(
            token,
            certs=certs,
            verify=True,
            audience=audience_to_verify,
        )

        # Verify issuer
        if claims.get("iss") != expected_issuer:
            raise ValueError(f"Invalid IAP JWT issuer: expected {expected_issuer}, got {claims.get('iss')}")

        return claims


# Singleton verifier instance
_iap_verifier = IAPVerifier()


def get_iap_verifier() -> IAPVerifier:
    """Returns the singleton IAPVerifier."""
    return _iap_verifier


def _clean_google_identity(identity: str) -> str:
    """Removes 'accounts.google.com:' prefix commonly added by Google IAP."""
    if identity.startswith("accounts.google.com:"):
        return identity.split("accounts.google.com:", 1)[1]
    return identity


async def get_current_clinician(request: Request) -> AuthenticatedClinician:
    """FastAPI dependency extracting and authenticating clinician identity from IAP headers."""
    settings = get_settings()

    raw_email_header = request.headers.get("x-goog-authenticated-user-email")
    raw_user_id_header = request.headers.get("x-goog-authenticated-user-id")
    jwt_assertion = request.headers.get("x-goog-iap-jwt-assertion")

    # If IAP is enabled, enforce cryptographic assertion verification
    if settings.enable_iap:
        if not jwt_assertion:
            # Check development bypass rule
            if settings.environment == "development" and settings.iap_allow_anonymous_in_dev:
                dev_email = _clean_google_identity(raw_email_header) if raw_email_header else "dev-clinician@medquad.local"
                dev_id = _clean_google_identity(raw_user_id_header) if raw_user_id_header else "dev-user-001"
                logger.debug("IAP dev bypass: Using simulated clinician %s", dev_email)
                return AuthenticatedClinician(
                    email=dev_email,
                    user_id=dev_id,
                    is_authenticated=True,
                    auth_source="dev_bypass",
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required: Missing Google IAP identity assertion header.",
                headers={"WWW-Authenticate": "IAP"},
            )

        try:
            verifier = get_iap_verifier()
            expected_aud = settings.iap_audience if settings.iap_audience else None
            claims = verifier.verify_token(
                token=jwt_assertion,
                expected_audience=expected_aud,
                expected_issuer=settings.iap_expected_issuer,
            )
            email = _clean_google_identity(claims.get("email", raw_email_header or "unknown@hospital.org"))
            user_id = _clean_google_identity(claims.get("sub", raw_user_id_header or "unknown-sub"))
            return AuthenticatedClinician(
                email=email,
                user_id=user_id,
                is_authenticated=True,
                auth_source="google_iap",
                claims=claims,
            )
        except Exception as exc:
            logger.error("Failed to verify Google IAP assertion: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google IAP identity assertion: {exc}",
                headers={"WWW-Authenticate": "IAP"},
            ) from exc

    # If IAP is disabled, check if headers were provided by proxy or use dev identity
    if raw_email_header:
        email = _clean_google_identity(raw_email_header)
        user_id = _clean_google_identity(raw_user_id_header) if raw_user_id_header else "mock-user-id"
        return AuthenticatedClinician(
            email=email,
            user_id=user_id,
            is_authenticated=True,
            auth_source="header_passthrough",
        )

    # Default fallback for development/demo mode without IAP
    return AuthenticatedClinician(
        email="clinician@hospital.org",
        user_id="clinician-default-01",
        is_authenticated=True,
        auth_source="anonymous_demo",
    )
