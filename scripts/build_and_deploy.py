#!/usr/bin/env python3
"""Build container image via Cloud Build REST API, then update Cloud Run."""

import io
import os
import subprocess
import sys
import tarfile
import time
from pathlib import Path

import requests

PROJECT_ID = "capstone-506616"
REGION = "us-central1"
BUCKET_NAME = f"{PROJECT_ID}-medquad-corpus"
IMAGE_TAG = f"{REGION}-docker.pkg.dev/{PROJECT_ID}/medquad/medquad-backend:latest"
SERVICE_NAME = "medquad-backend"

def get_token():
    try:
        return subprocess.check_output(["gcloud", "auth", "application-default", "print-access-token"], text=True).strip()
    except Exception:
        pass
    try:
        return subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()
    except Exception:
        pass
    import google.auth
    import google.auth.transport.requests
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    req = google.auth.transport.requests.Request()
    creds.refresh(req)
    return creds.token



print(f"=== Starting Cloud Build & Deployment for {PROJECT_ID} ===")

token = get_token()
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "X-Goog-User-Project": PROJECT_ID,
}

# 1. Package source code into in-memory tarball
print("[1/4] Archiving project sources...")
tar_stream = io.BytesIO()
with tarfile.open(fileobj=tar_stream, mode="w:gz") as tar:
    capstone_dir = Path("/usr/local/google/home/asadpatel/Documents/capstone")
    for root, dirs, files in os.walk(capstone_dir):
        dirs[:] = [
            d for d in dirs
            if d not in [
                ".git", "__pycache__", ".venv", "node_modules",
                ".terraform", ".pytest_cache", ".ruff_cache", "medquad_raw"
            ]
        ]
        for file in files:
            if file.endswith((".pyc", ".tar.gz", ".jsonl")):
                continue
            full_path = Path(root) / file
            rel_path = full_path.relative_to(capstone_dir)
            tar.add(full_path, arcname=str(rel_path))

tar_stream.seek(0)
tar_bytes = tar_stream.getvalue()
print(f"✔ Archive created ({len(tar_bytes) / (1024 * 1024):.2f} MB)")

# 2. Upload source archive to GCS via google-cloud-storage
print(f"[2/4] Uploading source archive to gs://{BUCKET_NAME}/builds/source.tar.gz...")
try:
    from google.cloud import storage
    gcs_client = storage.Client(project=PROJECT_ID)
    bucket = gcs_client.bucket(BUCKET_NAME)
    blob = bucket.blob("builds/source.tar.gz")
    blob.upload_from_string(tar_bytes, content_type="application/gzip")
except Exception:
    archive_file = "/tmp/source.tar.gz"
    with open(archive_file, "wb") as f:
        f.write(tar_bytes)
    subprocess.run(["gcloud", "storage", "cp", archive_file, f"gs://{BUCKET_NAME}/builds/source.tar.gz"], check=True)
    os.remove(archive_file)
print("✔ Source uploaded to GCS.")

# 3. Submit Cloud Build
print("[3/4] Submitting Cloud Build request...")
build_payload = {
    "source": {"storageSource": {"bucket": BUCKET_NAME, "object": "builds/source.tar.gz"}},
    "steps": [
        {
            "name": "gcr.io/cloud-builders/docker",
            "args": ["build", "-t", IMAGE_TAG, "-f", "Dockerfile", "."],
        }
    ],
    "images": [IMAGE_TAG],
    "timeout": "1200s",
    "options": {"logging": "LEGACY"},
}

headers["Authorization"] = f"Bearer {get_token()}"
submit_url = f"https://cloudbuild.googleapis.com/v1/projects/{PROJECT_ID}/builds"
resp = requests.post(submit_url, headers=headers, json=build_payload)
if resp.status_code not in (200, 201):
    print(f"Error submitting build: {resp.status_code} {resp.text}")
    sys.exit(1)

build_data = resp.json()
build_id = build_data.get("metadata", {}).get("build", {}).get("id") or build_data.get("id")
print(f"✔ Build submitted! Build ID: {build_id}")

# 4. Poll Build Status
print("Waiting for container image build to complete...")
poll_url = f"https://cloudbuild.googleapis.com/v1/projects/{PROJECT_ID}/builds/{build_id}"

while True:
    time.sleep(8)
    headers["Authorization"] = f"Bearer {get_token()}"
    poll_resp = requests.get(poll_url, headers=headers)
    if poll_resp.status_code != 200:
        print(f"Warning: polling failed {poll_resp.status_code}")
        continue

    status_data = poll_resp.json()
    status = status_data.get("status")
    print(f"Build status: {status}...")

    if status == "SUCCESS":
        print(f"🎉 Cloud Build Succeeded! Image pushed to {IMAGE_TAG}")
        break
    elif status in ("FAILURE", "INTERNAL_ERROR", "TIMEOUT", "CANCELLED"):
        print(f"❌ Cloud Build failed with status {status}: {status_data.get('statusDetail')}")
        sys.exit(1)

# 5. Deploy New Revision to Cloud Run with updated env vars
print(f"[4/4] Deploying new revision to Cloud Run service '{SERVICE_NAME}'...")

get_url = f"https://run.googleapis.com/v2/projects/{PROJECT_ID}/locations/{REGION}/services/{SERVICE_NAME}"
headers["Authorization"] = f"Bearer {get_token()}"
resp = requests.get(get_url, headers=headers)
if resp.status_code != 200:
    print(f"Failed to fetch Cloud Run service: {resp.status_code} {resp.text}")
    sys.exit(1)

service_def = resp.json()
template = service_def.get("template", {})
annotations = template.get("annotations", {})
annotations["client.knative.dev/user-image"] = IMAGE_TAG
annotations["run.googleapis.com/client-name"] = "build_and_deploy"
annotations["client.knative.dev/nonce"] = str(int(time.time()))
template["annotations"] = annotations

if "containers" in template and len(template["containers"]) > 0:
    container = template["containers"][0]
    container["image"] = IMAGE_TAG
    # Update environment variables
    env_vars = {
        "ENVIRONMENT": "production",
        "GCP_PROJECT_ID": PROJECT_ID,
        "USE_MOCK_SEARCH": "false",
        "VERTEX_AI_SEARCH_DATASTORE_ID": "medquad-corpus-v1",
        "VERTEX_DATASTORE_ID": "medquad-corpus-v1",
        "VERTEX_AI_SEARCH_ENGINE_ID": "medquad-search-app-v2",
        "MEDQUAD_CORPUS_PATH": "data/full_medquad.json",
        "BIGQUERY_TELEMETRY_TABLE": f"{PROJECT_ID}.telemetry.agent_metrics",
        "ROOT_ORCHESTRATOR_MODEL": "gemini-2.5-flash",
        "RESEARCHER_MODEL": "gemini-2.5-pro",
        "REVIEWER_MODEL": "gemini-3.5-flash",
    }
    container["env"] = [{"name": k, "value": v} for k, v in env_vars.items()]

if "revision" in template:
    del template["revision"]

patch_url = f"https://run.googleapis.com/v2/projects/{PROJECT_ID}/locations/{REGION}/services/{SERVICE_NAME}?updateMask=template"
headers["Authorization"] = f"Bearer {get_token()}"
patch_resp = requests.patch(patch_url, headers=headers, json={"template": template})
if patch_resp.status_code not in (200, 201):
    print(f"Failed to patch Cloud Run service: {patch_resp.status_code} {patch_resp.text}")
    sys.exit(1)

op = patch_resp.json()
op_name = op.get("name")
if op_name:
    print("Waiting for Cloud Run revision rollout...")
    op_url = f"https://run.googleapis.com/v2/{op_name}"
    while True:
        time.sleep(4)
        headers["Authorization"] = f"Bearer {get_token()}"
        op_check = requests.get(op_url, headers=headers).json()
        if op_check.get("done"):
            latest_rev = op_check.get("response", {}).get("latestReadyRevision")
            print(f"🚀 Deployment successful! New ready revision: {latest_rev}")
            service_url = op_check.get("response", {}).get("uri")
            print(f"🔗 Live Service URL: {service_url}")
            break
        print("Rolling out revision...")
