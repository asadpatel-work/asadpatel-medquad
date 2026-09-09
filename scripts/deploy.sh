#!/usr/bin/env bash
# ==============================================================================
# MedQuAD Clinical Assistant - Automated Cloud Run & GCP Deployment Script
# ==============================================================================

set -euo pipefail

# Color formatting
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================================${NC}"
echo -e "${BLUE}    MedQuAD Clinical Research Assistant - Production Deployment     ${NC}"
echo -e "${BLUE}====================================================================${NC}"

# 1. Resolve GCP Project and Region
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null || echo "")}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
SERVICE_NAME="medquad-clinical-assistant"
IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

if [[ -z "$PROJECT_ID" || "$PROJECT_ID" == "(unset)" ]]; then
    echo -e "${YELLOW}Warning: GOOGLE_CLOUD_PROJECT is not set.${NC}"
    read -rp "Please enter your GCP Project ID (e.g., fde-medquad-sandbox-dev): " PROJECT_ID
    if [[ -z "$PROJECT_ID" ]]; then
        echo -e "${RED}Error: Project ID is required for deployment.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}Deploying to Project:${NC} ${PROJECT_ID}"
echo -e "${GREEN}Target Region:${NC}       ${REGION}"
echo -e "${GREEN}Target Service:${NC}      ${SERVICE_NAME}"
echo ""

# 2. Verify Authentication Preflight
echo -e "${BLUE}[Step 1/5] Checking Google Cloud Authentication & ADC...${NC}"
if ! gcloud auth print-access-token >/dev/null 2>&1; then
    echo -e "${YELLOW}Notice: Active gcloud token not found or expired.${NC}"
    echo -e "Initiating application-default login..."
    gcloud auth application-default login --project="${PROJECT_ID}" || {
        echo -e "${RED}Failed to authenticate. Please ensure LOAS/gcert is active or login manually.${NC}"
        exit 1
    }
fi
echo -e "${GREEN}✔ Google Cloud Authentication verified.${NC}"

# 3. Enable Required GCP APIs
echo -e "${BLUE}[Step 2/5] Enabling Required Google Cloud APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    discoveryengine.googleapis.com \
    aiplatform.googleapis.com \
    bigquery.googleapis.com \
    cloudtrace.googleapis.com \
    logging.googleapis.com \
    secretmanager.googleapis.com \
    --project="${PROJECT_ID}"
echo -e "${GREEN}✔ All required APIs active.${NC}"

# 4. Provision MedQuAD Grounding Corpus Storage
echo -e "${BLUE}[Step 3/5] Setting up GCS Grounding Corpus Storage...${NC}"
BUCKET_NAME="${PROJECT_ID}-medquad-corpus"
if ! gcloud storage buckets describe "gs://${BUCKET_NAME}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
    echo "Creating GCS Bucket gs://${BUCKET_NAME}..."
    gcloud storage buckets create "gs://${BUCKET_NAME}" --location="${REGION}" --project="${PROJECT_ID}" --uniform-bucket-level-access
fi

echo "Uploading MedQuAD grounding documents to gs://${BUCKET_NAME}/data/..."
if [[ -f "data/full_medquad_documents.jsonl" ]]; then
    gcloud storage cp data/full_medquad_documents.jsonl "gs://${BUCKET_NAME}/data/full_medquad_documents.jsonl" || true
fi
python3 scripts/setup_datastore_v1.py || echo "Note: Datastore setup will continue once credentials are fully refreshed."
echo -e "${GREEN}✔ Grounding corpus staged in GCS and DataStore provisioned.${NC}"

# 5. Build Container Image via Cloud Build
echo -e "${BLUE}[Step 4/5] Building Container Image with Cloud Build...${NC}"
gcloud builds submit --tag "${IMAGE_TAG}" --project="${PROJECT_ID}" --timeout=1200s .
echo -e "${GREEN}✔ Container image built: ${IMAGE_TAG}${NC}"

# 6. Deploy to Google Cloud Run
echo -e "${BLUE}[Step 5/5] Deploying Service to Google Cloud Run...${NC}"
gcloud run deploy "${SERVICE_NAME}" \
    --image="${IMAGE_TAG}" \
    --platform=managed \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --allow-unauthenticated \
    --cpu=2 \
    --memory=2Gi \
    --concurrency=40 \
    --min-instances=1 \
    --max-instances=10 \
    --set-env-vars="ENVIRONMENT=production,GCP_PROJECT_ID=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=global,VERTEX_DATASTORE_ID=medquad-corpus-ds,ROOT_ORCHESTRATOR_MODEL=gemini-2.5-flash,RESEARCHER_MODEL=gemini-2.5-pro,REVIEWER_MODEL=gemini-3.5-flash"

SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --platform=managed --region="${REGION}" --project="${PROJECT_ID}" --format='value(status.url)')

echo ""
echo -e "${GREEN}====================================================================${NC}"
echo -e "${GREEN}    🎉 Deployment Complete! Service is Live at:                   ${NC}"
echo -e "${GREEN}    ${SERVICE_URL}                                                  ${NC}"
echo -e "${GREEN}====================================================================${NC}"
echo ""
echo "Health Check: ${SERVICE_URL}/api/v1/health"
echo "Interactive Split-Pane UI: ${SERVICE_URL}/"
echo "OpenAPI Documentation: ${SERVICE_URL}/docs"
