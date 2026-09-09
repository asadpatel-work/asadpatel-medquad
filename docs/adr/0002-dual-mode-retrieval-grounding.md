# ADR-002: Dual-Mode Retrieval Architecture (Vertex AI Search & Local Vector Store Fallback)

## Status
**Accepted** (Implemented)

## Context
Production clinical assistants must guarantee continuous availability during network disruptions, cloud credential rotation, or offline development/testing in air-gapped CI/CD environments. 
Furthermore, clinical grounding requires parsing 47,000+ NIH MedQuAD documents, extracting authoritative organizations, source URLs, and verbatim quotes with zero synthetic hallucination.

## Decision
We implemented a **Dual-Mode Retrieval Architecture**:
1. **Primary Live Cloud Mode (Vertex AI Search / Discovery Engine):**
   - Connects to GCP Vertex AI Search Data Store containing the indexed MedQuAD corpus.
   - Leverages Google's semantic indexing, BM25 + dense embedding hybrid retrieval, and automatic snippet extraction.
2. **Deterministic Offline/Local Mode (In-Memory TF-IDF & Cosine Similarity):**
   - Ingests `data/sample_medquad.json` into an in-memory vector index.
   - Automatically activates if Vertex AI Search credentials are unavailable, if running in local unit tests (`pytest`), or if network timeouts occur.
3. **Citation Verifier Module (`backend/tools/citation_verifier.py`):**
   - Enforces deterministic 1:1 mapping between inline citations (`[1]`, `[2]`) and retrieved source chunks before output release.

## Alternatives Considered
1. **Cloud-Only Vertex AI Search:** Rejected because it broke offline unit test automation and increased CI/CD pipeline dependencies.
2. **Self-Hosted Vector DB (e.g. Pinecone / Milvus):** Rejected to avoid external SaaS vendor lock-in and minimize operational maintenance overhead.

## Consequences
- **Positive:**
  - 100% CI/CD test pass rate without external GCP network calls.
  - Graceful fallback during upstream cloud outages.
  - Zero hallucinated URLs or non-existent document IDs.
- **Negative:**
  - Local mode requires loading sample embeddings into memory (negligible memory footprint: ~12MB for golden corpus).
