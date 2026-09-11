#!/usr/bin/env python3
"""CLI Runner for the MedQuAD Automated Ingestion Pipeline.

Usage:
    python scripts/run_medquad_ingestion_pipeline.py [--raw-dir data/medquad_raw] [--no-vertex-sync]
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Ensure root directory is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.pipelines.data_ingestion import MedQuADIngestionPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("run_medquad_ingestion_pipeline")


def main() -> None:
    parser = argparse.ArgumentParser(description="MedQuAD Automated Ingestion Pipeline Runner")
    parser.add_argument(
        "--raw-dir",
        type=str,
        default="data/medquad_raw",
        help="Path to raw MedQuAD XML files",
    )
    parser.add_argument(
        "--no-vertex-sync",
        action="store_true",
        help="Skip triggering Vertex AI Search document import",
    )

    args = parser.parse_args()
    raw_dir = Path(args.raw_dir)

    logger.info("Starting MedQuAD Ingestion Pipeline...")
    pipeline = MedQuADIngestionPipeline()
    summary = pipeline.execute_pipeline(
        raw_dir=raw_dir,
        sync_vertex=not args.no_vertex_sync,
    )

    print("\n" + "=" * 60)
    print("MEDQUAD INGESTION PIPELINE SUMMARY")
    print("=" * 60)
    print(f"Status:                    {summary.status}")
    print(f"Total Raw Files Scanned:   {summary.total_raw_files_scanned}")
    print(f"Total Q&A Pairs Extracted: {summary.total_qa_pairs_extracted}")
    print(f"Total Chunks Generated:    {summary.total_chunks_generated}")
    print(f"GCS Destination:           {summary.gcs_uri}")
    print(f"Target Datastore ID:       {summary.datastore_id}")
    print(f"Discovery Engine Op:       {summary.discovery_engine_op}")
    print(f"Execution Duration:        {summary.duration_seconds}s")
    print(f"Timestamp:                 {summary.timestamp}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
