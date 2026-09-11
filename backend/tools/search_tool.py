"""Dual-mode MedQuAD Knowledge Search Tool.

Supports:
1. Live Mode: Google Cloud Vertex AI Search (Discovery Engine SearchServiceClient).
2. Local/Mock Mode: In-memory TF-IDF and keyword semantic retriever over data/sample_medquad.json.
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from backend.core.config import get_settings
from backend.models.schemas import GroundedSearchResult, MedicalCategory

logger = logging.getLogger(__name__)


# Common English and query stopwords that should not count toward document relevance
STOPWORDS: set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "hadn't", "has",
    "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's",
    "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
    "ought", "our", "ours", "ourselves", "out", "over", "own", "please", "same",
    "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some",
    "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves", "tell", "give", "explain", "describe", "discuss",
    "details", "information", "info", "overview",
}


def _stem(word: str) -> str:
    """Lightweight clinical / English suffix stemmer for morphological variants."""
    w = word.lower()
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith("es") and len(w) > 4:
        return w[:-2]
    if w.endswith("s") and len(w) > 3 and not w.endswith("ss"):
        return w[:-1]
    return w


GENERIC_TERMS: set[str] = {
    "clinical",
    "diagnostic",
    "features",
    "criteria",
    "management",
    "treatment",
    "treatments",
    "disease",
    "diseases",
    "symptoms",
    "symptom",
    "therapy",
    "therapies",
    "patient",
    "patients",
    "condition",
    "conditions",
    "guidelines",
    "protocol",
    "protocols",
}


class LocalVectorRetriever:
    """In-memory TF-IDF style semantic retriever for local testing and CI/CD."""

    def __init__(self, corpus_path: Path | str | None = None) -> None:
        self.chunks: list[dict[str, Any]] = []
        self.inverted_index: dict[str, set[int]] = defaultdict(set)
        self.doc_freq: dict[str, int] = defaultdict(int)
        if corpus_path:
            self.load_corpus(corpus_path)

    def load_corpus(self, corpus_path: Path | str) -> None:
        """Loads chunked records from JSON file and builds fast inverted index."""
        path = Path(corpus_path)
        if not path.exists():
            logger.warning("Corpus file %s not found. Initializing empty retriever.", path)
            return

        with open(path, encoding="utf-8") as f:
            self.chunks = json.load(f)

        self.inverted_index.clear()
        self.doc_freq.clear()

        # Build inverted index for sub-millisecond retrieval across full corpus
        for idx, chunk in enumerate(self.chunks):
            title = chunk.get("title", "")
            content = chunk.get("content", "")
            searchable_text = f"{title} {content}".lower()
            tokens = set(self._tokenize(searchable_text))
            for tok in tokens:
                self.inverted_index[tok].add(idx)
                stemmed = _stem(tok)
                if stemmed != tok:
                    self.inverted_index[stemmed].add(idx)

        for tok, doc_ids in self.inverted_index.items():
            self.doc_freq[tok] = len(doc_ids)

        logger.info(
            "Loaded %d grounding chunks into LocalVectorRetriever with %d indexed terms from %s",
            len(self.chunks),
            len(self.inverted_index),
            path,
        )

    def _tokenize(self, text: str) -> list[str]:
        """Tokenizes text into lowercase alphanumeric terms."""
        return re.findall(r"\b\w+\b", text.lower())

    def search(
        self,
        query: str,
        category: MedicalCategory | str | None = None,
        top_k: int = 3,
        min_score: float = 0.05,
    ) -> list[GroundedSearchResult]:
        """Calculates term frequency and relevance match against indexed chunks.

        Enforces strict stopword filtering, downweights generic clinical meta-terms,
        and ranks candidates by term-coverage weighted raw relevance scores.
        """
        if not self.chunks:
            return []

        query_terms = self._tokenize(query)
        if not query_terms:
            return []

        content_terms = [t for t in query_terms if t not in STOPWORDS and len(t) > 1]
        if not content_terms:
            content_terms = query_terms

        unique_content_terms = set(content_terms)
        entity_terms = [
            t
            for t in content_terms
            if t not in GENERIC_TERMS and _stem(t) not in GENERIC_TERMS and not t.isdigit()
        ]
        target_terms = entity_terms if entity_terms else content_terms

        # Fast candidate filtering using inverted index
        candidate_indices: set[int] = set()
        for t in target_terms:
            candidate_indices.update(self.inverted_index.get(t, set()))
            stemmed = _stem(t)
            if stemmed != t:
                candidate_indices.update(self.inverted_index.get(stemmed, set()))

        if not candidate_indices:
            return []

        scores: list[tuple[float, dict[str, Any]]] = []
        total_chunks = len(self.chunks)

        for idx in candidate_indices:
            chunk = self.chunks[idx]
            title = chunk.get("title", "")
            content = chunk.get("content", "")
            searchable_text = f"{title} {content}".lower()
            title_lower = title.lower()

            # Verify which content terms matched
            matched_terms = [
                t
                for t in unique_content_terms
                if t in searchable_text or _stem(t) in searchable_text
            ]
            if not matched_terms:
                continue

            # Compute term frequency matches with heavy title and entity weights
            match_score = 0.0
            for term in matched_terms:
                stemmed = _stem(term)
                weight = 0.3 if term in GENERIC_TERMS or stemmed in GENERIC_TERMS else 2.5

                tf_content = searchable_text.count(term)
                if stemmed != term:
                    tf_content += searchable_text.count(stemmed)

                tf_title = title_lower.count(term) * 8.0
                if stemmed != term:
                    tf_title += title_lower.count(stemmed) * 8.0

                df = self.doc_freq.get(term, 0)
                if stemmed != term:
                    df = max(df, self.doc_freq.get(stemmed, 0))

                idf_approx = math.log(1.0 + (total_chunks / (1.0 + df)))
                match_score += (tf_content + tf_title) * idf_approx * weight

            # Category filter if provided
            chunk_category = chunk.get("topic_category", "General Medicine")
            if category and str(category) != MedicalCategory.UNKNOWN.value:
                cat_str = category.value if isinstance(category, MedicalCategory) else str(category)
                if (
                    cat_str.lower() != chunk_category.lower()
                    and cat_str.lower() != "general medicine"
                ):
                    category_boost = 0.9
                else:
                    category_boost = 1.3
            else:
                category_boost = 1.0

            term_coverage = len(matched_terms) / len(unique_content_terms)
            ranking_score = match_score * (term_coverage ** 2) * category_boost

            if ranking_score >= min_score:
                scores.append((ranking_score, chunk))

        scores.sort(key=lambda x: x[0], reverse=True)
        if not scores:
            return []

        max_score = scores[0][0]
        results: list[GroundedSearchResult] = []
        for rank_score, chunk in scores[:top_k]:
            normalized_score = min(1.0, round(rank_score / max(max_score, 1e-6), 3))
            results.append(
                GroundedSearchResult(
                    chunk_id=chunk.get("chunk_id", "unknown-chunk"),
                    doc_id=chunk.get("doc_id", "unknown-doc"),
                    title=chunk.get("title", "Clinical Reference"),
                    content=chunk.get("content", ""),
                    source_url=chunk.get("source_url", "https://medlineplus.gov"),
                    topic_category=MedicalCategory(
                        chunk.get("topic_category", MedicalCategory.GENERAL_MEDICINE.value)
                    )
                    if chunk.get("topic_category") in MedicalCategory._value2member_map_
                    else MedicalCategory.GENERAL_MEDICINE,
                    authoritative_org=chunk.get("authoritative_org", "NIH"),
                    score=normalized_score,
                    metadata=chunk.get("metadata", {}),
                )
            )

        return results


# Global singleton instance of local retriever
_local_retriever_instance: LocalVectorRetriever | None = None


def get_local_retriever() -> LocalVectorRetriever:
    """Returns singleton local vector retriever."""
    global _local_retriever_instance
    if _local_retriever_instance is None:
        settings = get_settings()
        full_path = Path(settings.medquad_corpus_path)
        sample_path = Path("data/sample_medquad.json")
        corpus_path = full_path if full_path.exists() else sample_path
        _local_retriever_instance = LocalVectorRetriever(corpus_path)
    return _local_retriever_instance


class SearchTool:
    """Unified Search Tool with dual-mode dispatch (Cloud Vertex AI Search vs Local)."""

    def __init__(
        self,
        use_mock: bool | None = None,
        project_id: str | None = None,
        datastore_id: str | None = None,
        engine_id: str | None = None,
        location: str | None = None,
    ) -> None:
        settings = get_settings()
        self.use_mock = use_mock if use_mock is not None else settings.use_mock_search
        self.project_id = project_id or settings.gcp_project_id
        self.datastore_id = datastore_id or settings.vertex_ai_search_datastore_id
        self.engine_id = engine_id or getattr(settings, "vertex_ai_search_engine_id", "medquad-search-app-v1")
        self.location = location or settings.vertex_ai_search_location
        self.local_retriever = get_local_retriever()

    async def search(
        self,
        query: str,
        category: MedicalCategory | str | None = None,
        top_k: int = 3,
    ) -> list[GroundedSearchResult]:
        """Executes search query against Vertex AI Search or local mock retriever."""
        if self.use_mock or os.getenv("USE_MOCK_SEARCH", "").lower() == "true":
            logger.info(
                "Executing local mock MedQuAD search for query: '%s' (top_k=%d)", query, top_k
            )
            return self.local_retriever.search(query=query, category=category, top_k=top_k)

        # Live Vertex AI Search
        return await self._search_vertex_ai(query=query, category=category, top_k=top_k)

    async def _search_vertex_ai(
        self,
        query: str,
        category: MedicalCategory | str | None = None,
        top_k: int = 3,
    ) -> list[GroundedSearchResult]:
        """Invokes Google Cloud Discovery Engine SearchServiceClient with resilient config resolution."""
        try:
            from google.cloud import discoveryengine_v1 as discoveryengine

            client = discoveryengine.SearchServiceAsyncClient()

            # Attempt Engine first, then DataStore serving config
            serving_configs_to_try = [
                (
                    f"projects/{self.project_id}/locations/{self.location}/"
                    f"collections/default_collection/engines/{self.engine_id}/"
                    f"servingConfigs/default_search"
                ),
                (
                    f"projects/{self.project_id}/locations/{self.location}/"
                    f"collections/default_collection/dataStores/{self.datastore_id}/"
                    f"servingConfigs/default_search"
                ),
            ]

            response = None
            last_err = None
            for serving_config in serving_configs_to_try:
                try:
                    request = discoveryengine.SearchRequest(
                        serving_config=serving_config,
                        query=query,
                        page_size=top_k,
                        content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                            snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                                return_snippet=True
                            ),
                            summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                                summary_result_count=top_k,
                                include_citations=True,
                            ),
                        ),
                    )
                    response = await client.search(request)
                    break
                except Exception as err:
                    last_err = err
                    logger.debug("Serving config %s unavailable: %s", serving_config, err)

            if response is None:
                raise last_err or RuntimeError("No serving config could be reached")

            results: list[GroundedSearchResult] = []

            async for result in response:
                struct_data = dict(result.document.struct_data or {})
                if not struct_data and getattr(result.document, "json_data", None):
                    try:
                        struct_data = json.loads(result.document.json_data)
                    except Exception:
                        pass

                derived_data = dict(result.document.derived_struct_data or {})
                snippets = derived_data.get("snippets", [])
                snippet_text = (
                    snippets[0].get("snippet", "")
                    if snippets and snippets[0].get("snippet_status") != "NO_SNIPPET_AVAILABLE"
                    else ""
                )

                content = struct_data.get("content") or snippet_text or ""
                title = struct_data.get("title") or derived_data.get("title", "NIH Clinical Guideline")
                source_url = struct_data.get("source_url") or derived_data.get("link", "https://medlineplus.gov")
                category_str = struct_data.get("topic_category", "General Medicine")
                try:
                    cat_enum = MedicalCategory(category_str)
                except (ValueError, TypeError):
                    cat_enum = MedicalCategory.GENERAL_MEDICINE

                results.append(
                    GroundedSearchResult(
                        chunk_id=result.document.id or "vais-chunk",
                        doc_id=struct_data.get("doc_id", result.document.id),
                        title=title,
                        content=content,
                        source_url=source_url,
                        topic_category=cat_enum,
                        authoritative_org=struct_data.get("authoritative_org", "NIH"),
                        score=0.95,
                        metadata={**derived_data, **struct_data},
                    )
                )

            if not results:
                logger.info(
                    "Discovery Engine returned 0 results for '%s', falling back to local retriever.", query
                )
                return self.local_retriever.search(query=query, category=category, top_k=top_k)

            return results
        except Exception as e:
            logger.error("Vertex AI Search error: %s. Falling back to local retriever.", str(e))
            return self.local_retriever.search(query=query, category=category, top_k=top_k)


# Convenience function for direct ADK Tool registration
async def medquad_search_tool(
    query: str, category: str = "General Medicine", top_k: int = 3
) -> str:
    """Tool function: Searches the authoritative NIH MedQuAD database for medical literature, protocols, and symptoms.

    Args:
        query: The medical or clinical search query.
        category: Clinical sub-specialty (e.g. Oncology, Cardiology, Infectious Disease).
        top_k: Number of relevant grounding passages to return (default 3).

    Returns:
        JSON string containing list of grounded passages and citation metadata.
    """
    search_tool = SearchTool()
    results = await search_tool.search(query=query, category=category, top_k=top_k)
    return json.dumps([r.model_dump() for r in results], indent=2)
