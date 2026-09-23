#!/usr/bin/env bash
# ==============================================================================
# MedQuAD Local CI Pre-flight Verification Script
# ==============================================================================
# Mirrors GitHub Actions CI pipeline on local developer workstation.
# Usage:
#   ./scripts/run_ci_local.sh [--with-docker]
# ==============================================================================

set -euo pipefail

# ANSI colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

WITH_DOCKER=false
if [[ "${1:-}" == "--with-docker" ]]; then
  WITH_DOCKER=true
fi

echo -e "${BLUE}====================================================================${NC}"
echo -e "${BLUE}       MedQuAD Clinical Research Assistant - Local CI Suite         ${NC}"
echo -e "${BLUE}====================================================================${NC}"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

VENV_PYTHON="${PROJECT_ROOT}/.venv/bin/python"
VENV_RUFF="${PROJECT_ROOT}/.venv/bin/ruff"
VENV_PYTEST="${PROJECT_ROOT}/.venv/bin/pytest"

if [[ ! -x "${VENV_PYTHON}" ]]; then
  echo -e "${RED}Error: Local virtual environment not found at .venv/${NC}"
  echo "Please set up .venv first: uv venv && uv pip install -e '.[dev]'"
  exit 1
fi

# Step 1: Ruff Lint Check
echo -e "\n${BLUE}[1/4] Running Ruff Static Analysis & Linting...${NC}"
"${VENV_RUFF}" check backend/ tests/
echo -e "${GREEN}✔ Ruff lint checks passed!${NC}"

# Step 2: Ruff Format Check
echo -e "\n${BLUE}[2/4] Verifying Code Formatting...${NC}"
"${VENV_RUFF}" format --check backend/ tests/
echo -e "${GREEN}✔ Code formatting verified!${NC}"

# Step 3: Pytest Suite with Coverage
echo -e "\n${BLUE}[3/4] Running Unit & Guardrail Test Suite...${NC}"
ENVIRONMENT=test \
GCP_PROJECT_ID=capstone-506616 \
USE_MOCK_SEARCH=true \
ENABLE_IAP=false \
"${VENV_PYTEST}" tests/unit/ \
  --cov=backend \
  --cov-report=term-missing:skip-covered \
  -q
echo -e "${GREEN}✔ All unit and guardrail tests passed!${NC}"

# Step 4: Optional Docker Build & Health Validation
if [[ "${WITH_DOCKER}" == "true" ]]; then
  echo -e "\n${BLUE}[4/4] Validating Docker Container Build & Boot...${NC}"
  if command -v docker >/dev/null 2>&1; then
    docker build -t medquad-local-test:ci -f Dockerfile .
    CONTAINER_ID=$(docker run -d -p 8000:8000 \
      -e ENVIRONMENT=development \
      -e GCP_PROJECT_ID=capstone-506616 \
      -e USE_MOCK_SEARCH=true \
      -e ENABLE_IAP=false \
      medquad-local-test:ci)
    
    echo "Awaiting container readiness..."
    READY=false
    for i in {1..15}; do
      if curl -s -f http://localhost:8000/api/v1/health >/dev/null 2>&1; then
        READY=true
        break
      fi
      sleep 2
    done

    docker stop "${CONTAINER_ID}" >/dev/null
    docker rm "${CONTAINER_ID}" >/dev/null

    if [[ "${READY}" == "true" ]]; then
      echo -e "${GREEN}✔ Docker container build & healthcheck passed!${NC}"
    else
      echo -e "${RED}✖ Docker container healthcheck failed!${NC}"
      exit 1
    fi
  else
    echo -e "${YELLOW}Notice: Docker CLI not found; skipping container build step.${NC}"
  fi
else
  echo -e "\n${BLUE}[4/4] Skipping Docker build (pass --with-docker to enable).${NC}"
fi

echo -e "\n${GREEN}====================================================================${NC}"
echo -e "${GREEN}  ✔ All CI pre-flight checks passed! Ready to push to GitHub.       ${NC}"
echo -e "${GREEN}====================================================================${NC}"
