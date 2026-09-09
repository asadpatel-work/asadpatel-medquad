"""Unit tests for search, clinical DB, and citation verification tools."""

import json

import pytest

from backend.models.schemas import GroundedSearchResult, MedicalCategory
from backend.tools.citation_verifier import verify_response_citations
from backend.tools.clinical_db_tool import ClinicalDBTool, clinical_db_lookup_tool
from backend.tools.search_tool import SearchTool, medquad_search_tool


@pytest.mark.asyncio
async def test_search_tool_local_mode():
    """Verify local semantic search retrieves relevant chunks for clinical queries."""
    tool = SearchTool(use_mock=True)

    # Test Oncology Query
    results = await tool.search(
        "What are the symptoms and staging of Hodgkin Lymphoma?", category=MedicalCategory.ONCOLOGY
    )
    assert len(results) > 0
    top_result = results[0]
    assert "lymphoma" in top_result.content.lower() or "lymphoma" in top_result.title.lower()
    assert top_result.source_url.startswith("https://")
    assert top_result.score > 0.0

    # Test Cardiology Query
    cardio_results = await tool.search(
        "blood pressure hypertension medication targets", category=MedicalCategory.CARDIOLOGY
    )
    assert len(cardio_results) > 0
    assert any("hypertension" in r.content.lower() for r in cardio_results)


@pytest.mark.asyncio
async def test_medquad_search_tool_json_wrapper():
    """Verify JSON wrapper function formatted for ADK tool calling."""
    json_output = await medquad_search_tool(
        query="Diabetes diagnostic criteria HbA1c", category="Endocrinology", top_k=2
    )
    parsed = json.loads(json_output)
    assert isinstance(parsed, list)
    assert len(parsed) <= 2
    assert any(
        "diabetes" in item["content"].lower() or "hba1c" in item["content"].lower()
        for item in parsed
    )


def test_clinical_db_tool_queries():
    """Verify mock clinical database queries for labs, protocols, and drugs."""
    db = ClinicalDBTool()

    # 1. Lab Reference Range Query
    lab_res = db.query_lab_reference("hba1c")
    assert lab_res["status"] == "found"
    assert lab_res["data"]["test_name"] == "Hemoglobin A1c (HbA1c)"
    assert "< 5.7%" in lab_res["data"]["normal_range"]

    # 2. Trial Protocol Query
    trial_res = db.query_trial_protocol("NCI-2026-HL01")
    assert trial_res["status"] == "found"
    assert "Hodgkin Lymphoma" in trial_res["data"]["title"]
    assert len(trial_res["data"]["eligibility_criteria"]) >= 3

    # 3. Drug Interaction Query
    drug_res = db.query_drug_info("lisinopril")
    assert drug_res["status"] == "found"
    assert len(drug_res["data"]["major_interactions"]) > 0

    # 4. Unknown lookup
    unknown_res = db.query_lab_reference("nonexistent_test_xyz")
    assert unknown_res["status"] == "not_found"


def test_clinical_db_lookup_tool_wrapper():
    """Verify clinical_db_lookup_tool JSON output."""
    raw_res = clinical_db_lookup_tool(query_type="lab_reference", lookup_key="esr")
    data = json.loads(raw_res)
    assert data["status"] == "found"
    assert "Erythrocyte Sedimentation Rate" in data["data"]["test_name"]


def test_citation_verifier_valid_mapping():
    """Verify citation verifier successfully resolves valid inline citations."""
    sample_chunks = [
        GroundedSearchResult(
            chunk_id="chunk_1",
            doc_id="NIH-001",
            title="Hodgkin Lymphoma Overview",
            content="Reed-Sternberg cells are pathognomonic on biopsy.",
            source_url="https://cancer.gov/hl",
            topic_category=MedicalCategory.ONCOLOGY,
            score=0.95,
        ),
        GroundedSearchResult(
            chunk_id="chunk_2",
            doc_id="NIH-002",
            title="Staging Guidelines",
            content="Ann Arbor staging classifies stages I through IV.",
            source_url="https://cancer.gov/staging",
            topic_category=MedicalCategory.ONCOLOGY,
            score=0.90,
        ),
    ]

    text = "Hodgkin lymphoma is identified by Reed-Sternberg cells [1] and staged using Ann Arbor criteria [2]."
    res = verify_response_citations(text, sample_chunks)

    assert res.is_valid is True
    assert len(res.citations) == 2
    assert res.citations[0].citation_id == 1
    assert res.citations[0].doc_id == "NIH-001"
    assert res.citations[1].citation_id == 2
    assert res.citations[1].doc_id == "NIH-002"
    assert len(res.hallucinated_indices) == 0


def test_citation_verifier_detects_hallucination():
    """Verify citation verifier catches out-of-bounds citation indices."""
    sample_chunks = [
        GroundedSearchResult(
            chunk_id="chunk_1",
            doc_id="NIH-001",
            title="Hodgkin Lymphoma",
            content="Clinical facts.",
            source_url="https://cancer.gov/hl",
            topic_category=MedicalCategory.ONCOLOGY,
            score=0.95,
        ),
    ]

    # Reference [1] is valid, [5] is hallucinated since only 1 chunk exists
    text = "Hodgkin lymphoma overview [1] and non-existent study claim [5]."
    res = verify_response_citations(text, sample_chunks)

    assert res.is_valid is False
    assert 5 in res.hallucinated_indices
    assert len(res.citations) == 1
    assert "Hallucinated citations detected" in res.error_message


def test_citation_verifier_no_citations():
    """Verify citation verifier flags responses missing required citations."""
    sample_chunks = [
        GroundedSearchResult(
            chunk_id="chunk_1",
            doc_id="NIH-001",
            title="Hypertension",
            content="Clinical facts.",
            source_url="https://nhlbi.nih.gov",
            topic_category=MedicalCategory.CARDIOLOGY,
            score=0.95,
        ),
    ]

    text = "Hypertension should be managed with lifestyle modifications and medication."
    res = verify_response_citations(text, sample_chunks)

    assert res.is_valid is False
    assert res.citation_coverage_ratio == 0.0
    assert len(res.citations) == 0


@pytest.mark.asyncio
async def test_mcp_server_discovery_and_execution():
    """Verify MCP Tool Server tool manifest discovery and execution dispatch."""
    from backend.tools.mcp_server import get_mcp_server

    server = get_mcp_server()
    tools = server.list_tools()
    assert len(tools) >= 3
    tool_names = [t["name"] for t in tools]
    assert "medquad_search" in tool_names
    assert "clinical_db_lookup" in tool_names
    assert "verify_citations" in tool_names

    # Test tool execution
    search_res = await server.execute_tool(
        "medquad_search",
        {"query": "glioblastoma IDH mutation", "category": "Oncology", "top_k": 2},
    )
    assert search_res["status"] == "success"
    assert len(search_res["results"]) > 0
