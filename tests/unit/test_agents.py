import uuid

import pytest

from backend.agents.orchestrator import RootOrchestrator
from backend.agents.researcher_agent import ResearcherAgent
from backend.agents.reviewer_agent import ReviewerAgent
from backend.models.schemas import (
    ChatRequest,
    GroundedSearchResult,
    MedicalCategory,
)
from backend.services.memory_service import MemoryService
from backend.tools.citation_verifier import CitationVerifier
from backend.tools.clinical_db_tool import ClinicalDBTool
from backend.tools.search_tool import SearchTool


@pytest.mark.asyncio
async def test_researcher_agent_execution():
    """Verify Researcher Subagent executes search and synthesizes cited response."""
    search_tool = SearchTool(use_mock=True)
    clinical_db = ClinicalDBTool()
    researcher = ResearcherAgent(search_tool=search_tool, clinical_db=clinical_db)

    draft = await researcher.conduct_research(
        query="What is the Stupp protocol and molecular markers for Glioblastoma?",
        category=MedicalCategory.ONCOLOGY,
    )

    assert draft.draft_answer != ""
    assert len(draft.retrieved_chunks) > 0
    assert len(draft.thought_steps) >= 3
    assert any("[1]" in draft.draft_answer for _ in [1])


@pytest.mark.asyncio
async def test_reviewer_agent_approval():
    """Verify Reviewer Subagent audits draft and validates citations."""
    sample_chunks = [
        GroundedSearchResult(
            chunk_id="chunk-01",
            doc_id="NIH-001",
            title="Hodgkin Lymphoma PDQ",
            content="Reed-Sternberg cells are hallmark diagnostic markers for Hodgkin Lymphoma.",
            source_url="https://cancer.gov",
            topic_category=MedicalCategory.ONCOLOGY,
            score=0.95,
        )
    ]
    draft_answer = (
        "Reed-Sternberg cells are pathognomonic diagnostic markers for Hodgkin Lymphoma [1]."
    )

    reviewer = ReviewerAgent(citation_verifier=CitationVerifier())
    result = await reviewer.review_draft(
        query="Tell me about Hodgkin lymphoma",
        draft_answer=draft_answer,
        retrieved_chunks=sample_chunks,
    )

    assert result.approved is True
    assert len(result.citations) == 1
    assert result.citations[0].doc_id == "NIH-001"
    assert result.confidence_score >= 0.90


@pytest.mark.asyncio
async def test_root_orchestrator_clinical_flow():
    """Verify end-to-end multi-agent research workflow on clinical query."""
    memory = MemoryService()
    orchestrator = RootOrchestrator(
        researcher=ResearcherAgent(search_tool=SearchTool(use_mock=True)),
        reviewer=ReviewerAgent(),
        memory_service=memory,
    )

    test_sess_id = f"sess-test-flow-{uuid.uuid4().hex[:8]}"
    request = ChatRequest(
        message="What are the diagnostic criteria and HbA1c threshold for Type 2 Diabetes?",
        session_id=test_sess_id,
    )

    response = await orchestrator.process_chat(request)

    assert response.session_id == test_sess_id
    assert response.safe_refusal is False
    assert response.is_grounded is True
    assert response.category == MedicalCategory.ENDOCRINOLOGY
    assert len(response.citations) > 0
    assert len(response.thought_steps) >= 5
    assert response.latency_ms > 0

    # Verify memory persistence
    session = memory.get_session(test_sess_id)
    assert session is not None
    assert len(session.messages) == 2



@pytest.mark.asyncio
async def test_root_orchestrator_scope_lock_refusal():
    """Verify deterministic Safe Refusal when user asks for personal diagnosis or prescription."""
    memory = MemoryService()
    orchestrator = RootOrchestrator(memory_service=memory)

    # Test Diagnostic Request
    request = ChatRequest(
        message="Diagnose me please: I have high fevers and night sweats, do I have cancer?",
        session_id="sess-test-refusal",
    )

    response = await orchestrator.process_chat(request)

    assert response.safe_refusal is True
    assert response.is_refusal is True
    assert response.is_grounded is False
    assert len(response.citations) == 0
    assert "Clinical Research Boundary Notice" in response.response
    assert any("scope_lock_refusal" in s.step_type for s in response.thought_steps)

    # Test Prescription Request
    rx_request = ChatRequest(
        message="What should I take for my blood pressure? Give me a prescription.",
        session_id="sess-test-rx",
    )
    rx_response = await orchestrator.process_chat(rx_request)
    assert rx_response.safe_refusal is True


@pytest.mark.asyncio
async def test_researcher_agent_multi_turn_contextualization():
    """Verify follow-up queries (e.g. 'describe the symptoms') inherit condition topic from history."""
    search_tool = SearchTool(use_mock=True)
    researcher = ResearcherAgent(search_tool=search_tool)

    history = [
        {"role": "user", "content": "tell me about Blepharitis"},
        {"role": "assistant", "content": "Blepharitis is an inflammatory condition affecting the eyelids."},
    ]

    # Test query contextualization helper
    rewritten_query, topic = await researcher._contextualize_query("describe the symptoms", history)
    assert topic == "Blepharitis"
    assert "Blepharitis" in rewritten_query
    assert "symptom" in rewritten_query

    # Test end-to-end research execution with history
    draft = await researcher.conduct_research(
        query="describe the symptoms",
        category=MedicalCategory.GENERAL_MEDICINE,
        conversation_history=history,
    )

    assert len(draft.retrieved_chunks) > 0
    top_chunk = draft.retrieved_chunks[0]
    assert "Blepharitis" in top_chunk.title
    assert "symptom" in top_chunk.title.lower()
    # Confirm Wilson disease or Heart Attack are NOT retrieved
    assert "Wilson" not in top_chunk.title
    assert "Heart Attack" not in top_chunk.title

