"""MedQuAD Corpus Ingestion and Grounding API routes."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.pipelines.data_ingestion import IngestionSummary, MedQuADIngestionPipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/ingestion", tags=["Ingestion"])


class IngestRequest(BaseModel):
    raw_dir: str = "data/medquad_raw"
    sync_vertex: bool = Field(default=True, description="Whether to trigger Vertex AI Search import")


@router.post("/run", response_model=IngestionSummary)
async def trigger_ingestion(request: IngestRequest | None = None) -> IngestionSummary:
    """Executes the automated MedQuAD corpus ingestion and Vertex AI grounding pipeline."""
    req = request or IngestRequest()
    raw_path = Path(req.raw_dir)
    if not raw_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Raw data directory '{req.raw_dir}' not found on server.",
        )

    pipeline = MedQuADIngestionPipeline()
    try:
        summary = pipeline.execute_pipeline(raw_dir=raw_path, sync_vertex=req.sync_vertex)
        return summary
    except Exception as e:
        logger.error("Ingestion pipeline failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion pipeline failure: {str(e)}") from e


@router.get("/status")
async def get_ingestion_status() -> dict:
    """Returns local and cloud grounding corpus metadata."""
    corpus_json = Path("data/full_medquad.json")
    corpus_jsonl = Path("data/full_medquad_documents.jsonl")
    raw_dir = Path("data/medquad_raw")

    return {
        "raw_dir_exists": raw_dir.exists(),
        "local_chunk_corpus_exists": corpus_json.exists(),
        "local_chunk_size_bytes": corpus_json.stat().st_size if corpus_json.exists() else 0,
        "discovery_engine_jsonl_exists": corpus_jsonl.exists(),
        "discovery_engine_jsonl_size_bytes": corpus_jsonl.stat().st_size if corpus_jsonl.exists() else 0,
    }
