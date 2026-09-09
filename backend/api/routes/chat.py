"""Clinical Chat API endpoints with multi-agent orchestration and SSE streaming."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from backend.agents.orchestrator import get_orchestrator
from backend.models.schemas import (
    ChatRequest,
    ChatResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


async def stream_chat_response(request: ChatRequest, session_id: str) -> AsyncGenerator[dict, None]:
    """Yields Server-Sent Events representing real-time multi-agent execution tokens and thoughts."""
    orchestrator = get_orchestrator()

    # Step 1: Initial Routing Notification
    yield {
        "event": "thought",
        "data": json.dumps(
            {
                "agent_name": "Root Orchestrator (Gemini 2.5 Flash)",
                "step_type": "routing",
                "description": f"Analyzing clinical research query: '{request.query[:80]}...'",
            }
        ),
    }

    # Execute multi-agent process
    response: ChatResponse = await orchestrator.process_chat(request)

    # Stream intermediate thought steps
    for step in response.thought_steps:
        yield {
            "event": "thought",
            "data": json.dumps(step.model_dump(mode="json")),
        }

    # Stream text tokens
    tokens = response.response.split(" ")
    for token in tokens:
        yield {
            "event": "token",
            "data": json.dumps({"token": token + " "}),
        }

    # Stream final completion payload
    yield {
        "event": "final",
        "data": json.dumps(
            {
                "session_id": response.session_id,
                "response": response.response,
                "category": response.category.value,
                "safe_refusal": response.safe_refusal,
                "is_refusal": response.is_refusal,
                "is_grounded": response.is_grounded,
                "citations": [c.model_dump(mode="json") for c in response.citations],
                "latency_ms": response.latency_ms,
            }
        ),
    }


@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Handles clinician conversational queries via synchronous JSON or SSE streaming."""
    if not request.session_id:
        request.session_id = f"sess_{uuid.uuid4().hex[:12]}"

    if request.stream:
        return EventSourceResponse(stream_chat_response(request, request.session_id))

    orchestrator = get_orchestrator()
    return await orchestrator.process_chat(request)
