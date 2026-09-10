#!/usr/bin/env bash
# ==============================================================================
# MedQuAD Nightly Clinical Conversation Audit Pipeline Runner
# Can be executed via Linux crontab, systemd timer, or CI/CD workflow.
#
# Crontab setup example (runs at 00:00 UTC daily):
#   0 0 * * * /usr/local/google/home/asadpatel/Documents/capstone/scripts/run_nightly_audit.sh >> /usr/local/google/home/asadpatel/Documents/capstone/logs/audit_cron.log 2>&1
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

LOGS_DIR="${ROOT_DIR}/logs"
mkdir -p "${LOGS_DIR}"

TIMESTAMP="$(date -u +"%Y%m%d_%H%M%S")"
LOG_FILE="${LOGS_DIR}/nightly_audit_${TIMESTAMP}.log"

echo "========================================================================"
echo "🌙 [$(date -u +"%Y-%m-%d %H:%M:%S UTC")] Executing MedQuAD Nightly Audit Pipeline"
echo "========================================================================"

# Locate Python environment
PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
if [ ! -f "${PYTHON_BIN}" ]; then
  PYTHON_BIN="python3"
fi

# Execute automated conversation audit
"${PYTHON_BIN}" "${ROOT_DIR}/scripts/validate_conversations.py" --all --output-dir "${ROOT_DIR}/reports" 2>&1 | tee -a "${LOG_FILE}"

EXIT_CODE="${PIPESTATUS[0]}"

if [ "${EXIT_CODE}" -eq 0 ]; then
  echo "✅ Nightly clinical audit finished successfully. Log: ${LOG_FILE}"
else
  echo "⚠️ Nightly clinical audit flagged clinical violations or warnings. Exit code: ${EXIT_CODE}"
fi

exit "${EXIT_CODE}"
