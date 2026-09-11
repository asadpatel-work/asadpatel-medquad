#!/usr/bin/env python3
"""Format, upload, and import the full MedQuAD corpus into Google Cloud Discovery Engine (Vertex AI Search).

Imports documents from data/full_medquad_documents.jsonl (or data/medquad_documents.jsonl)
into the Cloud Storage bucket and triggers the Discovery Engine document import operation.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("import_medquad")

DEFAULT_PROJECT_ID = "capstone-506616"
DEFAULT_LOCATION = "global"
DEFAULT_DATASTORE_ID = "medquad-corpus-ds"
DEFAULT_BUCKET_NAME = f"{DEFAULT_PROJECT_ID}-medquad-corpus"


def get_access_token() -> str:
    """Retrieves an access token using gcloud or google-auth."""
    # Try environment variable first
    env_token = os.getenv("GOOGLE_OAUTH_TOKEN") or os.getenv("VERTEX_API_TOKEN")
    if env_token:
        return env_token.strip()

    # Try gcloud CLI
    try:
        token = subprocess.check_output(
            ["gcloud", "auth", "print-access-token"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if token:
            return token
    except Exception:
        pass

    # Try google-auth library
    try:
        import google.auth
        import google.auth.transport.requests

        credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)
        return credentials.token
    except Exception as e:
        logger.error("Could not obtain Google Cloud access token: %s", e)
        raise RuntimeError("Authentication failed. Please run 'gcloud auth login' or provide credentials.") from e


def upload_to_gcs(local_file: Path, bucket_name: str, destination_blob: str) -> str:
    """Uploads local JSONL file to Google Cloud Storage."""
    gcs_uri = f"gs://{bucket_name}/{destination_blob}"
    logger.info("Uploading %s to %s...", local_file, gcs_uri)

    try:
        subprocess.run(
            ["gcloud", "storage", "cp", str(local_file), gcs_uri],
            check=True,
        )
        logger.info("✔ Successfully uploaded to %s", gcs_uri)
        return gcs_uri
    except Exception as e:
        logger.warning("gcloud storage cp failed: %s. Attempting python google-cloud-storage...", e)

    try:
        from google.cloud import storage

        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(destination_blob)
        blob.upload_from_filename(str(local_file))
        logger.info("✔ Successfully uploaded to %s via google-cloud-storage", gcs_uri)
        return gcs_uri
    except Exception as e:
        logger.error("Failed to upload to Cloud Storage: %s", e)
        raise


def trigger_import(
    project_id: str,
    location: str,
    datastore_id: str,
    gcs_uri: str,
    reconciliation_mode: str = "INCREMENTAL",
    token: str | None = None,
) -> dict:
    """Initiates Discovery Engine documents:import long-running operation."""
    if not token:
        token = get_access_token()

    base_url = (
        f"https://discoveryengine.googleapis.com/v1/projects/{project_id}/"
        f"locations/{location}/collections/default_collection"
    )
    import_url = f"{base_url}/dataStores/{datastore_id}/branches/default_branch/documents:import"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id,
    }

    import_payload = {
        "gcsSource": {
            "inputUris": [gcs_uri],
            "dataSchema": "custom",
        },
        "reconciliationMode": reconciliation_mode,
    }

    logger.info("Submitting Document Import request to Discovery Engine at %s...", import_url)
    resp = requests.post(import_url, headers=headers, json=import_payload)

    if resp.status_code not in (200, 201):
        logger.error("Import request failed: %s %s", resp.status_code, resp.text)
        return {"error": resp.text, "status_code": resp.status_code}

    op_data = resp.json()
    op_name = op_data.get("name")
    logger.info("✔ Import operation submitted: %s", op_name)
    return op_data


def poll_operation(op_name: str, project_id: str) -> None:
    """Polls the long-running operation until completion."""
    op_url = f"https://discoveryengine.googleapis.com/v1/{op_name}"
    logger.info("Polling operation status from %s...", op_url)

    while True:
        try:
            token = get_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Goog-User-Project": project_id,
            }
            resp = requests.get(op_url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("done"):
                    logger.info("🎉 Import operation completed!")
                    logger.info("%s", json.dumps(data, indent=2))
                    break
                logger.info("Import in progress... (waiting 10s)")
            else:
                logger.warning("Operation poll status: %s %s", resp.status_code, resp.text)
        except Exception as e:
            logger.warning("Poll error: %s", e)

        time.sleep(10)


def main() -> None:
    """CLI Entrypoint for MedQuAD Vertex AI Search document import."""
    parser = argparse.ArgumentParser(description="Import MedQuAD corpus into Vertex AI Search")
    parser.add_argument(
        "--input-file",
        type=str,
        default="data/full_medquad_documents.jsonl",
        help="Path to prepared Discovery Engine JSONL file",
    )
    parser.add_argument(
        "--project-id",
        type=str,
        default=os.getenv("GCP_PROJECT_ID", DEFAULT_PROJECT_ID),
        help="GCP Project ID",
    )
    parser.add_argument(
        "--location",
        type=str,
        default=os.getenv("VERTEX_LOCATION", DEFAULT_LOCATION),
        help="Discovery Engine location (default: global)",
    )
    parser.add_argument(
        "--datastore-id",
        type=str,
        default=os.getenv("VERTEX_DATASTORE_ID", DEFAULT_DATASTORE_ID),
        help="Discovery Engine DataStore ID (default: medquad-corpus-ds)",
    )
    parser.add_argument(
        "--bucket-name",
        type=str,
        default=os.getenv("MEDQUAD_GCS_BUCKET", DEFAULT_BUCKET_NAME).replace("gs://", ""),
        help="Target GCS bucket for corpus documents",
    )
    parser.add_argument(
        "--reconciliation-mode",
        type=str,
        choices=["INCREMENTAL", "FULL"],
        default="INCREMENTAL",
        help="Import mode (INCREMENTAL or FULL)",
    )
    parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="Skip GCS upload and use existing URI",
    )
    parser.add_argument(
        "--poll",
        action="store_true",
        default=False,
        help="Poll operation until completion",
    )

    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        fallback_path = Path("data/medquad_documents.jsonl")
        if fallback_path.exists():
            input_path = fallback_path
        else:
            logger.error("Input file %s not found. Please run scripts/ingest_full_medquad.py first.", input_path)
            sys.exit(1)

    destination_blob = f"data/{input_path.name}"
    gcs_uri = f"gs://{args.bucket_name}/{destination_blob}"

    if not args.skip_upload:
        upload_to_gcs(input_path, args.bucket_name, destination_blob)

    try:
        op = trigger_import(
            project_id=args.project_id,
            location=args.location,
            datastore_id=args.datastore_id,
            gcs_uri=gcs_uri,
            reconciliation_mode=args.reconciliation_mode,
        )

        op_name = op.get("name")
        if op_name and args.poll:
            poll_operation(op_name, args.project_id)
        elif op_name:
            logger.info("Import started. Check operation status with:")
            logger.info("curl -H \"Authorization: Bearer $(gcloud auth print-access-token)\" -H \"X-Goog-User-Project: %s\" https://discoveryengine.googleapis.com/v1/%s", args.project_id, op_name)

    except Exception as e:
        logger.error("Document import could not be completed automatically: %s", e)
        logger.info(
            "\nTo trigger the import directly via gcloud:\n"
            "curl -X POST \\\n"
            "  -H \"Authorization: Bearer $(gcloud auth print-access-token)\" \\\n"
            "  -H \"Content-Type: application/json\" \\\n"
            "  -H \"X-Goog-User-Project: %s\" \\\n"
            "  \"https://discoveryengine.googleapis.com/v1/projects/%s/locations/%s/collections/default_collection/dataStores/%s/branches/default_branch/documents:import\" \\\n"
            "  -d '{\"gcsSource\": {\"inputUris\": [\"%s\"], \"dataSchema\": \"custom\"}, \"reconciliationMode\": \"%s\"}'\n",
            args.project_id,
            args.project_id,
            args.location,
            args.datastore_id,
            gcs_uri,
            args.reconciliation_mode,
        )


if __name__ == "__main__":
    main()
