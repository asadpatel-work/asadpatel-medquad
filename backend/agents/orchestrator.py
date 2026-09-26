"""Root Orchestrator Supervisor Agent (Gemini 2.5 Flash).

Orchestrates multi-agent clinical workflow:
1. Model Armor Security & PHI Redaction.
2. Deterministic Scope Lock (Safe Refusal for personal medical diagnosis / prescriptions).
3. Subagent Delegation (Researcher -> Reviewer).
4. Distributed OpenTelemetry Tracing & BigQuery Telemetry logging.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from google.adk.agents import Agent as AdkAgent
from google.adk.runners import Runner as AdkRunner
from google.adk.sessions import InMemorySessionService

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

SUPERVISOR_SYSTEM_INSTRUCTION = """You are the Root Clinical Orchestrator Supervisor for the MedQuAD Clinical Assistant at the NIH Clinical Center.
You oversee the multi-agent clinical workflow, routing clinician inquiries between the ResearcherAgent and ReviewerAgent to deliver safe, grounded, and verified medical literature responses.
"""


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

        # Google ADK Supervisor-Worker topology initialization
        self.adk_agent = AdkAgent(
            name="root_orchestrator",
            model=self.model_name,
            instruction=SUPERVISOR_SYSTEM_INSTRUCTION,
            sub_agents=[self.researcher.adk_agent, self.reviewer.adk_agent],
            description="Root Clinical Orchestrator supervising Researcher and Reviewer subagents.",
        )
        self.adk_session_service = InMemorySessionService()
        self.adk_runner = AdkRunner(
            agent=self.adk_agent,
            app_name="medquad_clinical_assistant",
            session_service=self.adk_session_service,
        )

    def classify_category(self, query: str) -> MedicalCategory:
        """Classifies query into standard clinical sub-specialties."""
        category_name = infer_topic_category(query)
        for cat in MedicalCategory:
            if cat.value.lower() == category_name.lower():
                return cat
        return MedicalCategory.GENERAL_MEDICINE

    async def process_chat_stream(
        self, request: ChatRequest
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Streams real-time thoughts, tokens, safety refusal events, and final response."""
        start_time = time.perf_counter()
        query_id = f"q-{uuid.uuid4().hex[:10]}"
        session_id = request.session_id or f"session-{uuid.uuid4().hex[:8]}"
        thought_steps: list[AgentThoughtStep] = []

        queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()

        async def emit(event_type: str, data: dict[str, Any]) -> None:
            await queue.put({"event": event_type, "data": data})

        async def on_thought_step(step: AgentThoughtStep) -> None:
            thought_steps.append(step)
            await emit("thought", step.model_dump(mode="json"))

        emit_thought = on_thought_step

        async def run_pipeline() -> None:
            try:
                # Step 1: Model Armor Security & PHI Sanitization
                await emit(
                    "thought",
                    AgentThoughtStep(
                        agent_name="Model Armor Security Guardrail",
                        step_type="security_check",
                        description="Auditing prompt for adversarial injections and Protected Health Information (PHI)...",
                    ).model_dump(mode="json"),
                )

                with trace_span(
                    "guardrails.model_armor",
                    attributes={"guardrail.type": "hipaa_phi_and_jailbreak_shield"},
                ):
                    sanitization = self.armor.sanitize(request.query)

                if not sanitization.is_safe:
                    step = AgentThoughtStep(
                        agent_name="Model Armor Security Guardrail",
                        step_type="security_violation",
                        description="Adversarial prompt injection attempt intercepted and blocked.",
                    )
                    thought_steps.append(step)
                    await emit("thought", step.model_dump(mode="json"))

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

                    self.memory.add_message(
                        session_id=session_id, role="user", content=request.query
                    )
                    self.memory.add_message(
                        session_id=session_id,
                        role="assistant",
                        content=refusal_msg,
                        thought_steps=thought_steps,
                        metadata={
                            "safe_refusal": True,
                            "is_refusal": True,
                            "refusal_type": "security_violation",
                            "category": "Security Violation",
                            "latency_ms": round(total_ms, 2),
                        },
                    )

                    await emit(
                        "safety_refusal",
                        {
                            "refusal_type": "security_violation",
                            "category": "Security Violation",
                            "reason": "Adversarial prompt injection or prohibited control instruction detected.",
                            "message": refusal_msg,
                        },
                    )

                    final_resp = ChatResponse(
                        session_id=session_id,
                        response=refusal_msg,
                        citations=[],
                        category=MedicalCategory.UNKNOWN,
                        safe_refusal=True,
                        is_refusal=True,
                        refusal_type="security_violation",
                        is_grounded=False,
                        thought_steps=thought_steps,
                        latency_ms=round(total_ms, 2),
                    )
                    await emit("final", final_resp.model_dump(mode="json"))
                    return

                clean_query = sanitization.sanitized_text
                if sanitization.redacted_phi_count > 0:
                    phi_step = AgentThoughtStep(
                        agent_name="Model Armor PHI Guardrail",
                        step_type="phi_redaction",
                        description=f"Masked {sanitization.redacted_phi_count} protected health information (PHI) token(s).",
                    )
                    thought_steps.append(phi_step)
                    await emit("thought", phi_step.model_dump(mode="json"))

                # Step 2: Intent Classification & Safe Refusal Check
                category = self.classify_category(clean_query)
                with trace_span(
                    "guardrails.safe_refusal",
                    attributes={"guardrail.type": "deterministic_clinical_boundary"},
                ):
                    refusal_eval = self.safe_refusal.evaluate(clean_query)

                route_step = AgentThoughtStep(
                    agent_name="Root Orchestrator (Gemini 2.5 Flash)",
                    step_type="routing",
                    description=f"Classified clinical domain: {category.value}.",
                )
                thought_steps.append(route_step)
                await emit("thought", route_step.model_dump(mode="json"))

                if refusal_eval.is_refusal:
                    refusal_type_str = refusal_eval.refusal_category.value
                    scope_step = AgentThoughtStep(
                        agent_name="Root Orchestrator (Gemini 2.5 Flash)",
                        step_type="scope_lock_refusal",
                        description=f"Scope Lock triggered ({refusal_type_str}). Enforcing safe clinical disclaimer.",
                    )
                    thought_steps.append(scope_step)
                    await emit("thought", scope_step.model_dump(mode="json"))

                    total_ms = (time.perf_counter() - start_time) * 1000
                    refusal_text = (
                        refusal_eval.refusal_message
                        or "Personal medical diagnosis or prescription request cannot be fulfilled."
                    )

                    self.memory.add_message(
                        session_id=session_id, role="user", content=request.query
                    )
                    self.memory.add_message(
                        session_id=session_id,
                        role="assistant",
                        content=refusal_text,
                        thought_steps=thought_steps,
                        metadata={
                            "safe_refusal": True,
                            "is_refusal": True,
                            "refusal_type": refusal_type_str,
                            "category": category.value
                            if hasattr(category, "value")
                            else str(category),
                            "latency_ms": round(total_ms, 2),
                        },
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

                    await emit(
                        "safety_refusal",
                        {
                            "refusal_type": refusal_type_str,
                            "category": category.value,
                            "reason": refusal_type_str.replace("_", " ").title(),
                            "message": refusal_text,
                        },
                    )

                    final_resp = ChatResponse(
                        session_id=session_id,
                        response=refusal_text,
                        citations=[],
                        category=category,
                        safe_refusal=True,
                        is_refusal=True,
                        refusal_type=refusal_type_str,
                        is_grounded=False,
                        thought_steps=thought_steps,
                        latency_ms=round(total_ms, 2),
                    )
                    await emit("final", final_resp.model_dump(mode="json"))
                    return

                # Step 3: Retrieve Conversation History Context
                # Hydrate from client-supplied history if memory service lacks prior turns (e.g. replica failover)
                client_history = [
                    {
                        "role": str(m.get("role", "user")),
                        "content": str(m.get("content", "")).strip(),
                    }
                    for m in (request.history or [])
                    if m.get("content")
                ]
                memory_history = self.memory.get_history_formatted(session_id)
                if len(client_history) > len(memory_history):
                    session = self.memory.get_or_create_session(session_id)
                    existing_contents = {msg.content.strip() for msg in session.messages}
                    for h_msg in client_history:
                        if h_msg["content"] and h_msg["content"] not in existing_contents:
                            self.memory.add_message(
                                session_id=session_id,
                                role=h_msg["role"],
                                content=h_msg["content"],
                            )
                            existing_contents.add(h_msg["content"])
                    history = self.memory.get_history_formatted(session_id)
                else:
                    history = memory_history if memory_history else client_history

                self.memory.add_message(session_id=session_id, role="user", content=request.query)

                # Step 4: Delegate to Researcher Subagent (Gemini 2.5 Pro)
                deleg_res_step = AgentThoughtStep(
                    agent_name="Root Orchestrator (Gemini 2.5 Flash)",
                    step_type="delegation",
                    description=f"Delegating retrieval and synthesis to Researcher Subagent ({self.settings.gemini_researcher_model}).",
                )
                thought_steps.append(deleg_res_step)
                await emit("thought", deleg_res_step.model_dump(mode="json"))

                with trace_span(
                    "agent.researcher",
                    attributes={
                        "gen_ai.system": "gemini",
                        "gen_ai.request.model": self.settings.gemini_researcher_model,
                        "gen_ai.operation.name": "clinical_synthesis",
                        "clinical.category": category,
                    },
                ):
                    research_draft = await self.researcher.conduct_research(
                        query=clean_query,
                        category=category,
                        conversation_history=history,
                        on_thought=emit_thought,
                    )
                thought_steps.extend(research_draft.thought_steps)

                # Step 5: Delegate to Reviewer Subagent (Gemini 3.5 Flash)
                deleg_rev_step = AgentThoughtStep(
                    agent_name="Root Orchestrator (Gemini 2.5 Flash)",
                    step_type="delegation",
                    description=f"Delegating quality control and citation verification to Reviewer Subagent ({self.settings.gemini_reviewer_model}).",
                )
                thought_steps.append(deleg_rev_step)
                await emit("thought", deleg_rev_step.model_dump(mode="json"))

                with trace_span(
                    "agent.reviewer",
                    attributes={
                        "gen_ai.system": "gemini",
                        "gen_ai.request.model": self.settings.gemini_reviewer_model,
                        "gen_ai.operation.name": "citation_verification",
                    },
                ):
                    review_result = await self.reviewer.review_draft(
                        query=clean_query,
                        draft_answer=research_draft.draft_answer,
                        retrieved_chunks=research_draft.retrieved_chunks,
                        on_thought=emit_thought,
                    )
                thought_steps.extend(review_result.thought_steps)

                # Check if Reviewer flagged prescriptive advice
                if not review_result.approved and review_result.critique_notes:
                    audit_flag_step = AgentThoughtStep(
                        agent_name="Root Orchestrator (Gemini 2.5 Flash)",
                        step_type="audit_critique",
                        description=f"Reviewer Audit Notice: {review_result.critique_notes}",
                    )
                    thought_steps.append(audit_flag_step)
                    await emit("thought", audit_flag_step.model_dump(mode="json"))

                total_ms = (time.perf_counter() - start_time) * 1000

                # Step 6: Persist Assistant Response in Memory
                self.memory.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=review_result.final_answer,
                    citations=review_result.citations,
                    thought_steps=thought_steps,
                    metadata={
                        "confidence_score": review_result.confidence_score,
                        "latency_ms": round(total_ms, 2),
                        "safe_refusal": False,
                        "is_refusal": False,
                        "category": category.value if hasattr(category, "value") else str(category),
                    },
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

                # Step 8: Stream response tokens to frontend
                words = review_result.final_answer.split(" ")
                for i, word in enumerate(words):
                    tok = word if i == len(words) - 1 else word + " "
                    await emit("token", {"token": tok})
                    await asyncio.sleep(0.005)

                final_resp = ChatResponse(
                    session_id=session_id,
                    response=review_result.final_answer,
                    citations=review_result.citations,
                    category=category,
                    safe_refusal=False,
                    is_refusal=False,
                    refusal_type=None,
                    is_grounded=True,
                    thought_steps=thought_steps,
                    latency_ms=round(total_ms, 2),
                )
                await emit("final", final_resp.model_dump(mode="json"))

            except Exception as exc:
                logger.exception("Error in multi-agent orchestration stream: %s", exc)
                err_step = AgentThoughtStep(
                    agent_name="Root Orchestrator (Gemini 2.5 Flash)",
                    step_type="error",
                    description=f"Encountered unexpected internal error: {str(exc)[:120]}",
                )
                thought_steps.append(err_step)
                await emit("thought", err_step.model_dump(mode="json"))
                err_resp = ChatResponse(
                    session_id=session_id,
                    response="An error occurred while processing your request. Please try again.",
                    citations=[],
                    category=MedicalCategory.UNKNOWN,
                    safe_refusal=False,
                    is_grounded=False,
                    thought_steps=thought_steps,
                    latency_ms=round((time.perf_counter() - start_time) * 1000, 2),
                )
                await emit("final", err_resp.model_dump(mode="json"))
            finally:
                await queue.put(None)

        task = asyncio.create_task(run_pipeline())
        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                yield item
        finally:
            if not task.done():
                task.cancel()

    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Executes full multi-agent Supervisor-Worker workflow synchronously."""
        final_response: ChatResponse | None = None
        async for event in self.process_chat_stream(request):
            if event.get("event") == "final":
                final_response = ChatResponse.model_validate(event["data"])

        if final_response is None:
            raise RuntimeError("No final response generated by orchestrator stream")
        return final_response


# Global singleton orchestrator
_orchestrator_instance: RootOrchestrator | None = None


def get_orchestrator() -> RootOrchestrator:
    """Returns singleton RootOrchestrator."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = RootOrchestrator()
    return _orchestrator_instance


def get_root_agent() -> AdkAgent:
    """Returns the configured root Google ADK agent for CLI runners and external harnesses."""
    return get_orchestrator().adk_agent


root_agent = get_root_agent()
