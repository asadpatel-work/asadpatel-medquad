"""Clinical Chat API endpoints with multi-agent orchestration and SSE streaming."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from backend.agents.orchestrator import get_orchestrator
from backend.core.iap_auth import AuthenticatedClinician, get_current_clinician
from backend.models.schemas import (
    ChatRequest,
    ChatResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


async def stream_chat_response(request: ChatRequest, session_id: str) -> AsyncGenerator[dict, None]:
    """Yields Server-Sent Events representing real-time multi-agent execution tokens, thoughts, and safety events."""
    orchestrator = get_orchestrator()

    async for event in orchestrator.process_chat_stream(request):
        yield {
            "event": event["event"],
            "data": json.dumps(event["data"]),
        }


@router.post("", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    clinician: Annotated[AuthenticatedClinician, Depends(get_current_clinician)],
):
    """Handles clinician conversational queries via synchronous JSON or SSE streaming."""
    if not request.session_id:
        request.session_id = f"sess_{uuid.uuid4().hex[:12]}"

    logger.info("Chat query from clinician: %s (session: %s)", clinician.email, request.session_id)

    if request.stream:
        return EventSourceResponse(stream_chat_response(request, request.session_id))

    orchestrator = get_orchestrator()
    return await orchestrator.process_chat(request)
