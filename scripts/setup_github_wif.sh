#!/usr/bin/env bash
# ==============================================================================
# Setup Google Cloud Workload Identity Federation for GitHub Actions
# ==============================================================================
# Configures keyless OIDC authentication between GitHub Actions and GCP.
# ==============================================================================

set -euo pipefail

# ANSI colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-capstone-506616}"
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")
GITHUB_REPO="${1:-asadpatel-work/asadpatel-medquad}"
POOL_NAME="github-actions-pool"
PROVIDER_NAME="github-actions-provider"
SA_NAME="sa-github-actions"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo -e "${BLUE}====================================================================${NC}"
echo -e "${BLUE}   Configuring GitHub Actions Workload Identity Federation (WIF)    ${NC}"
echo -e "${BLUE}====================================================================${NC}"
echo -e "Project ID:      ${PROJECT_ID} (${PROJECT_NUMBER})"
echo -e "GitHub Repo:     ${GITHUB_REPO}"
echo -e "Service Account: ${SA_EMAIL}"
echo ""

# 1. Enable Required APIs
echo -e "${BLUE}[1/5] Enabling IAM Credentials & Security APIs...${NC}"
gcloud services enable \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  cloudresourcemanager.googleapis.com \
  sts.googleapis.com \
  artifactregistry.googleapis.com \
  run.googleapis.com \
  --project="${PROJECT_ID}"
echo -e "${GREEN}✔ APIs enabled.${NC}"

# 2. Create Service Account for GitHub Actions
echo -e "\n${BLUE}[2/5] Setting up GitHub Actions Service Account...${NC}"
if ! gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${SA_NAME}" \
    --display-name="GitHub Actions Deployer" \
    --description="Used by GitHub Actions CI/CD to build, push images, and deploy Cloud Run services" \
    --project="${PROJECT_ID}"
  echo -e "${GREEN}✔ Created service account: ${SA_EMAIL}${NC}"
else
  echo -e "${YELLOW}Notice: Service account ${SA_EMAIL} already exists.${NC}"
fi

# 3. Grant Required Roles to Service Account
echo -e "\n${BLUE}[3/5] Assigning IAM Roles...${NC}"
ROLES=(
  "roles/artifactregistry.writer"
  "roles/run.developer"
  "roles/iam.serviceAccountUser"
)

for ROLE in "${ROLES[@]}"; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="${ROLE}" \
    --condition=None \
    --quiet >/dev/null
  echo -e "  ✔ Granted ${ROLE}"
done

# 4. Create Workload Identity Pool and Provider
echo -e "\n${BLUE}[4/5] Provisioning Workload Identity Pool and OIDC Provider...${NC}"
if ! gcloud iam workload-identity-pools describe "${POOL_NAME}" --location="global" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools create "${POOL_NAME}" \
    --location="global" \
    --display-name="GitHub Actions Identity Pool" \
    --description="Identity pool for GitHub Actions OIDC tokens" \
    --project="${PROJECT_ID}"
  echo -e "${GREEN}✔ Created pool: ${POOL_NAME}${NC}"
fi

if ! gcloud iam workload-identity-pools providers describe "${PROVIDER_NAME}" --workload-identity-pool="${POOL_NAME}" --location="global" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools providers create-oidc "${PROVIDER_NAME}" \
    --workload-identity-pool="${POOL_NAME}" \
    --location="global" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
    --attribute-condition="assertion.repository == '${GITHUB_REPO}'" \
    --project="${PROJECT_ID}"
  echo -e "${GREEN}✔ Created OIDC provider: ${PROVIDER_NAME}${NC}"
fi

# 5. Bind GitHub Repository to Service Account
echo -e "\n${BLUE}[5/5] Authorizing GitHub Repository for Service Account Impersonation...${NC}"
PRINCIPAL="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}/attribute.repository/${GITHUB_REPO}"

BIND_SUCCESS=false
for i in {1..6}; do
  if gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
    --project="${PROJECT_ID}" \
    --role="roles/iam.workloadIdentityUser" \
    --member="${PRINCIPAL}" \
    --quiet >/dev/null 2>&1; then
    BIND_SUCCESS=true
    break
  fi
  echo "Waiting for service account IAM propagation across GCP cells (attempt $i/6)..."
  sleep 5
done

if [[ "$BIND_SUCCESS" != "true" ]]; then
  echo -e "${RED}Failed to bind workloadIdentityUser after 30s. Please retry.${NC}"
  exit 1
fi
echo -e "${GREEN}✔ Bound ${GITHUB_REPO} to ${SA_EMAIL}.${NC}"

# Output Config
WIF_PROVIDER_ID="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}/providers/${PROVIDER_NAME}"

echo -e "\n${GREEN}====================================================================${NC}"
echo -e "${GREEN}       ✔ Workload Identity Federation Configured Successfully!       ${NC}"
echo -e "${GREEN}====================================================================${NC}"
echo -e "Please configure the following Secrets in your GitHub Repository settings:"
echo -e "URL: https://github.com/${GITHUB_REPO}/settings/secrets/actions"
echo ""
echo -e "  Secret: ${BLUE}GCP_WIF_PROVIDER${NC}"
echo -e "  Value:  ${WIF_PROVIDER_ID}"
echo ""
echo -e "  Secret: ${BLUE}GCP_WIF_SERVICE_ACCOUNT${NC}"
echo -e "  Value:  ${SA_EMAIL}"
echo ""
echo -e "${YELLOW}Option B (Fallback): If you prefer using a static JSON key instead:${NC}"
echo -e "  gcloud iam service-accounts keys create sa-key.json --iam-account=${SA_EMAIL}"
echo -e "  Paste contents of sa-key.json into GitHub Secret: ${BLUE}GCP_SA_KEY${NC}"
echo -e "${GREEN}====================================================================${NC}"
