"""Root Orchestrator Supervisor Agent (Gemini 2.5 Flash).

Orchestrates multi-agent clinical workflow:
1. Model Armor Security & PHI Redaction.
2. Deterministic Scope Lock (Safe Refusal for personal medical diagnosis / prescriptions).
3. Subagent Delegation (Researcher -> Reviewer).
4. Distributed OpenTelemetry Tracing & BigQuery Telemetry logging.
"""

from __future__ import annotations

import logging
import time
import uuid

from backend.agents.researcher_agent import ResearcherAgent
from backend.agents.reviewer_agent import ReviewerAgent
from backend.core.config import get_settings
from backend.core.telemetry import trace_span
from backend.guardrails.model_armor import ModelArmor, get_model_armor
from backend.guardrails.safe_refusal import SafeRefusalEngine, get_safe_refusal_engine
from backend.models.schemas import (
    AgentThoughtStep,
    ChatRequest,
    ChatResponse,
    MedicalCategory,
)
from backend.services.memory_service import MemoryService, get_memory_service
from backend.services.telemetry_service import TelemetryService, get_telemetry_service
from scripts.ingest_medquad import infer_topic_category

logger = logging.getLogger(__name__)


class RootOrchestrator:
    """Supervisor Agent coordinating clinical research and quality control subagents."""

    def __init__(
        self,
        researcher: ResearcherAgent | None = None,
        reviewer: ReviewerAgent | None = None,
        memory_service: MemoryService | None = None,
        model_armor: ModelArmor | None = None,
        safe_refusal_engine: SafeRefusalEngine | None = None,
        telemetry_service: TelemetryService | None = None,
    ) -> None:
        self.settings = get_settings()
        self.model_name = self.settings.root_orchestrator_model
        self.researcher = researcher or ResearcherAgent()
        self.reviewer = reviewer or ReviewerAgent()
        self.memory = memory_service or get_memory_service()
        self.armor = model_armor or get_model_armor()
        self.safe_refusal = safe_refusal_engine or get_safe_refusal_engine()
        self.telemetry = telemetry_service or get_telemetry_service()

    def classify_category(self, query: str) -> MedicalCategory:
        """Classifies query into standard clinical sub-specialties."""
        category_name = infer_topic_category(query)
        for cat in MedicalCategory:
            if cat.value.lower() == category_name.lower():
                return cat
        return MedicalCategory.GENERAL_MEDICINE

    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Executes full multi-agent Supervisor-Worker workflow with safety and telemetry."""
        start_time = time.perf_counter()
        query_id = f"q-{uuid.uuid4().hex[:10]}"
        session_id = request.session_id or f"session-{uuid.uuid4().hex[:8]}"
        thought_steps: list[AgentThoughtStep] = []

        with trace_span(
            "orchestrator.process_chat", {"session.id": session_id, "query.id": query_id}
        ):
            # Step 1: Model Armor Security & PHI Sanitization
            with trace_span("guardrails.model_armor"):
                sanitization = self.armor.sanitize(request.query)

            if not sanitization.is_safe:
                # Jailbreak intercepted
                thought_steps.append(
                    AgentThoughtStep(
                        agent_name="Model Armor Security Guardrail",
                        step_type="security_violation",
                        description="Adversarial prompt injection attempt intercepted and blocked.",
                    )
                )
                refusal_msg = (
                    "**Security Violation:** The submitted query violates the system safety policy "
                    "(adversarial prompt injection or prohibited control instruction detected)."
                )
                total_ms = (time.perf_counter() - start_time) * 1000

                self.telemetry.record_query_metrics(
                    query_id=query_id,
                    session_id=session_id,
                    category="Security Violation",
                    prompt_tokens=len(request.query.split()) * 2,
                    completion_tokens=len(refusal_msg.split()) * 2,
                    latency_ms=total_ms,
                    safe_refusal=True,
                    model_name=self.model_name,
                )

                return ChatResponse(
                    session_id=session_id,
                    response=refusal_msg,
                    citations=[],
                    category=MedicalCategory.UNKNOWN,
                    safe_refusal=True,
                    is_grounded=False,
                    thought_steps=thought_steps,
                    latency_ms=round(total_ms, 2),
                )

            clean_query = sanitization.sanitized_text
            if sanitization.redacted_phi_count > 0:
                thought_steps.append(
                    AgentThoughtStep(
                        agent_name="Model Armor PHI Guardrail",
                        step_type="phi_redaction",
                        description=f"Masked {sanitization.redacted_phi_count} protected health information (PHI) token(s).",
                    )
                )

            # Step 2: Intent Classification & Safe Refusal Check
            category = self.classify_category(clean_query)
            with trace_span("guardrails.safe_refusal"):
                refusal_eval = self.safe_refusal.evaluate(clean_query)

            thought_steps.append(
                AgentThoughtStep(
                    agent_name="Root Orchestrator (Gemini 2.5 Flash)",
                    step_type="routing",
                    description=f"Classified clinical domain: {category.value}.",
                )
            )

            if refusal_eval.is_refusal:
                thought_steps.append(
                    AgentThoughtStep(
                        agent_name="Root Orchestrator (Gemini 2.5 Flash)",
                        step_type="scope_lock_refusal",
                        description=f"Scope Lock triggered ({refusal_eval.refusal_category.value}). Enforcing safe clinical disclaimer.",
                    )
                )

                total_ms = (time.perf_counter() - start_time) * 1000
                refusal_text = (
                    refusal_eval.refusal_message
                    or "Personal medical diagnosis or prescription request cannot be fulfilled."
                )

                self.memory.add_message(session_id=session_id, role="user", content=request.query)
                self.memory.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=refusal_text,
                    thought_steps=thought_steps,
                    metadata={"safe_refusal": True},
                )

                self.telemetry.record_query_metrics(
                    query_id=query_id,
                    session_id=session_id,
                    category=category.value,
                    prompt_tokens=len(clean_query.split()) * 2,
                    completion_tokens=len(refusal_text.split()) * 2,
                    latency_ms=total_ms,
                    safe_refusal=True,
                    model_name=self.model_name,
                )

                return ChatResponse(
                    session_id=session_id,
                    response=refusal_text,
                    citations=[],
                    category=category,
                    safe_refusal=True,
                    is_grounded=False,
                    thought_steps=thought_steps,
                    latency_ms=round(total_ms, 2),
                )

            # Step 3: Retrieve Conversation History Context
            history = self.memory.get_history_formatted(session_id)

            # Step 4: Delegate to Researcher Subagent (Gemini 2.5 Pro)
            thought_steps.append(
                AgentThoughtStep(
                    agent_name="Root Orchestrator (Gemini 2.5 Flash)",
                    step_type="delegation",
                    description="Delegated literature retrieval and synthesis to Researcher Subagent.",
                )
            )

            with trace_span("agent.researcher"):
                research_draft = await self.researcher.conduct_research(
                    query=clean_query,
                    category=category,
                    conversation_history=history,
                )
            thought_steps.extend(research_draft.thought_steps)

            # Step 5: Delegate to Reviewer Subagent (Gemini 3.5 Flash)
            thought_steps.append(
                AgentThoughtStep(
                    agent_name="Root Orchestrator (Gemini 2.5 Flash)",
                    step_type="delegation",
                    description="Delegated draft verification and citation audit to Reviewer Subagent.",
                )
            )

            with trace_span("agent.reviewer"):
                review_result = await self.reviewer.review_draft(
                    query=clean_query,
                    draft_answer=research_draft.draft_answer,
                    retrieved_chunks=research_draft.retrieved_chunks,
                )
            thought_steps.extend(review_result.thought_steps)

            total_ms = (time.perf_counter() - start_time) * 1000

            # Step 6: Persist in Memory
            self.memory.add_message(session_id=session_id, role="user", content=request.query)
            self.memory.add_message(
                session_id=session_id,
                role="assistant",
                content=review_result.final_answer,
                citations=review_result.citations,
                thought_steps=thought_steps,
                metadata={"confidence_score": review_result.confidence_score},
            )

            # Step 7: Record Telemetry Metrics & Estimated Cost
            prompt_toks = len(clean_query.split()) * 3 + sum(
                len(c.content.split()) for c in research_draft.retrieved_chunks
            )
            comp_toks = len(review_result.final_answer.split()) * 2
            self.telemetry.record_query_metrics(
                query_id=query_id,
                session_id=session_id,
                category=category.value,
                prompt_tokens=prompt_toks,
                completion_tokens=comp_toks,
                latency_ms=total_ms,
                safe_refusal=False,
                citations_count=len(review_result.citations),
                model_name=self.settings.researcher_model,
            )

            return ChatResponse(
                session_id=session_id,
                response=review_result.final_answer,
                citations=review_result.citations,
                category=category,
                safe_refusal=False,
                is_grounded=True,
                thought_steps=thought_steps,
                latency_ms=round(total_ms, 2),
            )


# Global singleton orchestrator
_orchestrator_instance: RootOrchestrator | None = None


def get_orchestrator() -> RootOrchestrator:
    """Returns singleton RootOrchestrator."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = RootOrchestrator()
    return _orchestrator_instance
