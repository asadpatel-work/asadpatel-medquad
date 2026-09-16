"""Unit tests for Google Cloud IAP authentication and JWT validation module."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, Request

from backend.core.config import Settings
from backend.core.iap_auth import (
    AuthenticatedClinician,
    IAPVerifier,
    _clean_google_identity,
    get_current_clinician,
)


def test_authenticated_clinician_display_name():
    clinician = AuthenticatedClinician(
        email="john.watson@hospital.org",
        user_id="user-123",
    )
    assert clinician.display_name == "John Watson"

    simple = AuthenticatedClinician(email="admin", user_id="1")
    assert simple.display_name == "admin"


def test_clean_google_identity():
    assert _clean_google_identity("accounts.google.com:doctor@hospital.org") == "doctor@hospital.org"
    assert _clean_google_identity("doctor@hospital.org") == "doctor@hospital.org"
    assert _clean_google_identity("accounts.google.com:11823719") == "11823719"


@pytest.mark.asyncio
async def test_get_current_clinician_disabled():
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {}

    clinician = await get_current_clinician(mock_request)
    assert clinician.is_authenticated is True
    assert clinician.auth_source == "anonymous_demo"
    assert "hospital.org" in clinician.email


@pytest.mark.asyncio
async def test_get_current_clinician_header_passthrough():
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {
        "x-goog-authenticated-user-email": "accounts.google.com:specialist@clinic.org",
        "x-goog-authenticated-user-id": "accounts.google.com:98765",
    }

    clinician = await get_current_clinician(mock_request)
    assert clinician.email == "specialist@clinic.org"
    assert clinician.user_id == "98765"
    assert clinician.auth_source == "header_passthrough"


@pytest.mark.asyncio
async def test_get_current_clinician_dev_bypass():
    test_settings = Settings(
        enable_iap=True,
        environment="development",
        iap_allow_anonymous_in_dev=True,
    )
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {}

    with patch("backend.core.iap_auth.get_settings", return_value=test_settings):
        clinician = await get_current_clinician(mock_request)
        assert clinician.auth_source == "dev_bypass"
        assert clinician.email == "dev-clinician@medquad.local"


@pytest.mark.asyncio
async def test_get_current_clinician_rejects_missing_jwt_in_production():
    test_settings = Settings(
        enable_iap=True,
        environment="production",
        iap_allow_anonymous_in_dev=False,
    )
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {}

    with patch("backend.core.iap_auth.get_settings", return_value=test_settings):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_clinician(mock_request)
        assert exc_info.value.status_code == 401
        assert "Missing Google IAP identity assertion" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_clinician_validates_jwt():
    test_settings = Settings(
        enable_iap=True,
        environment="production",
        iap_allow_anonymous_in_dev=False,
        iap_audience="/projects/12345/global/backendServices/medquad-backend-service",
    )
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {
        "x-goog-iap-jwt-assertion": "mock.jwt.token",
        "x-goog-authenticated-user-email": "accounts.google.com:verified@hospital.org",
        "x-goog-authenticated-user-id": "accounts.google.com:user-555",
    }

    mock_claims = {
        "iss": "https://cloud.google.com/iap",
        "sub": "accounts.google.com:user-555",
        "email": "verified@hospital.org",
        "aud": "/projects/12345/global/backendServices/medquad-backend-service",
    }

    mock_verifier = MagicMock()
    mock_verifier.verify_token.return_value = mock_claims

    with (
        patch("backend.core.iap_auth.get_settings", return_value=test_settings),
        patch("backend.core.iap_auth.get_iap_verifier", return_value=mock_verifier),
    ):
        clinician = await get_current_clinician(mock_request)
        assert clinician.email == "verified@hospital.org"
        assert clinician.user_id == "user-555"
        assert clinician.auth_source == "google_iap"
        assert clinician.claims == mock_claims


@pytest.mark.asyncio
async def test_get_current_clinician_rejects_invalid_jwt():
    test_settings = Settings(
        enable_iap=True,
        environment="production",
        iap_allow_anonymous_in_dev=False,
    )
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {
        "x-goog-iap-jwt-assertion": "corrupted.jwt.token",
    }

    mock_verifier = MagicMock()
    mock_verifier.verify_token.side_effect = ValueError("JWT signature verification failed")

    with (
        patch("backend.core.iap_auth.get_settings", return_value=test_settings),
        patch("backend.core.iap_auth.get_iap_verifier", return_value=mock_verifier),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_clinician(mock_request)
        assert exc_info.value.status_code == 401
        assert "Invalid Google IAP identity assertion" in exc_info.value.detail


def test_iap_verifier_key_caching():
    verifier = IAPVerifier(keys_url="https://mock.url", cache_ttl=100)
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"key1": "cert1", "key2": "cert2"}
        mock_get.return_value = mock_resp

        # First call fetches
        keys1 = verifier.get_public_keys()
        assert keys1 == {"key1": "cert1", "key2": "cert2"}
        assert mock_get.call_count == 1

        # Second call within TTL uses cache
        keys2 = verifier.get_public_keys()
        assert keys2 == {"key1": "cert1", "key2": "cert2"}
        assert mock_get.call_count == 1
