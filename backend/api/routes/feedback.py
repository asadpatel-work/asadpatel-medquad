"""Feedback collection API endpoints."""

import logging

from fastapi import APIRouter

from backend.models.schemas import FeedbackRequest, FeedbackResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/feedback", tags=["Feedback"])

# In-memory storage for feedback before database persistence
_feedback_store: list[dict] = []


@router.post("", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """Records clinician feedback on assistant responses."""
    logger.info("Feedback received for session %s: rating=%s", request.session_id, request.rating)
    _feedback_store.append(request.model_dump())
    return FeedbackResponse(session_id=request.session_id)


@router.get("/metrics")
async def get_feedback_metrics() -> dict:
    """Returns aggregated satisfaction metrics."""
    total = len(_feedback_store)
    if total == 0:
        return {"total_feedback": 0, "positive_rate": 0.0, "negative_rate": 0.0}
    positive = sum(1 for f in _feedback_store if f["rating"] > 0)
    negative = sum(1 for f in _feedback_store if f["rating"] < 0)
    return {
        "total_feedback": total,
        "positive": positive,
        "negative": negative,
        "positive_rate": round(positive / total, 3),
        "negative_rate": round(negative / total, 3),
    }
