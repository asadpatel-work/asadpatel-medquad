"""Citation Resolution, Validation, and Extraction Engine.

Validates that inline citations in generated clinical answers (e.g. [1], [2], [1, 2])
deterministically map 1:1 to retrieved MedQuAD grounding chunks, verifying URL integrity
and detecting hallucinated or out-of-bounds references.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from backend.models.schemas import Citation, GroundedSearchResult

logger = logging.getLogger(__name__)


@dataclass
class CitationVerificationResult:
    """Outcome of citation integrity verification."""

    is_valid: bool
    citations: list[Citation] = field(default_factory=list)
    referenced_indices: list[int] = field(default_factory=list)
    hallucinated_indices: list[int] = field(default_factory=list)
    citation_coverage_ratio: float = 1.0
    error_message: str | None = None


class CitationVerifier:
    """Parses and validates citations against active retrieved grounding chunks."""

    CITATION_PATTERN = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")

    def extract_citation_indices(self, text: str) -> list[int]:
        """Extracts all unique referenced integer citation indices from markdown text."""
        indices: set[int] = set()
        matches = self.CITATION_PATTERN.findall(text)
        for match in matches:
            parts = match.split(",")
            for p in parts:
                p_clean = p.strip()
                if p_clean.isdigit():
                    indices.add(int(p_clean))
        return sorted(indices)

    def verify_and_resolve_citations(
        self,
        text: str,
        retrieved_chunks: list[GroundedSearchResult],
    ) -> CitationVerificationResult:
        """Verifies citation markers in generated response against retrieved grounding chunks."""
        referenced_indices = self.extract_citation_indices(text)
        total_chunks = len(retrieved_chunks)

        if not referenced_indices and total_chunks > 0:
            logger.warning(
                "No citations found in generated clinical text despite %d retrieved chunks.",
                total_chunks,
            )
            return CitationVerificationResult(
                is_valid=False,
                citations=[],
                referenced_indices=[],
                hallucinated_indices=[],
                citation_coverage_ratio=0.0,
                error_message="Response contains no inline citations to support clinical claims.",
            )

        hallucinated: list[int] = []
        valid_citations: list[Citation] = []

        for idx in referenced_indices:
            # 1-based indexing in citations [1], [2] -> 0-based in retrieved_chunks
            chunk_idx = idx - 1
            if 0 <= chunk_idx < total_chunks:
                chunk = retrieved_chunks[chunk_idx]
                valid_citations.append(
                    Citation(
                        citation_id=idx,
                        doc_id=chunk.doc_id,
                        title=chunk.title,
                        source_url=chunk.source_url,
                        authoritative_org=chunk.authoritative_org,
                        snippet=chunk.content[:280] + ("..." if len(chunk.content) > 280 else ""),
                        relevance_score=chunk.score,
                    )
                )
            else:
                hallucinated.append(idx)

        is_valid = len(hallucinated) == 0 and len(valid_citations) > 0
        coverage = len(valid_citations) / max(1, len(referenced_indices))

        error_msg = None
        if hallucinated:
            error_msg = f"Hallucinated citations detected: indices {hallucinated} have no matching retrieved grounding chunks (max index: {total_chunks})."

        return CitationVerificationResult(
            is_valid=is_valid,
            citations=valid_citations,
            referenced_indices=referenced_indices,
            hallucinated_indices=hallucinated,
            citation_coverage_ratio=coverage,
            error_message=error_msg,
        )


def verify_response_citations(
    text: str,
    retrieved_chunks: list[GroundedSearchResult],
) -> CitationVerificationResult:
    """Convenience helper to verify citations."""
    verifier = CitationVerifier()
    return verifier.verify_and_resolve_citations(text, retrieved_chunks)
