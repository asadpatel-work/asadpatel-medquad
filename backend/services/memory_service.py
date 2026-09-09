"""Multi-Turn Conversation Memory and Session Service.

Maintains conversation history, clinical reasoning traces, and metadata across
multi-turn interactions with in-memory caching and optional PostgreSQL persistence.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from backend.models.schemas import AgentThoughtStep, Citation

logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    """A single turn in the conversation."""

    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    citations: list[Citation] = Field(default_factory=list)
    thought_steps: list[AgentThoughtStep] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionState(BaseModel):
    """Encapsulates full multi-turn session state."""

    session_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    messages: list[ChatMessage] = Field(default_factory=list)
    active_category: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from google.cloud import storage

from backend.core.config import Settings


class MemoryService:
    """Manages conversation sessions in-memory with disk and GCS persistence."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}
        self._local_dir = Path("/tmp/medquad_sessions")
        self._local_dir.mkdir(parents=True, exist_ok=True)
        self._gcs_client: storage.Client | None = None
        self._bucket_name: str | None = None
        self._executor = ThreadPoolExecutor(max_workers=3)
        self._init_storage()

    def _init_storage(self) -> None:
        """Initializes Google Cloud Storage persistence if available."""
        try:
            settings = Settings()
            raw_bucket = settings.medquad_gcs_bucket.replace("gs://", "").strip("/")
            if raw_bucket and not settings.use_mock_search:
                self._bucket_name = raw_bucket
                self._gcs_client = storage.Client(project=settings.gcp_project_id)
                logger.info("MemoryService persistent storage linked to GCS bucket: %s", self._bucket_name)
        except Exception as e:
            logger.info("MemoryService running with local disk persistence: %s", e)

    def _save_session(self, session: SessionState) -> None:
        """Persists session state to local disk and GCS."""
        try:
            file_path = self._local_dir / f"{session.session_id}.json"
            file_path.write_text(session.model_dump_json(indent=2))
        except Exception as e:
            logger.warning("Failed to write session %s to local disk: %s", session.session_id, e)

        if self._gcs_client and self._bucket_name:
            def _upload() -> None:
                try:
                    bucket = self._gcs_client.bucket(self._bucket_name)
                    blob = bucket.blob(f"sessions/{session.session_id}.json")
                    blob.upload_from_string(session.model_dump_json(), content_type="application/json")
                except Exception as upload_err:
                    logger.warning("Failed to sync session %s to GCS: %s", session.session_id, upload_err)

            self._executor.submit(_upload)

    def _load_session_from_storage(self, session_id: str) -> SessionState | None:
        """Attempts to load session from local disk or GCS."""
        # 1. Check local disk
        file_path = self._local_dir / f"{session_id}.json"
        if file_path.exists():
            try:
                data = json.loads(file_path.read_text())
                state = SessionState.model_validate(data)
                self._sessions[session_id] = state
                return state
            except Exception as e:
                logger.warning("Failed to read session %s from disk: %s", session_id, e)

        # 2. Check GCS
        if self._gcs_client and self._bucket_name:
            try:
                bucket = self._gcs_client.bucket(self._bucket_name)
                blob = bucket.blob(f"sessions/{session_id}.json")
                if blob.exists():
                    data = json.loads(blob.download_as_text())
                    state = SessionState.model_validate(data)
                    self._sessions[session_id] = state
                    file_path.write_text(state.model_dump_json(indent=2))
                    return state
            except Exception as e:
                logger.warning("Failed to download session %s from GCS: %s", session_id, e)

        return None

    def get_or_create_session(
        self, session_id: str, metadata: dict[str, Any] | None = None
    ) -> SessionState:
        """Retrieves existing session or initializes a new one."""
        existing = self.get_session(session_id)
        if existing:
            return existing

        logger.info("Creating new conversation session: %s", session_id)
        new_session = SessionState(
            session_id=session_id,
            metadata=metadata or {},
        )
        self._sessions[session_id] = new_session
        self._save_session(new_session)
        return new_session

    def get_session(self, session_id: str) -> SessionState | None:
        """Retrieves a session if it exists in memory, disk, or GCS."""
        if session_id in self._sessions:
            return self._sessions[session_id]
        return self._load_session_from_storage(session_id)

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        citations: list[Citation] | None = None,
        thought_steps: list[AgentThoughtStep] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ChatMessage:
        """Appends a new turn to the session history and persists it."""
        session = self.get_or_create_session(session_id)
        msg = ChatMessage(
            role=role,
            content=content,
            citations=citations or [],
            thought_steps=thought_steps or [],
            metadata=metadata or {},
        )
        session.messages.append(msg)
        session.updated_at = datetime.now(UTC)
        self._save_session(session)
        return msg

    def get_history_formatted(self, session_id: str, max_turns: int = 6) -> list[dict[str, str]]:
        """Formats recent history for LLM prompt context."""
        session = self.get_session(session_id)
        if not session or not session.messages:
            return []

        recent = session.messages[-max_turns:]
        return [{"role": m.role, "content": m.content} for m in recent]

    def delete_session(self, session_id: str) -> bool:
        """Deletes a session from memory, local disk, and GCS."""
        deleted = False
        if session_id in self._sessions:
            del self._sessions[session_id]
            deleted = True

        file_path = self._local_dir / f"{session_id}.json"
        if file_path.exists():
            try:
                file_path.unlink()
                deleted = True
            except Exception as e:
                logger.warning("Failed to delete session file %s: %s", file_path, e)

        if self._gcs_client and self._bucket_name:
            def _delete_blob() -> None:
                try:
                    bucket = self._gcs_client.bucket(self._bucket_name)
                    blob = bucket.blob(f"sessions/{session_id}.json")
                    if blob.exists():
                        blob.delete()
                except Exception as del_err:
                    logger.warning("Failed to delete session blob %s from GCS: %s", session_id, del_err)

            self._executor.submit(_delete_blob)

        logger.info("Deleted session: %s", session_id)
        return deleted

    def list_sessions(self) -> list[str]:
        """Lists all active session IDs from memory, local disk, and GCS."""
        session_ids = set(self._sessions.keys())

        # Collect from local disk
        for p in self._local_dir.glob("*.json"):
            session_ids.add(p.stem)

        # Collect from GCS
        if self._gcs_client and self._bucket_name:
            try:
                bucket = self._gcs_client.bucket(self._bucket_name)
                for blob in bucket.list_blobs(prefix="sessions/"):
                    if blob.name.endswith(".json"):
                        name = blob.name.replace("sessions/", "").replace(".json", "")
                        if name:
                            session_ids.add(name)
            except Exception as e:
                logger.warning("Failed to list sessions from GCS: %s", e)

        return list(session_ids)


# Global singleton instance
_memory_service_instance: MemoryService | None = None


def get_memory_service() -> MemoryService:
    """Returns singleton instance of MemoryService."""
    global _memory_service_instance
    if _memory_service_instance is None:
        _memory_service_instance = MemoryService()
    return _memory_service_instance
