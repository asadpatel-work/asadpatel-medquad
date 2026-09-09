"""Unit tests for conversation memory and session state management."""

from backend.models.schemas import AgentThoughtStep, Citation
from backend.services.memory_service import MemoryService


def test_memory_service_session_lifecycle():
    """Verify session creation, message appending, retrieval, and deletion."""
    memory = MemoryService()

    # 1. Create session
    session = memory.get_or_create_session("sess-001", metadata={"user": "dr_vance"})
    assert session.session_id == "sess-001"
    assert session.metadata["user"] == "dr_vance"
    assert len(session.messages) == 0

    # 2. Add User Message
    msg1 = memory.add_message(
        "sess-001", role="user", content="What are the diagnostic markers for glioblastoma?"
    )
    assert msg1.role == "user"
    assert len(session.messages) == 1

    # 3. Add Assistant Message with Citation and Thought Step
    citation = Citation(
        citation_id=1,
        doc_id="NIH-006",
        title="Glioblastoma Markers",
        source_url="https://cancer.gov",
        snippet="IDH1 mutation and MGMT promoter methylation.",
    )
    thought = AgentThoughtStep(
        agent_name="Researcher Subagent",
        step_type="search",
        description="Searched MedQuAD for glioblastoma markers.",
    )
    msg2 = memory.add_message(
        "sess-001",
        role="assistant",
        content="Key markers include IDH mutation and MGMT methylation [1].",
        citations=[citation],
        thought_steps=[thought],
    )
    assert msg2.role == "assistant"
    assert len(msg2.citations) == 1
    assert len(msg2.thought_steps) == 1
    assert len(session.messages) == 2

    # 4. History formatting
    history = memory.get_history_formatted("sess-001")
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"

    # 5. List and Delete
    assert "sess-001" in memory.list_sessions()
    deleted = memory.delete_session("sess-001")
    assert deleted is True
    assert memory.get_session("sess-001") is None
