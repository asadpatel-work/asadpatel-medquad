"""Full MedQuAD Corpus Ingestion and Vertex AI Search Preparation Pipeline.

Ingests all 11,274 NIH MedQuAD XML files from the official corpus (CancerGov,
CDC, GARD, GHR, MedlinePlus, NIDDK, NINDS, SeniorHealth, NHLBI), normalizes
16,407+ medical Q&A pairs, applies a 500-token chunking strategy with 10% overlap,
and exports production artifacts for Google Cloud Vertex AI Search (Discovery Engine).
"""

from __future__ import annotations

import argparse
import base64
import glob
import json
import logging
import os
import re
import shutil
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest_full_medquad")

# Authoritative Institute Names
AUTHORITATIVE_ORGS: dict[str, str] = {
    "NINDS": "National Institute of Neurological Disorders and Stroke (NINDS)",
    "NHLBI": "National Heart, Lung, and Blood Institute (NHLBI)",
    "CancerGov": "National Cancer Institute (NCI / CancerGov)",
    "CDC": "Centers for Disease Control and Prevention (CDC)",
    "NIDDK": "National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK)",
    "GARD": "Genetic and Rare Diseases Information Center (GARD / NCATS)",
    "GHR": "Genetics Home Reference (GHR / NLM)",
    "MPlusHealthTopics": "MedlinePlus (NLM / NIH)",
    "MPlusDrugs": "MedlinePlus (NLM / NIH)",
    "MPlusHerbsSupplements": "MedlinePlus (NLM / NIH)",
    "ADAM": "MedlinePlus A.D.A.M. Encyclopedia (NLM / NIH)",
    "NIHSeniorHealth": "NIH Senior Health",
}

# Sub-specialty keyword taxonomy
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Oncology": [
        "cancer", "tumor", "carcinoma", "lymphoma", "leukemia", "melanoma",
        "sarcoma", "oncology", "chemotherapy", "radiation", "glioblastoma",
        "malignant", "metastasis", "neoplasm", "blastomas",
    ],
    "Cardiology": [
        "heart", "cardiac", "coronary", "hypertension", "arrhythmia",
        "infarction", "blood pressure", "atherosclerosis", "aneurysm",
        "aortic", "vascular", "heart failure", "angina", "troponin",
        "myocardial", "pericarditis", "endocarditis", "valvular",
    ],
    "Infectious Disease": [
        "infection", "virus", "bacterial", "hiv", "hepatitis", "covid",
        "tuberculosis", "sepsis", "antibiotic", "flu", "influenza",
        "fungal", "parasitic", "pneumonia", "pathogen",
    ],
    "Neurology": [
        "brain", "neurological", "seizure", "epilepsy", "parkinson",
        "alzheimer", "dementia", "stroke", "neuropathy", "aneurysm",
        "cerebral", "subarachnoid", "headache", "migraine", "spine",
        "meningitis", "encephalitis", "multiple sclerosis",
    ],
    "Endocrinology": [
        "diabetes", "thyroid", "insulin", "glucose", "hormone",
        "pituitary", "adrenal", "metabolic", "hba1c", "cushing",
        "addison", "hypothyroidism", "hyperthyroidism",
    ],
    "Pulmonology": [
        "lung", "respiratory", "asthma", "copd", "bronchitis",
        "pulmonary", "cystic fibrosis", "emphysema", "hypoxemia",
    ],
    "Pediatrics": [
        "child", "infant", "pediatric", "congenital", "newborn",
        "juvenile", "syndrome", "neonatal",
    ],
}

FOLDER_DEFAULT_CATEGORY: dict[str, str] = {
    "1_CancerGov_QA": "Oncology",
    "5_NIDDK_QA": "Endocrinology",
    "6_NINDS_QA": "Neurology",
    "8_NHLBI_QA_XML": "Cardiology",
    "9_CDC_QA": "Infectious Disease",
}


@dataclass
class MedQuADRecord:
    """Normalized medical Q&A document record."""

    doc_id: str
    focus: str
    question_id: str
    question_type: str
    question: str
    answer: str
    topic_category: str
    source_url: str
    authoritative_org: str = "National Institutes of Health (NIH)"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MedQuADChunk:
    """Chunked document segment for embedding and vector indexing."""

    chunk_id: str
    doc_id: str
    question_id: str
    title: str
    content: str
    topic_category: str
    source_url: str
    authoritative_org: str
    token_count_approx: int
    metadata: dict[str, Any] = field(default_factory=dict)


def infer_topic_category(text: str, default_category: str = "General Medicine") -> str:
    """Classifies clinical text into standard medical categories based on keywords."""
    lower_text = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(re.search(r"\b" + re.escape(kw) + r"\b", lower_text) for kw in keywords):
            return category
    return default_category


def chunk_text(
    text: str,
    target_tokens: int = 500,
    overlap_tokens: int = 50,
) -> list[str]:
    """Splits text into chunks of target_tokens with overlap_tokens overlap."""
    words = text.split()
    if not words:
        return []

    words_per_chunk = max(10, int(target_tokens / 1.3))
    words_overlap = max(2, int(overlap_tokens / 1.3))
    step = max(1, words_per_chunk - words_overlap)

    chunks = []
    for i in range(0, len(words), step):
        chunk_words = words[i : i + words_per_chunk]
        chunks.append(" ".join(chunk_words))
        if i + words_per_chunk >= len(words):
            break

    return chunks


def parse_xml_file(file_path: str | Path) -> list[MedQuADRecord]:
    """Parses a single NIH MedQuAD XML file into normalized Q&A records."""
    file_path = Path(file_path)
    parent_folder = file_path.parent.name
    default_cat = FOLDER_DEFAULT_CATEGORY.get(parent_folder, "General Medicine")

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        root = ET.fromstring(content)
    except Exception as e:
        logger.debug("Error parsing XML %s: %s", file_path, e)
        return []

    doc_id = root.attrib.get("id") or root.attrib.get("docid") or file_path.stem
    source_code = root.attrib.get("source") or root.attrib.get("corpus") or parent_folder
    source_url = root.attrib.get("url") or "https://medlineplus.gov"
    authoritative_org = AUTHORITATIVE_ORGS.get(source_code, "National Institutes of Health (NIH)")

    focus_elem = root.find("Focus")
    focus = (
        focus_elem.text.strip()
        if focus_elem is not None and focus_elem.text
        else "General Medical Topic"
    )

    records: list[MedQuADRecord] = []
    qa_pairs = root.findall(".//QAPair")
    for qa in qa_pairs:
        qid = qa.attrib.get("pid", "0")
        q_elem = qa.find("Question")
        a_elem = qa.find("Answer")

        question_text = q_elem.text.strip() if q_elem is not None and q_elem.text else ""
        answer_text = a_elem.text.strip() if a_elem is not None and a_elem.text else ""
        q_type = q_elem.attrib.get("qtype", "information") if q_elem is not None else "information"

        if not question_text or not answer_text:
            continue

        combined_text = f"{focus} {question_text} {answer_text}"
        category = infer_topic_category(combined_text, default_category=default_cat)

        records.append(
            MedQuADRecord(
                doc_id=doc_id,
                focus=focus,
                question_id=qid,
                question_type=q_type,
                question=question_text,
                answer=answer_text,
                topic_category=category,
                source_url=source_url,
                authoritative_org=authoritative_org,
                metadata={
                    "focus": focus,
                    "question_type": q_type,
                    "source_code": source_code,
                    "file": file_path.name,
                },
            )
        )

    return records


def process_records_to_chunks(
    records: list[MedQuADRecord],
    target_tokens: int = 500,
    overlap_tokens: int = 50,
) -> list[MedQuADChunk]:
    """Converts normalized records into searchable chunk representations."""
    all_chunks: list[MedQuADChunk] = []
    for record in records:
        full_content = (
            f"Topic: {record.focus}\n"
            f"Category: {record.topic_category}\n"
            f"Question: {record.question}\n\n"
            f"Answer: {record.answer}"
        )

        text_chunks = chunk_text(
            full_content,
            target_tokens=target_tokens,
            overlap_tokens=overlap_tokens,
        )

        for idx, chunk_str in enumerate(text_chunks):
            chunk_id = f"{record.doc_id}_q{record.question_id}_c{idx + 1}"
            clean_chunk_id = re.sub(r"[^a-zA-Z0-9_\-]", "-", chunk_id)
            all_chunks.append(
                MedQuADChunk(
                    chunk_id=clean_chunk_id,
                    doc_id=record.doc_id,
                    question_id=record.question_id,
                    title=f"{record.focus}: {record.question}",
                    content=chunk_str,
                    topic_category=record.topic_category,
                    source_url=record.source_url,
                    authoritative_org=record.authoritative_org,
                    token_count_approx=max(1, int(len(chunk_str.split()) * 1.3)),
                    metadata=record.metadata,
                )
            )

    return all_chunks


def parse_full_corpus(raw_dir: Path) -> list[MedQuADRecord]:
    """Parses all XML files in the raw MedQuAD corpus directory."""
    xml_files = sorted(glob.glob(str(raw_dir / "**" / "*.xml"), recursive=True))
    logger.info("Found %d XML files in %s", len(xml_files), raw_dir)

    all_records: list[MedQuADRecord] = []
    start_time = time.time()
    for idx, xml_path in enumerate(xml_files):
        records = parse_xml_file(xml_path)
        all_records.extend(records)
        if (idx + 1) % 2500 == 0 or (idx + 1) == len(xml_files):
            elapsed = time.time() - start_time
            logger.info(
                "Parsed %d/%d files: %d valid Q&A records so far (%.1fs)",
                idx + 1,
                len(xml_files),
                len(all_records),
                elapsed,
            )

    return all_records


def export_full_corpus(
    records: list[MedQuADRecord],
    output_records_path: Path,
    output_chunks_path: Path,
    output_jsonl_path: Path,
) -> None:
    """Exports normalized records, chunks, and Discovery Engine JSONL."""
    output_records_path.parent.mkdir(parents=True, exist_ok=True)
    records_data = [asdict(r) for r in records]
    with open(output_records_path, "w", encoding="utf-8") as f:
        json.dump(records_data, f, indent=2)
    logger.info("Saved %d records to %s", len(records_data), output_records_path)

    chunks = process_records_to_chunks(records)
    chunks_data = [asdict(c) for c in chunks]
    with open(output_chunks_path, "w", encoding="utf-8") as f:
        json.dump(chunks_data, f, indent=2)
    logger.info("Saved %d chunks to %s", len(chunks_data), output_chunks_path)

    output_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_jsonl_path, "w", encoding="utf-8") as f:
        for c in chunks_data:
            content_text = f"Topic: {c['title']}\nCategory: {c['topic_category']}\n\n{c['content']}"
            content_b64 = base64.b64encode(content_text.encode("utf-8")).decode("utf-8")

            struct_fields = {
                "doc_id": c["doc_id"],
                "chunk_id": c["chunk_id"],
                "title": c["title"],
                "content": c["content"],
                "topic_category": c["topic_category"],
                "source_url": c["source_url"],
                "authoritative_org": c["authoritative_org"],
            }

            doc_entry = {
                "_id": c["chunk_id"],
                "id": c["chunk_id"],
                "jsonData": json.dumps(struct_fields),
                "structData": struct_fields,
                "content": {
                    "mimeType": "text/plain",
                    "rawBytes": content_b64,
                },
            }
            f.write(json.dumps(doc_entry) + "\n")

    logger.info("Saved %d Discovery Engine documents to %s", len(chunks_data), output_jsonl_path)


def main() -> None:
    """CLI entrypoint for full MedQuAD ingestion."""
    parser = argparse.ArgumentParser(description="Full MedQuAD Corpus Ingestion Tool")
    parser.add_argument(
        "--raw-dir",
        type=str,
        default="data/medquad_raw",
        help="Directory containing MedQuAD raw XML folders",
    )
    parser.add_argument(
        "--output-records",
        type=str,
        default="data/full_medquad_records.json",
        help="Path for parsed records JSON",
    )
    parser.add_argument(
        "--output-chunks",
        type=str,
        default="data/full_medquad.json",
        help="Path for chunked dataset JSON",
    )
    parser.add_argument(
        "--output-jsonl",
        type=str,
        default="data/full_medquad_documents.jsonl",
        help="Path for Discovery Engine JSONL",
    )
    parser.add_argument(
        "--sync-default-paths",
        action="store_true",
        default=True,
        help="Also update data/medquad_documents.jsonl with full corpus",
    )

    args = parser.parse_args()

    raw_path = Path(args.raw_dir)
    if not raw_path.exists():
        logger.error("Raw directory %s does not exist! Please ensure MedQuAD is cloned.", raw_path)
        sys.exit(1)

    logger.info("Starting ingestion of full MedQuAD corpus from %s...", raw_path)
    records = parse_full_corpus(raw_path)

    # Also include any custom/curated clinical records from ingest_medquad
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from scripts.ingest_medquad import generate_sample_dataset
        curated_records = generate_sample_dataset()
        logger.info("Merging %d high-yield clinical guideline records...", len(curated_records))
        records.extend(curated_records)
    except Exception as e:
        logger.warning("Could not merge curated sample records: %s", e)

    output_records = Path(args.output_records)
    output_chunks = Path(args.output_chunks)
    output_jsonl = Path(args.output_jsonl)

    export_full_corpus(
        records=records,
        output_records_path=output_records,
        output_chunks_path=output_chunks,
        output_jsonl_path=output_jsonl,
    )

    if getattr(args, "sync_default_paths", True):
        # Also copy to data/medquad_documents.jsonl so default imports use full corpus
        default_jsonl = Path("data/medquad_documents.jsonl")
        logger.info("Synchronizing %s with full corpus Discovery Engine JSONL...", default_jsonl)
        shutil.copyfile(output_jsonl, default_jsonl)
        logger.info("✔ %s updated.", default_jsonl)

    logger.info("Full MedQuAD ingestion completed successfully.")


if __name__ == "__main__":
    main()
