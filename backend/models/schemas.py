"""Pydantic data schemas and API contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class MedicalCategory(StrEnum):
    """Supported clinical domain categories."""

    GENERAL_MEDICINE = "General Medicine"
    ONCOLOGY = "Oncology"
    CARDIOLOGY = "Cardiology"
    INFECTIOUS_DISEASE = "Infectious Disease"
    NEUROLOGY = "Neurology"
    ENDOCRINOLOGY = "Endocrinology"
    PULMONOLOGY = "Pulmonology"
    PEDIATRICS = "Pediatrics"
    UNKNOWN = "Unknown"


class RoleEnum(StrEnum):
    """Chat message participant role."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Citation(BaseModel):
    """Reference citation linking grounded text to MedQuAD source chunk."""

    citation_id: int = Field(description="Sequential citation index, e.g. 1 for [1]")
    doc_id: str = Field(description="NIH MedQuAD document identifier")
    title: str = Field(description="Document title or clinical question")
    source_url: str = Field(description="Authoritative NIH URL link")
    authoritative_org: str = Field(
        default="NIH", description="Publishing institute (e.g. NCI, NHLBI, CDC)"
    )
    snippet: str = Field(description="Grounding text snippet referenced")
    relevance_score: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence/similarity score"
    )


class GroundedSearchResult(BaseModel):
    """Raw search retrieval chunk from MedQuAD grounding index."""

    chunk_id: str
    doc_id: str
    title: str
    content: str
    source_url: str
    topic_category: MedicalCategory = MedicalCategory.GENERAL_MEDICINE
    authoritative_org: str = "NIH"
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    """Incoming user chat query."""

    session_id: str | None = Field(
        default=None, description="Optional persistent session identifier"
    )
    message: str | None = Field(
        default=None, description="Natural language clinical research query"
    )
    query: str | None = Field(default=None, description="Alias for message")
    stream: bool = Field(default=False, description="Whether to stream response tokens via SSE")

    @model_validator(mode="after")
    def populate_query_message(self) -> ChatRequest:
        if not self.message and not self.query:
            raise ValueError("Either 'message' or 'query' must be provided.")
        if not self.message and self.query:
            self.message = self.query
        if not self.query and self.message:
            self.query = self.message
        return self


class AgentThoughtStep(BaseModel):
    """Intermediate reasoning step emitted by the multi-agent system."""

    agent_name: str
    step_type: str = "reasoning"
    description: str = ""
    action: str | None = None
    thought: str | None = None
    observation: str | None = None
    tool_called: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_output_summary: str | None = None
    latency_ms: float | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def sync_action_thought(self) -> AgentThoughtStep:
        if not self.action:
            self.action = self.step_type
        if not self.thought and self.description:
            self.thought = self.description
        return self


class ChatResponse(BaseModel):
    """Standardized response from the MedQuAD Clinical Assistant."""

    session_id: str
    response: str
    safe_refusal: bool = Field(
        default=False, description="True if query triggered Safe Refusal guardrails"
    )
    is_refusal: bool = Field(default=False, description="Alias for safe_refusal")
    is_grounded: bool = Field(
        default=True, description="True if answer is backed by retrieved citations"
    )
    category: MedicalCategory = Field(default=MedicalCategory.GENERAL_MEDICINE)
    citations: list[Citation] = Field(default_factory=list)
    thought_steps: list[AgentThoughtStep] = Field(default_factory=list)
    reasoning_trace: list[AgentThoughtStep] = Field(default_factory=list)
    latency_ms: float = Field(
        default=0.0, description="End-to-end execution latency in milliseconds"
    )

    @model_validator(mode="after")
    def sync_refusal_and_traces(self) -> ChatResponse:
        if self.safe_refusal and not self.is_refusal:
            self.is_refusal = True
        elif self.is_refusal and not self.safe_refusal:
            self.safe_refusal = True
        if self.thought_steps and not self.reasoning_trace:
            self.reasoning_trace = self.thought_steps
        elif self.reasoning_trace and not self.thought_steps:
            self.thought_steps = self.reasoning_trace
        return self


class FeedbackRequest(BaseModel):
    """Clinician feedback submission."""

    session_id: str
    message_id: str | None = None
    rating: int = Field(..., ge=-1, le=1, description="+1 for helpful, -1 for unhelpful")
    comments: str | None = Field(default=None, max_length=1000)


class FeedbackResponse(BaseModel):
    """Feedback acknowledgment response."""

    status: str = "recorded"
    session_id: str
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class HealthResponse(BaseModel):
    """Service health status."""

    status: str = "healthy"
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
