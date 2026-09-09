"""Unit tests for OpenTelemetry tracing and BigQuery telemetry cost accounting."""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.core.telemetry import get_in_memory_spans, trace_span
from backend.main import app
from backend.services.telemetry_service import TelemetryService


def test_telemetry_cost_estimation():
    """Verify model cost estimation across different Gemini model tiers."""
    telemetry = TelemetryService()

    # Gemini 2.5 Flash: $0.075 / 1M in, $0.30 / 1M out
    cost_flash = telemetry.estimate_cost(
        model_name="gemini-2.5-flash",
        prompt_tokens=100_000,
        completion_tokens=20_000,
    )
    # (100000 * 0.075 / 1e6) + (20000 * 0.30 / 1e6) = 0.0075 + 0.006 = 0.0135
    assert cost_flash == pytest.approx(0.0135, rel=1e-3)

    # Gemini 2.5 Pro: $1.25 / 1M in, $5.00 / 1M out
    cost_pro = telemetry.estimate_cost(
        model_name="gemini-2.5-pro",
        prompt_tokens=100_000,
        completion_tokens=20_000,
    )
    # (100000 * 1.25 / 1e6) + (20000 * 5.00 / 1e6) = 0.125 + 0.100 = 0.225
    assert cost_pro == pytest.approx(0.225, rel=1e-3)


def test_telemetry_record_and_aggregate():
    """Verify telemetry record logging and aggregate metric computation."""
    telemetry = TelemetryService()

    telemetry.record_query_metrics(
        query_id="q-001",
        session_id="sess-001",
        category="Oncology",
        prompt_tokens=500,
        completion_tokens=200,
        latency_ms=1200.0,
        safe_refusal=False,
        citations_count=3,
        model_name="gemini-2.5-pro",
    )
    telemetry.record_query_metrics(
        query_id="q-002",
        session_id="sess-002",
        category="General Medicine",
        prompt_tokens=100,
        completion_tokens=50,
        latency_ms=300.0,
        safe_refusal=True,
        citations_count=0,
        model_name="gemini-2.5-flash",
    )

    stats = telemetry.get_aggregate_stats()
    assert stats["total_queries"] >= 2
    assert stats["avg_latency_ms"] > 0
    assert stats["total_cost_usd"] > 0
    assert stats["safe_refusal_rate"] > 0


def test_opentelemetry_span_tracing():
    """Verify child spans are created and attributes recorded."""
    with trace_span("test.clinical_operation", {"clinical.category": "Oncology", "test.id": 42}):
        pass

    spans = get_in_memory_spans()
    test_spans = [s for s in spans if s.name == "test.clinical_operation"]
    assert len(test_spans) > 0
    assert test_spans[-1].attributes.get("clinical.category") == "Oncology"


@pytest.mark.asyncio
async def test_telemetry_api_endpoints():
    """Verify /api/v1/telemetry/stats and /api/v1/telemetry/records endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/telemetry/stats")
        assert res.status_code == 200
        data = res.json()
        assert "total_queries" in data
        assert "avg_latency_ms" in data

        res_records = await client.get("/api/v1/telemetry/records")
        assert res_records.status_code == 200
        records = res_records.json()
        assert isinstance(records, list)
