"""Health and readiness check endpoints."""

from fastapi import APIRouter

from backend.core.config import get_settings
from backend.models.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/healthz", response_model=HealthResponse)
@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Returns application health and environment metadata."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
    )
