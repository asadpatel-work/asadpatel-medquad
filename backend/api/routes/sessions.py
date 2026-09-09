"""Session management API endpoints."""

import uuid

from fastapi import APIRouter, HTTPException

from backend.services.memory_service import get_memory_service

router = APIRouter(prefix="/api/v1/sessions", tags=["Sessions"])


@router.post("", status_code=201)
async def create_session() -> dict:
    """Creates a new conversational clinical session."""
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    memory = get_memory_service()
    session = memory.get_or_create_session(session_id)
    return {
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat(),
        "messages": [m.model_dump(mode="json") for m in session.messages],
        "metadata": session.metadata,
    }


@router.get("")
async def list_sessions() -> list[dict]:
    """Lists all consultation sessions with metadata and previews."""
    memory = get_memory_service()
    results = []
    for sid in memory.list_sessions():
        s = memory.get_session(sid)
        if not s:
            continue
        first_user_msg = next((m.content for m in s.messages if m.role == "user"), None)
        title = (
            first_user_msg[:50] + ("..." if len(first_user_msg) > 50 else "")
            if first_user_msg
            else "New Consultation"
        )
        last_msg = s.messages[-1].content[:80] + "..." if s.messages else "No messages"
        results.append(
            {
                "session_id": sid,
                "title": title,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
                "message_count": len(s.messages),
                "preview": last_msg,
                "category": s.active_category or "Clinical",
            }
        )
    results.sort(key=lambda x: x["updated_at"], reverse=True)
    return results


@router.get("/{session_id}")
async def get_session(session_id: str) -> dict:
    """Retrieves session history and context."""
    memory = get_memory_service()
    session = memory.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return {
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "messages": [m.model_dump(mode="json") for m in session.messages],
        "metadata": session.metadata,
    }


@router.delete("/{session_id}")
async def delete_session(session_id: str) -> dict:
    """Deletes active session and clears working memory."""
    memory = get_memory_service()
    success = memory.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return {"status": "deleted", "session_id": session_id}
