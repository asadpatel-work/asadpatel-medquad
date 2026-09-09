"""Telemetry and Observability API endpoints."""

from fastapi import APIRouter

from backend.services.telemetry_service import get_telemetry_service

router = APIRouter(prefix="/api/v1/telemetry", tags=["Telemetry"])


@router.get("/stats")
async def get_telemetry_stats() -> dict:
    """Returns aggregated query counts, latency averages, total estimated cost, and refusal rates."""
    service = get_telemetry_service()
    return service.get_aggregate_stats()


@router.get("/records")
async def get_telemetry_records(limit: int = 50) -> list[dict]:
    """Returns recent query execution records for real-time dashboard observability."""
    service = get_telemetry_service()
    records = service.get_records()[-limit:]
    return [r.model_dump(mode="json") for r in records]
