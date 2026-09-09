"""Post-Hoc Conversation Evaluation and Auditing API routes."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.pipelines.post_hoc_validation import (
    PostHocValidationPipeline,
    ValidationBatchSummary,
)
from backend.services.memory_service import get_memory_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/evaluations", tags=["Evaluations"])


class ValidateRequest(BaseModel):
    session_id: str | None = None
    min_faithfulness: float = Field(default=3.5, ge=1.0, le=5.0)
    min_relevance: float = Field(default=3.5, ge=1.0, le=5.0)


@router.post("/validate", response_model=ValidationBatchSummary)
async def validate_conversations(request: ValidateRequest | None = None) -> ValidationBatchSummary:
    """Runs the post-hoc clinical conversation validation pipeline across stored sessions."""
    req = request or ValidateRequest()
    memory = get_memory_service()
    pipeline = PostHocValidationPipeline(memory_service=memory)

    if req.session_id:
        session = memory.get_session(req.session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {req.session_id} not found")
        summary = pipeline.validate_sessions(
            sessions=[session],
            min_faithfulness=req.min_faithfulness,
            min_relevance=req.min_relevance,
        )
    else:
        summary = pipeline.validate_stored_sessions(
            min_faithfulness=req.min_faithfulness,
            min_relevance=req.min_relevance,
        )

    # Persist report artifacts
    pipeline.save_reports(summary)
    return summary


@router.get("/reports/latest")
async def get_latest_report() -> dict:
    """Retrieves the most recent validation report summary and markdown content."""
    reports_dir = Path("reports")
    if not reports_dir.exists():
        raise HTTPException(status_code=404, detail="No evaluation reports found")

    md_files = sorted(reports_dir.glob("validation_report_*.md"), reverse=True)
    if not md_files:
        raise HTTPException(status_code=404, detail="No evaluation reports found")

    latest_md = md_files[0]
    latest_json = latest_md.with_suffix(".json")

    json_data = {}
    if latest_json.exists():
        import json
        json_data = json.loads(latest_json.read_text(encoding="utf-8"))

    return {
        "report_id": latest_md.stem,
        "markdown_content": latest_md.read_text(encoding="utf-8"),
        "summary": json_data,
    }


@router.post("/export")
async def export_conversations() -> dict:
    """Exports all stored conversations to an auditable JSONL file."""
    memory = get_memory_service()
    target_path = memory.export_sessions_to_jsonl()
    return {
        "status": "success",
        "file_path": str(target_path),
        "total_sessions": len(memory.list_sessions()),
    }
