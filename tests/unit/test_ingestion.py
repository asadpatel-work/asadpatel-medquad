"""Unit tests for MedQuAD ingestion and chunking logic."""

import json

from scripts.ingest_medquad import (
    chunk_text,
    estimate_token_count,
    generate_sample_dataset,
    infer_topic_category,
    parse_medquad_xml,
    process_records_to_chunks,
)

SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Document id="TEST-DOC-001" url="https://cancer.gov/lymphoma">
    <Focus>Hodgkin Lymphoma</Focus>
    <QAPairs>
        <QAPair pid="1">
            <Question qid="1" qtype="symptoms">What are the symptoms of Hodgkin Lymphoma?</Question>
            <Answer>Painless swelling of lymph nodes, persistent fever, and night sweats.</Answer>
        </QAPair>
        <QAPair pid="2">
            <Question qid="2" qtype="treatment">What are the treatments for Hodgkin Lymphoma?</Question>
            <Answer>Standard chemotherapy regimens such as ABVD combined with radiotherapy.</Answer>
        </QAPair>
    </QAPairs>
</Document>
"""


def test_parse_medquad_xml():
    """Verify XML parser extracts document attributes and QA pairs correctly."""
    records = parse_medquad_xml(SAMPLE_XML)
    assert len(records) == 2

    assert records[0].doc_id == "TEST-DOC-001"
    assert records[0].focus == "Hodgkin Lymphoma"
    assert records[0].question_id == "1"
    assert records[0].question_type == "symptoms"
    assert "symptoms" in records[0].question.lower()
    assert "painless swelling" in records[0].answer.lower()
    assert records[0].topic_category == "Oncology"
    assert records[0].source_url == "https://cancer.gov/lymphoma"

    assert records[1].question_id == "2"
    assert records[1].topic_category == "Oncology"


def test_infer_topic_category():
    """Verify clinical category classification for various medical conditions."""
    assert infer_topic_category("Patient has Glioblastoma multiforme brain tumor") == "Oncology"
    assert infer_topic_category("Essential hypertension systolic pressure > 140") == "Cardiology"
    assert (
        infer_topic_category("Acute viral hepatitis B infection and sepsis") == "Infectious Disease"
    )
    assert infer_topic_category("Juvenile pediatric onset type 1 diabetes") == "Endocrinology"
    assert infer_topic_category("General health wellness checkup routine") == "General Medicine"


def test_chunk_text_and_overlap():
    """Verify chunking maintains target token count and appropriate overlap."""
    text = " ".join([f"word{i}" for i in range(100)])
    chunks = chunk_text(text, target_tokens=40, overlap_tokens=10)

    assert len(chunks) > 1
    # Check that chunks have overlap
    words_chunk0 = set(chunks[0].split())
    words_chunk1 = set(chunks[1].split())
    assert len(words_chunk0.intersection(words_chunk1)) > 0


def test_process_records_to_chunks():
    """Verify conversion of records into search chunks with proper metadata."""
    records = generate_sample_dataset()
    assert len(records) >= 5

    chunks = process_records_to_chunks(records, target_tokens=200, overlap_tokens=30)
    assert len(chunks) >= len(records)

    first_chunk = chunks[0]
    assert first_chunk.chunk_id.startswith("NIH-MEDQUAD-0001")
    assert first_chunk.source_url.startswith("https://")
    assert first_chunk.authoritative_org != ""
    assert first_chunk.token_count_approx > 0
    assert "Topic:" in first_chunk.content
    assert "Question:" in first_chunk.content
    assert "Answer:" in first_chunk.content


def test_estimate_token_count():
    """Verify token count approximation formula."""
    text = "This is a clinical query with ten words in total here."
    count = estimate_token_count(text)
    assert count >= 10


def test_medquad_ingestion_pipeline_chunking_and_export(tmp_path):
    """Verify that MedQuADIngestionPipeline parses XML, chunks records, and exports Discovery Engine JSONL."""
    from backend.pipelines.data_ingestion import MedQuADIngestionPipeline

    pipeline = MedQuADIngestionPipeline()

    # Create temporary XML file
    xml_file = tmp_path / "test_medquad.xml"
    xml_file.write_text(SAMPLE_XML, encoding="utf-8")

    records = pipeline.parse_xml_file(xml_file)
    assert len(records) == 2
    assert records[0].focus == "Hodgkin Lymphoma"
    assert records[0].sub_specialty == "Oncology"
    assert records[0].token_count > 0

    chunks = pipeline.chunk_records(records, target_chunk_size=10, chunk_overlap=2)
    assert len(chunks) >= 2
    assert "Topic:" in chunks[0]["content"]

    output_jsonl = tmp_path / "discovery_engine.jsonl"
    pipeline.export_discovery_engine_jsonl(chunks, output_jsonl)
    assert output_jsonl.exists()

    lines = output_jsonl.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == len(chunks)
    first_doc = json.loads(lines[0])
    assert "id" in first_doc
    assert "jsonData" in first_doc
    inner_data = json.loads(first_doc["jsonData"])
    assert inner_data["focus"] == "Hodgkin Lymphoma"
