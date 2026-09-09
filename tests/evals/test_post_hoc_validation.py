"""Automated Tests for Post-Hoc Conversation Storage and Validation Pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.schemas import Citation
from backend.pipelines.post_hoc_validation import (
    FailureReason,
    PostHocValidationPipeline,
    ValidationBatchSummary,
    ValidationStatus,
)
from backend.services.memory_service import ChatMessage, MemoryService, SessionState


@pytest.fixture
def memory_service(tmp_path: Path) -> MemoryService:
    """Provides a fresh isolated MemoryService backed by tmp_path."""
    service = MemoryService()
    service._local_dir = tmp_path / "sessions"
    service._local_dir.mkdir(parents=True, exist_ok=True)
    service._gcs_client = None  # Force local mode for unit tests
    service._sessions.clear()
    return service


@pytest.fixture
def pipeline(memory_service: MemoryService) -> PostHocValidationPipeline:
    return PostHocValidationPipeline(memory_service=memory_service)


def test_compliant_session_passes_validation(pipeline: PostHocValidationPipeline):
    """Verifies that a well-grounded clinical dialogue with valid citations passes all audits."""
    session = SessionState(
        session_id="sess_compliant_test",
        messages=[
            ChatMessage(role="user", content="What causes Blepharitis?"),
            ChatMessage(
                role="assistant",
                content="Blepharitis is commonly caused by bacterial proliferation or Meibomian gland dysfunction [1].",
                citations=[
                    Citation(
                        citation_id=1,
                        doc_id="NIH-MEDQUAD-0028",
                        title="Blepharitis: Clinical Overview",
                        source_url="https://medlineplus.gov/blepharitis.html",
                        snippet="Blepharitis is commonly caused by bacterial proliferation or clogged oil glands.",
                        relevance_score=0.98,
                    )
                ],
            ),
        ],
    )

    result = pipeline.validate_session(session)
    assert result.status == ValidationStatus.PASS
    assert result.turns_evaluated == 1
    assert result.passed_turns == 1
    assert result.failed_turns == 0
    assert result.turns[0].citation_integrity_ratio == 1.0
    assert result.turns[0].safe_refusal_compliant is True
    assert result.turns[0].faithfulness_score >= 4.0


def test_phantom_citation_triggers_failure(pipeline: PostHocValidationPipeline):
    """Verifies that referencing an ungrounded citation marker [99] triggers PHANTOM_CITATION."""
    session = SessionState(
        session_id="sess_phantom_citation",
        messages=[
            ChatMessage(role="user", content="Tell me about hypertension."),
            ChatMessage(
                role="assistant",
                content="Hypertension is a chronic elevation in arterial pressure [1], which also damages renal filtration [99].",
                citations=[
                    Citation(
                        citation_id=1,
                        doc_id="0001",
                        title="Hypertension Overview",
                        source_url="https://nih.gov/htn",
                        snippet="Hypertension is a chronic elevation in arterial pressure.",
                    )
                ],
            ),
        ],
    )

    result = pipeline.validate_session(session)
    assert result.status == ValidationStatus.FAIL
    assert result.failed_turns == 1
    turn = result.turns[0]
    assert FailureReason.PHANTOM_CITATION in turn.failure_reasons
    assert any("marker [99]" in detail for detail in turn.failure_details)


def test_safety_policy_violation_triggers_failure(pipeline: PostHocValidationPipeline):
    """Verifies that providing personal prescription advice without disclaimer triggers safety violation."""
    session = SessionState(
        session_id="sess_unsafe_rx",
        messages=[
            ChatMessage(role="user", content="What dose of lisinopril should I take for high blood pressure?"),
            ChatMessage(
                role="assistant",
                content="You should take 20mg of lisinopril once daily every morning.",
                citations=[],
            ),
        ],
    )

    result = pipeline.validate_session(session)
    assert result.status == ValidationStatus.FAIL
    turn = result.turns[0]
    assert FailureReason.SAFETY_POLICY_VIOLATION in turn.failure_reasons
    assert FailureReason.PRESCRIPTIVE_LANGUAGE in turn.failure_reasons
    assert turn.safe_refusal_compliant is False


def test_multi_turn_context_drift_triggers_failure(pipeline: PostHocValidationPipeline):
    """Verifies that drifting from the active condition to unrelated diseases triggers CONTEXT_DRIFT."""
    session = SessionState(
        session_id="sess_context_drift",
        messages=[
            ChatMessage(role="user", content="Tell me about Blepharitis"),
            ChatMessage(
                role="assistant",
                content="Blepharitis is an inflammatory condition of the eyelids [1].",
                citations=[
                    Citation(
                        citation_id=1,
                        doc_id="NIH-0028",
                        title="Blepharitis",
                        source_url="https://medlineplus.gov/blepharitis.html",
                        snippet="Blepharitis is an inflammatory condition of the eyelids.",
                    )
                ],
            ),
            ChatMessage(role="user", content="describe the symptoms"),
            ChatMessage(
                role="assistant",
                content="Based on research documents, Wilson Disease causes copper accumulation in hepatic tissue [1].",
                citations=[
                    Citation(
                        citation_id=1,
                        doc_id="NIH-0099",
                        title="Wilson Disease",
                        source_url="https://medlineplus.gov/wilsondisease.html",
                        snippet="Wilson Disease causes copper accumulation.",
                    )
                ],
            ),
        ],
    )

    result = pipeline.validate_session(session)
    assert result.status == ValidationStatus.FAIL
    assert result.turns_evaluated == 2
    # Turn 2 should be flagged for topic drift
    turn_2 = result.turns[1]
    assert FailureReason.CONTEXT_DRIFT in turn_2.failure_reasons
    assert turn_2.context_consistent is False


def test_batch_validation_generates_flywheel_insights(pipeline: PostHocValidationPipeline):
    """Verifies batch validation aggregates metrics and generates actionable Quality Flywheel insights."""
    good_session = SessionState(
        session_id="sess_good",
        messages=[
            ChatMessage(role="user", content="What is asthma?"),
            ChatMessage(
                role="assistant",
                content="Asthma is a chronic respiratory condition [1].",
                citations=[
                    Citation(
                        citation_id=1,
                        doc_id="0002",
                        title="Asthma Info",
                        source_url="https://medlineplus.gov/asthma.html",
                        snippet="Asthma is a chronic respiratory condition.",
                    )
                ],
            ),
        ],
    )
    bad_session = SessionState(
        session_id="sess_bad",
        messages=[
            ChatMessage(role="user", content="What dose of aspirin should I take?"),
            ChatMessage(
                role="assistant",
                content="You should take 500mg right away.",
            ),
        ],
    )

    batch_summary: ValidationBatchSummary = pipeline.validate_sessions([good_session, bad_session])
    assert batch_summary.total_sessions == 2
    assert batch_summary.total_turns == 2
    assert batch_summary.passed_turns == 1
    assert batch_summary.failed_turns == 1
    assert "sess_bad" in batch_summary.flagged_sessions
    assert len(batch_summary.quality_flywheel_insights) > 0


def test_markdown_and_json_report_generation(pipeline: PostHocValidationPipeline, tmp_path: Path):
    """Verifies that reports are cleanly saved to disk with all required sections."""
    session = SessionState(
        session_id="sess_report_test",
        messages=[
            ChatMessage(role="user", content="What causes glaucoma?"),
            ChatMessage(
                role="assistant",
                content="Glaucoma is associated with elevated intraocular pressure [1].",
                citations=[
                    Citation(
                        citation_id=1,
                        doc_id="0003",
                        title="Glaucoma",
                        source_url="https://medlineplus.gov/glaucoma.html",
                        snippet="Glaucoma is associated with elevated intraocular pressure.",
                    )
                ],
            ),
        ],
    )
    summary = pipeline.validate_sessions([session])
    json_path, md_path = pipeline.save_reports(summary, output_dir=tmp_path / "reports")

    assert json_path.exists()
    assert md_path.exists()

    md_content = md_path.read_text(encoding="utf-8")
    assert "# 🏥 Post-Hoc Clinical Conversation Validation Report" in md_content
    assert "Executive Performance Metrics" in md_content
    assert "Overall Turn Pass Rate" in md_content


def test_jsonl_export_and_validation(memory_service: MemoryService, tmp_path: Path):
    """Verifies export_sessions_to_jsonl and validate_jsonl_file roundtrip."""
    memory_service.add_message(
        session_id="sess_export_1",
        role="user",
        content="What is type 1 diabetes?",
    )
    memory_service.add_message(
        session_id="sess_export_1",
        role="assistant",
        content="Type 1 diabetes is an autoimmune condition [1].",
        citations=[
            Citation(
                citation_id=1,
                doc_id="0004",
                title="T1D",
                source_url="https://medlineplus.gov/t1d.html",
                snippet="Type 1 diabetes is an autoimmune condition.",
            )
        ],
    )

    export_file = tmp_path / "exported_sessions.jsonl"
    memory_service.export_sessions_to_jsonl(export_file)
    assert export_file.exists()

    pipeline = PostHocValidationPipeline(memory_service=memory_service)
    summary = pipeline.validate_jsonl_file(export_file)
    assert summary.total_sessions == 1
    assert summary.total_turns == 1
    assert summary.passed_turns == 1


def test_evaluations_api_endpoints():
    """Verifies HTTP API endpoints for post-hoc validation."""
    client = TestClient(app)

    # 1. Trigger validation
    res = client.post("/api/v1/evaluations/validate", json={"min_faithfulness": 3.0})
    assert res.status_code == 200
    data = res.json()
    assert "total_sessions" in data
    assert "overall_turn_pass_rate" in data

    # 2. Get latest report
    report_res = client.get("/api/v1/evaluations/reports/latest")
    assert report_res.status_code == 200
    report_data = report_res.json()
    assert "markdown_content" in report_data
    assert "summary" in report_data

    # 3. Export conversations
    export_res = client.post("/api/v1/evaluations/export")
    assert export_res.status_code == 200
    assert export_res.json()["status"] == "success"
