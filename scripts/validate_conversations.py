#!/usr/bin/env python3
"""CLI Runner for Post-Hoc Clinical Conversation Validation Pipeline.

Usage:
    python scripts/validate_conversations.py --all
    python scripts/validate_conversations.py --session-id <session_id>
    python scripts/validate_conversations.py --input data/conversations/conversations_20260909.jsonl
    python scripts/validate_conversations.py --export
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.pipelines.post_hoc_validation import (  # noqa: E402
    PostHocValidationPipeline,
    ValidationBatchSummary,
)
from backend.services.memory_service import get_memory_service  # noqa: E402


def print_banner() -> None:
    print("=" * 80)
    print("🏥 MedQuAD Post-Hoc Clinical Conversation Validation Pipeline")
    print("   Auditing Citation Integrity, Safe Refusal, Topic Drift & Faithfulness")
    print("=" * 80)


def print_terminal_summary(summary: ValidationBatchSummary, json_path: Path, md_path: Path) -> None:
    print(f"\n📊 Audit Complete: {summary.total_sessions} Sessions | {summary.total_turns} Conversation Turns")
    print("-" * 80)
    print(f"{'Metric':<35} | {'Value':<15} | {'Compliance':<10}")
    print("-" * 80)
    print(
        f"{'Overall Turn Pass Rate':<35} | {summary.overall_turn_pass_rate * 100:.1f}%{'':<10} | {'✅ PASS' if summary.overall_turn_pass_rate >= 0.9 else '❌ FAIL'}"
    )
    print(
        f"{'Citation Integrity Rate':<35} | {summary.citation_integrity_rate * 100:.1f}%{'':<10} | {'✅ PASS' if summary.citation_integrity_rate >= 0.95 else '❌ FAIL'}"
    )
    print(
        f"{'Safe Refusal Adherence':<35} | {summary.safe_refusal_compliance_rate * 100:.1f}%{'':<10} | {'✅ PASS' if summary.safe_refusal_compliance_rate >= 1.0 else '❌ FAIL'}"
    )
    print(
        f"{'Multi-Turn Topic Consistency':<35} | {summary.multi_turn_consistency_rate * 100:.1f}%{'':<10} | {'✅ PASS' if summary.multi_turn_consistency_rate >= 0.9 else '❌ FAIL'}"
    )
    print(
        f"{'Mean Faithfulness Score':<35} | {summary.avg_faithfulness_score:.2f} / 5.0{'':<6} | {'✅ PASS' if summary.avg_faithfulness_score >= 4.0 else '⚠️ WARN'}"
    )
    print(
        f"{'Mean Answer Relevance':<35} | {summary.avg_relevance_score:.2f} / 5.0{'':<6} | {'✅ PASS' if summary.avg_relevance_score >= 4.0 else '⚠️ WARN'}"
    )
    print("-" * 80)

    if summary.common_failure_modes:
        print("\n⚠️  Identified Failure Modes:")
        for mode, count in summary.common_failure_modes.items():
            print(f"   * {mode}: {count} occurrence(s)")
    else:
        print("\n✅ Zero clinical failure modes identified across audited sessions.")

    print("\n💡 Quality Flywheel Action Items:")
    for idx, item in enumerate(summary.quality_flywheel_insights, start=1):
        print(f"   {idx}. {item}")

    print("\n📁 Artifacts Generated:")
    print(f"   * JSON Report:     {json_path}")
    print(f"   * Markdown Report: {md_path}")
    print("=" * 80)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run post-hoc conversation validation across MedQuAD consultation sessions."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Validate all stored conversation sessions.")
    group.add_argument("--session-id", type=str, help="Validate a specific session by ID.")
    group.add_argument("--input", type=str, help="Validate sessions from an exported JSONL file.")
    group.add_argument("--export", action="store_true", help="Export all stored sessions to data/conversations/*.jsonl.")

    parser.add_argument("--output-dir", type=str, default="reports", help="Directory to save audit reports.")
    parser.add_argument("--min-faithfulness", type=float, default=3.5, help="Minimum acceptable faithfulness score (1-5).")
    parser.add_argument("--min-relevance", type=float, default=3.5, help="Minimum acceptable relevance score (1-5).")

    args = parser.parse_args()
    print_banner()

    memory = get_memory_service()
    pipeline = PostHocValidationPipeline(memory_service=memory)

    if args.export:
        export_path = memory.export_sessions_to_jsonl()
        print(f"✅ Successfully exported stored sessions to: {export_path}")
        return 0

    if args.input:
        print(f"Auditing conversation export file: {args.input}")
        summary = pipeline.validate_jsonl_file(
            file_path=args.input,
            min_faithfulness=args.min_faithfulness,
            min_relevance=args.min_relevance,
        )
    elif args.session_id:
        print(f"Auditing single conversation session: {args.session_id}")
        session = memory.get_session(args.session_id)
        if not session:
            print(f"❌ Error: Session '{args.session_id}' not found in memory, local disk, or GCS.")
            return 1
        summary = pipeline.validate_sessions(
            sessions=[session],
            min_faithfulness=args.min_faithfulness,
            min_relevance=args.min_relevance,
        )
    else:  # --all
        session_ids = memory.list_sessions()
        if not session_ids:
            print("⚠️ No stored sessions found to validate. Run a chat query first.")
            return 0
        print(f"Auditing all {len(session_ids)} stored conversation session(s)...")
        summary = pipeline.validate_stored_sessions(
            session_ids=session_ids,
            min_faithfulness=args.min_faithfulness,
            min_relevance=args.min_relevance,
        )

    json_file, md_file = pipeline.save_reports(summary, output_dir=args.output_dir)
    print_terminal_summary(summary, json_file, md_file)

    # Return non-zero if critical failures were found
    return 1 if summary.failed_turns > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
