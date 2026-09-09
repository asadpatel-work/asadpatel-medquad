#!/usr/bin/env python3
"""Setup Vertex AI Search DataStore (medquad-corpus-ds) and Search Engine (medquad-search-app-v1).

Creates the Discovery Engine DataStore, links it to the Search Engine,
and triggers the ingestion of the full 19,204 document corpus from GCS.
"""

import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("setup_datastore")

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "capstone-506616")
LOCATION = "global"
DATASTORE_ID = "medquad-corpus-ds"
ENGINE_ID = "medquad-search-app-v1"
BUCKET_NAME = f"{PROJECT_ID}-medquad-corpus"
GCS_JSONL_PATH = f"gs://{BUCKET_NAME}/data/full_medquad_documents.jsonl"


def get_token() -> str:
    """Attempts to obtain a valid Google Cloud bearer token."""
    try:
        res = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        token = res.stdout.strip()
        if token:
            return token
    except Exception as e:
        logger.debug("gcloud print-access-token failed: %s", e)

    try:
        import google.auth
        import google.auth.transport.requests

        credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)
        if credentials.token:
            return credentials.token
    except Exception as e:
        logger.error("google.auth.default refresh failed: %s", e)

    logger.error("Authentication required! Please run 'gcloud auth login' and try again.")
    sys.exit(1)


def main():
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": PROJECT_ID,
    }

    base_url = (
        f"https://discoveryengine.googleapis.com/v1/projects/{PROJECT_ID}"
        f"/locations/{LOCATION}/collections/default_collection"
    )

    # 1. Create or verify DataStore
    logger.info("[1/3] Checking / Creating DataStore '%s'...", DATASTORE_ID)
    ds_check_url = f"{base_url}/dataStores/{DATASTORE_ID}"
    r_check = requests.get(ds_check_url, headers=headers)

    if r_check.status_code == 200:
        logger.info("✔ DataStore '%s' already exists.", DATASTORE_ID)
    else:
        create_ds_url = f"{base_url}/dataStores?dataStoreId={DATASTORE_ID}"
        payload = {
            "displayName": "MedQuAD Grounding Corpus",
            "industryVertical": "GENERIC",
            "solutionTypes": ["SOLUTION_TYPE_SEARCH"],
            "contentConfig": "CONTENT_REQUIRED",
        }
        r_create = requests.post(create_ds_url, headers=headers, json=payload)
        if r_create.status_code in (200, 201):
            op = r_create.json()
            op_name = op.get("name")
            if op_name and not op.get("done"):
                logger.info("Provisioning DataStore operation: %s", op_name)
                while True:
                    time.sleep(3)
                    headers["Authorization"] = f"Bearer {get_token()}"
                    poll = requests.get(
                        f"https://discoveryengine.googleapis.com/v1/{op_name}", headers=headers
                    ).json()
                    if poll.get("done"):
                        logger.info("✔ DataStore '%s' successfully provisioned.", DATASTORE_ID)
                        break
                    logger.info("Waiting for DataStore creation...")
            else:
                logger.info("✔ DataStore '%s' created.", DATASTORE_ID)
        elif r_create.status_code == 409:
            logger.info("✔ DataStore '%s' already exists (HTTP 409).", DATASTORE_ID)
        else:
            logger.error("Failed to create DataStore: %d %s", r_create.status_code, r_create.text)
            sys.exit(1)

    # 2. Create or verify Search Engine / App
    logger.info("\n[2/3] Checking / Creating Search Engine '%s'...", ENGINE_ID)
    eng_check_url = f"{base_url}/engines/{ENGINE_ID}"
    headers["Authorization"] = f"Bearer {get_token()}"
    r_eng_check = requests.get(eng_check_url, headers=headers)

    if r_eng_check.status_code == 200:
        logger.info("✔ Search Engine '%s' already exists.", ENGINE_ID)
    else:
        create_eng_url = f"{base_url}/engines?engineId={ENGINE_ID}"
        eng_payload = {
            "displayName": "MedQuAD Search Engine",
            "dataStoreIds": [DATASTORE_ID],
            "solutionType": "SOLUTION_TYPE_SEARCH",
            "searchEngineConfig": {
                "searchTier": "SEARCH_TIER_STANDARD",
                "searchAddOns": ["SEARCH_ADD_ON_LLM"],
            },
        }
        r_eng = requests.post(create_eng_url, headers=headers, json=eng_payload)
        if r_eng.status_code in (200, 201):
            logger.info("✔ Search Engine '%s' created successfully.", ENGINE_ID)
        elif r_eng.status_code == 409:
            logger.info("✔ Search Engine '%s' already exists (HTTP 409).", ENGINE_ID)
        else:
            logger.warning(
                "Engine creation returned %d: %s. Continuing with DataStore direct import.",
                r_eng.status_code,
                r_eng.text,
            )

    # 3. Import full document corpus into DataStore
    logger.info("\n[3/3] Importing full MedQuAD documents from '%s'...", GCS_JSONL_PATH)
    import_url = f"{base_url}/dataStores/{DATASTORE_ID}/branches/default_branch/documents:import"
    import_payload = {
        "gcsSource": {
            "inputUris": [GCS_JSONL_PATH],
            "dataSchema": "custom",
        },
        "reconciliationMode": "INCREMENTAL",
    }
    headers["Authorization"] = f"Bearer {get_token()}"
    r_imp = requests.post(import_url, headers=headers, json=import_payload)

    if r_imp.status_code in (200, 201):
        op = r_imp.json()
        op_name = op.get("name")
        logger.info("Import operation started: %s", op_name)
        if op_name:
            logger.info("Polling import status (this processes ~19,204 chunks)...")
            start_poll = time.time()
            while time.time() - start_poll < 60:
                time.sleep(5)
                headers["Authorization"] = f"Bearer {get_token()}"
                poll = requests.get(
                    f"https://discoveryengine.googleapis.com/v1/{op_name}", headers=headers
                ).json()
                if poll.get("done"):
                    logger.info("🎉 Ingestion Complete! Response:\n%s", json.dumps(poll, indent=2))
                    return
                logger.info("Import in progress in Discovery Engine...")
            logger.info("Import is continuing asynchronously in Discovery Engine.")
    else:
        logger.error("Failed to start document import: %d %s", r_imp.status_code, r_imp.text)


if __name__ == "__main__":
    main()
