"""Automated Data Ingestion and Vertex AI Search Grounding Pipeline for MedQuAD.

Ingests raw NIH MedQuAD XML files, extracts clinical Q&A pairs with authoritative
source metadata, chunks long responses preserving medical context, exports Discovery
Engine custom JSONL schemas, uploads to Google Cloud Storage, and triggers
Discovery Engine document import operations.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
from pydantic import BaseModel, Field

from backend.core.config import get_settings

logger = logging.getLogger("medquad_ingestion_pipeline")

# Authoritative Institute Mapping
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

# Sub-specialty keyword taxonomy for automatic metadata classification
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Oncology": [
        "cancer",
        "tumor",
        "carcinoma",
        "lymphoma",
        "leukemia",
        "melanoma",
        "sarcoma",
        "oncology",
        "chemotherapy",
        "radiation",
        "glioblastoma",
        "malignant",
        "metastasis",
        "neoplasm",
        "blastomas",
    ],
    "Cardiology": [
        "heart",
        "cardiac",
        "coronary",
        "hypertension",
        "arrhythmia",
        "infarction",
        "blood pressure",
        "atherosclerosis",
        "aneurysm",
        "aortic",
        "vascular",
        "heart failure",
        "angina",
        "troponin",
    ],
    "Infectious Disease": [
        "infection",
        "virus",
        "bacterial",
        "hiv",
        "hepatitis",
        "covid",
        "tuberculosis",
        "sepsis",
        "antibiotic",
        "flu",
        "influenza",
        "pneumonia",
        "fungal",
        "parasitic",
        "ebola",
        "measles",
    ],
    "Genetics & Rare Diseases": [
        "syndrome",
        "genetic",
        "mutation",
        "chromosome",
        "hereditary",
        "congenital",
        "recessive",
        "dominant",
        "dna",
        "rare disease",
    ],
    "Endocrinology": [
        "diabetes",
        "thyroid",
        "insulin",
        "glucose",
        "hormone",
        "endocrine",
        "pituitary",
        "adrenal",
        "cushing",
        "addison",
    ],
    "Neurology": [
        "brain",
        "neural",
        "neurological",
        "epilepsy",
        "seizure",
        "stroke",
        "parkinson",
        "alzheimer",
        "dementia",
        "sclerosis",
    ],
    "Pulmonology": [
        "lung",
        "pulmonary",
        "respiratory",
        "asthma",
        "copd",
        "bronchitis",
        "emphysema",
        "apnea",
        "cystic fibrosis",
    ],
    "Gastroenterology": [
        "liver",
        "hepatitis",
        "cirrhosis",
        "gastric",
        "colon",
        "bowel",
        "crohn",
        "colitis",
        "celiac",
        "pancreas",
    ],
    "Pharmacology & Therapeutics": [
        "drug",
        "medication",
        "dose",
        "dosage",
        "side effect",
        "interaction",
        "pharmaceutical",
        "tablet",
        "capsule",
        "prescription",
    ],
}


class MedQuADRecord(BaseModel):
    """Normalized medical Q&A document record."""

    id: str
    focus: str
    sub_specialty: str
    organization: str
    url: str
    question: str
    question_type: str
    answer: str
    token_count: int


class IngestionSummary(BaseModel):
    """Execution metrics and audit summary for the ingestion pipeline."""

    status: str = "completed"
    total_raw_files_scanned: int = 0
    total_qa_pairs_extracted: int = 0
    total_chunks_generated: int = 0
    gcs_uri: str | None = None
    datastore_id: str = ""
    discovery_engine_op: str | None = None
    duration_seconds: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class MedQuADIngestionPipeline:
    """End-to-End Automated Pipeline for MedQuAD Corpus Processing & Vertex AI Grounding."""

    def __init__(
        self,
        project_id: str | None = None,
        location: str = "global",
        datastore_id: str | None = None,
        bucket_name: str | None = None,
    ):
        settings = get_settings()
        self.project_id = project_id or settings.gcp_project_id
        self.location = location or settings.vertex_ai_search_location
        self.datastore_id = datastore_id or settings.vertex_ai_search_datastore_id
        self.bucket_name = bucket_name or settings.medquad_gcs_bucket.replace("gs://", "")

    @staticmethod
    def infer_sub_specialty(text: str) -> str:
        """Categorize clinical topics into medical sub-specialties."""
        lower = text.lower()
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if any(k in lower for k in keywords):
                return cat
        return "General Medicine"

    @staticmethod
    def clean_text(text: str | None) -> str:
        """Sanitizes text by removing XML entities, excess whitespace, and control chars."""
        if not text:
            return ""
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&[a-zA-Z]+;", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def parse_xml_file(self, file_path: Path) -> list[MedQuADRecord]:
        """Parses a single NIH MedQuAD XML file into structured records."""
        records: list[MedQuADRecord] = []
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except Exception:
            return records

        focus = self.clean_text(root.findtext("Focus", default=""))
        sub_specialty = self.infer_sub_specialty(focus)

        # Source Organization
        source_folder = file_path.parent.name
        matched_org = "National Institutes of Health (NIH)"
        for prefix, full_name in AUTHORITATIVE_ORGS.items():
            if prefix.lower() in source_folder.lower():
                matched_org = full_name
                break

        doc_url = self.clean_text(
            root.findtext("FocusAnnotations/UMLS/SemanticGroup", default="")
        ) or (
            f"https://medlineplus.gov/{re.sub(r'[^a-zA-Z0-9]+', '', focus.lower())}.html"
            if focus
            else "https://medlineplus.gov"
        )

        qa_pairs = root.findall(".//QAPair")
        for i, qa in enumerate(qa_pairs):
            q_elem = qa.find("Question")
            q_text = self.clean_text(q_elem.text if q_elem is not None else "")
            q_type = q_elem.get("qtype", "general") if q_elem is not None else "general"

            a_elem = qa.find("Answer")
            a_text = self.clean_text(a_elem.text if a_elem is not None else "")

            if not q_text or not a_text or len(a_text) < 20:
                continue

            doc_id = f"{file_path.stem}_q{i + 1}"
            approx_tokens = len(a_text.split())

            record = MedQuADRecord(
                id=doc_id,
                focus=focus or "General Health",
                sub_specialty=sub_specialty,
                organization=matched_org,
                url=doc_url,
                question=q_text,
                question_type=q_type,
                answer=a_text,
                token_count=approx_tokens,
            )
            records.append(record)

        return records

    def parse_raw_corpus(self, raw_dir: Path) -> tuple[list[MedQuADRecord], int]:
        """Scans all subdirectories of raw MedQuAD XML files."""
        all_records: list[MedQuADRecord] = []
        xml_files = list(raw_dir.glob("**/*.xml"))
        logger.info("Discovered %d raw XML files in %s", len(xml_files), raw_dir)

        for path in xml_files:
            recs = self.parse_xml_file(path)
            all_records.extend(recs)

        logger.info(
            "Successfully extracted %d Q&A records across %d files.",
            len(all_records),
            len(xml_files),
        )
        return all_records, len(xml_files)

    def chunk_records(
        self,
        records: list[MedQuADRecord],
        target_chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> list[dict[str, Any]]:
        """Splits lengthy clinical answers into overlapping semantic chunks with full citation context."""
        chunks: list[dict[str, Any]] = []

        for rec in records:
            words = rec.answer.split()
            if len(words) <= target_chunk_size:
                chunks.append(
                    {
                        "id": f"{rec.id}_c1",
                        "title": f"{rec.focus} - {rec.question}",
                        "focus": rec.focus,
                        "sub_specialty": rec.sub_specialty,
                        "question": rec.question,
                        "question_type": rec.question_type,
                        "organization": rec.organization,
                        "url": rec.url,
                        "chunk_index": 1,
                        "total_chunks": 1,
                        "content": f"Topic: {rec.focus}\nQuestion: {rec.question}\nAnswer: {rec.answer}",
                        "token_count": len(words),
                    }
                )
            else:
                step = target_chunk_size - chunk_overlap
                total_c = max(1, (len(words) - 1) // step + 1)
                for c_idx in range(total_c):
                    start = c_idx * step
                    end = min(len(words), start + target_chunk_size)
                    chunk_words = words[start:end]
                    chunk_body = " ".join(chunk_words)

                    chunks.append(
                        {
                            "id": f"{rec.id}_c{c_idx + 1}",
                            "title": f"{rec.focus} - {rec.question} (Part {c_idx + 1})",
                            "focus": rec.focus,
                            "sub_specialty": rec.sub_specialty,
                            "question": rec.question,
                            "question_type": rec.question_type,
                            "organization": rec.organization,
                            "url": rec.url,
                            "chunk_index": c_idx + 1,
                            "total_chunks": total_c,
                            "content": f"Topic: {rec.focus} (Part {c_idx + 1}/{total_c})\nQuestion: {rec.question}\nAnswer: {chunk_body}",
                            "token_count": len(chunk_words),
                        }
                    )

        logger.info("Generated %d chunks from %d Q&A records.", len(chunks), len(records))
        return chunks

    def export_discovery_engine_jsonl(
        self, chunks: list[dict[str, Any]], output_path: Path
    ) -> Path:
        """Exports chunks into Google Cloud Discovery Engine custom schema JSONL format."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for chunk in chunks:
                safe_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", chunk["id"])[:63]
                doc = {
                    "id": safe_id,
                    "jsonData": json.dumps(
                        {
                            "title": chunk["title"],
                            "content": chunk["content"],
                            "focus": chunk["focus"],
                            "sub_specialty": chunk["sub_specialty"],
                            "question": chunk["question"],
                            "question_type": chunk["question_type"],
                            "organization": chunk["organization"],
                            "url": chunk["url"],
                            "chunk_index": chunk["chunk_index"],
                            "total_chunks": chunk["total_chunks"],
                        }
                    ),
                }
                f.write(json.dumps(doc) + "\n")

        logger.info("✔ Exported %d Discovery Engine records to %s", len(chunks), output_path)
        return output_path

    def upload_to_gcs(self, local_path: Path, destination_blob: str) -> str:
        """Uploads JSONL to GCS bucket using gcloud storage or google-cloud-storage."""
        gcs_uri = f"gs://{self.bucket_name}/{destination_blob}"
        logger.info("Uploading %s to %s...", local_path, gcs_uri)

        try:
            subprocess.run(
                ["gcloud", "storage", "cp", str(local_path), gcs_uri],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.info("✔ Successfully uploaded to %s via gcloud storage", gcs_uri)
            return gcs_uri
        except Exception as e:
            logger.warning("gcloud storage cp failed: %s. Using google.cloud.storage client...", e)

        from google.cloud import storage

        client = storage.Client(project=self.project_id)
        bucket = client.bucket(self.bucket_name)
        blob = bucket.blob(destination_blob)
        blob.upload_from_filename(str(local_path))
        logger.info("✔ Successfully uploaded to %s via google-cloud-storage SDK", gcs_uri)
        return gcs_uri

    def trigger_discovery_engine_import(
        self,
        gcs_uri: str,
        reconciliation_mode: str = "INCREMENTAL",
    ) -> dict[str, Any]:
        """Submits an asynchronous Document Import operation to Vertex AI Search."""
        token = self._get_access_token()
        base_url = (
            f"https://discoveryengine.googleapis.com/v1/projects/{self.project_id}/"
            f"locations/{self.location}/collections/default_collection"
        )
        import_url = (
            f"{base_url}/dataStores/{self.datastore_id}/branches/default_branch/documents:import"
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Goog-User-Project": self.project_id,
        }

        payload = {
            "gcsSource": {
                "inputUris": [gcs_uri],
                "dataSchema": "custom",
            },
            "reconciliationMode": reconciliation_mode,
        }

        logger.info("Triggering Discovery Engine document import from %s...", gcs_uri)
        resp = requests.post(import_url, headers=headers, json=payload, timeout=30)
        if resp.status_code not in (200, 201):
            logger.error("Import failed (%s): %s", resp.status_code, resp.text)
            return {"error": resp.text, "status_code": resp.status_code}

        data = resp.json()
        logger.info("✔ Discovery Engine import operation initiated: %s", data.get("name"))
        return data

    @staticmethod
    def _get_access_token() -> str:
        """Retrieves an active OAuth2 access token for GCP APIs."""
        env_token = os.getenv("GOOGLE_OAUTH_TOKEN")
        if env_token:
            return env_token.strip()

        # Try application default credentials first
        try:
            return subprocess.check_output(
                ["gcloud", "auth", "application-default", "print-access-token"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except Exception:
            pass

        # Try CLI token
        try:
            return subprocess.check_output(
                ["gcloud", "auth", "print-access-token"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except Exception:
            pass

        import google.auth
        import google.auth.transport.requests

        credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)
        return credentials.token

    def execute_pipeline(
        self,
        raw_dir: Path | None = None,
        sync_vertex: bool = True,
    ) -> IngestionSummary:
        """Executes the full ingestion, chunking, GCS upload, and Datastore import pipeline."""
        start_time = time.time()
        raw_path = raw_dir or Path("data/medquad_raw")
        output_chunks_json = Path("data/full_medquad.json")
        output_jsonl = Path("data/full_medquad_documents.jsonl")

        if not raw_path.exists():
            raise FileNotFoundError(f"Raw MedQuAD directory {raw_path} does not exist.")

        # 1. Parse raw XML documents
        records, file_count = self.parse_raw_corpus(raw_path)

        # 2. Chunk records
        chunks = self.chunk_records(records, target_chunk_size=500, chunk_overlap=50)

        # Save local JSON chunks for local vector store fallback
        output_chunks_json.parent.mkdir(parents=True, exist_ok=True)
        with open(output_chunks_json, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2)

        # 3. Export Discovery Engine JSONL
        self.export_discovery_engine_jsonl(chunks, output_jsonl)

        # 4. Upload to GCS
        destination_blob = (
            f"corpus/medquad_documents_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.jsonl"
        )
        gcs_uri = self.upload_to_gcs(output_jsonl, destination_blob)

        # 5. Trigger Vertex AI Search Datastore import
        op_name = None
        if sync_vertex:
            try:
                op_result = self.trigger_discovery_engine_import(gcs_uri)
                op_name = op_result.get("name")
            except Exception as e:
                logger.warning("Could not initiate Discovery Engine import: %s", e)

        duration = round(time.time() - start_time, 2)
        summary = IngestionSummary(
            status="completed",
            total_raw_files_scanned=file_count,
            total_qa_pairs_extracted=len(records),
            total_chunks_generated=len(chunks),
            gcs_uri=gcs_uri,
            datastore_id=self.datastore_id,
            discovery_engine_op=op_name,
            duration_seconds=duration,
        )

        logger.info(
            "✔ MedQuAD Ingestion Pipeline complete in %.2fs: %d files, %d Q&As, %d chunks -> %s",
            duration,
            file_count,
            len(records),
            len(chunks),
            gcs_uri,
        )
        return summary
