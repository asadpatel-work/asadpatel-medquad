"""Unit tests for FastAPI endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Verify /healthz returns 200 OK and valid status."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data


@pytest.mark.asyncio
async def test_chat_endpoint_sync():
    """Verify synchronous chat endpoint generates response with citations and trace."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "message": "What are the clinical indicators of Hodgkin Lymphoma?",
            "stream": False,
        }
        response = await client.post("/api/v1/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "response" in data
        assert len(data["citations"]) >= 1
        assert "latency_ms" in data
        assert response.headers.get("X-Request-ID") is not None


@pytest.mark.asyncio
async def test_session_lifecycle():
    """Verify creating, fetching, and deleting sessions."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create session
        create_res = await client.post("/api/v1/sessions")
        assert create_res.status_code == 201
        session_id = create_res.json()["session_id"]

        # Fetch session
        get_res = await client.get(f"/api/v1/sessions/{session_id}")
        assert get_res.status_code == 200
        assert get_res.json()["session_id"] == session_id

        # Delete session
        del_res = await client.delete(f"/api/v1/sessions/{session_id}")
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "deleted"

        # 404 on deleted session
        get_again_res = await client.get(f"/api/v1/sessions/{session_id}")
        assert get_again_res.status_code == 404


@pytest.mark.asyncio
async def test_feedback_submission():
    """Verify feedback submission and metrics calculation."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        fb_payload = {
            "session_id": "test_session_123",
            "rating": 1,
            "comments": "Accurate NIH citations and concise summary.",
        }
        res = await client.post("/api/v1/feedback", json=fb_payload)
        assert res.status_code == 200
        assert res.json()["status"] == "recorded"

        metrics_res = await client.get("/api/v1/feedback/metrics")
        assert metrics_res.status_code == 200
        metrics = metrics_res.json()
        assert metrics["total_feedback"] >= 1
        assert metrics["positive"] >= 1
