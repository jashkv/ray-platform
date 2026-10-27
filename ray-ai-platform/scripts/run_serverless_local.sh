#!/usr/bin/env bash
# ==============================================================================
# Local End-to-End Runner for AWS Serverless Alternative Pipeline
# Executes: Discovery -> Validation -> Entity Resolution -> Iceberg Sink -> ML Training -> Finalizer
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$PLATFORM_DIR"

# Colors for log output
CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${CYAN}[INFO]${NC} $1"; }
log_ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
log_err()  { echo -e "${RED}[ERROR]${NC} $1"; }

PYTHON_BIN="python3"
if [ -f ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
elif [ -f "../.venv/bin/python" ]; then
    PYTHON_BIN="../.venv/bin/python"
fi

echo "================================================================================"
echo "  AWS SERVERLESS ALTERNATIVE LOCAL VERIFICATION HARNESS"
echo "================================================================================"

# Gate 1: Check Input Datasets
log_info "Gate 1: Verifying Source CSV Datasets..."
if [ ! -f "application/data/supply_chain_data_s1.csv" ] || [ ! -f "application/data/financial_data_s2.csv" ]; then
    log_info "Generating synthetic datasets S1 & S2..."
    $PYTHON_BIN application/src/generate_datasets.py
fi
log_ok "Input datasets S1 and S2 present."

# Gate 2: Terraform Serverless Validation
log_info "Gate 2: Validating Terraform Serverless Layer..."
(
    cd terraform/serverless
    terraform validate > /dev/null
)
log_ok "Terraform serverless configuration is valid."

# Gate 3: Unit Tests for Serverless Handlers
log_info "Gate 3: Running Pytest Test Suite for Serverless Handlers..."
$PYTHON_BIN -m pytest application/tests/test_serverless_pipeline.py -v
log_ok "All serverless unit and integration tests passed."

# Gate 4: Full Pipeline Execution
log_info "Gate 4: Executing Full Local Serverless Pipeline..."
TMP_WH=$(mktemp -d /tmp/iceberg_serverless_wh_XXXXXX)
TMP_MOD=$(mktemp -d /tmp/serverless_models_XXXXXX)

trap 'rm -rf "$TMP_WH" "$TMP_MOD"' EXIT

$PYTHON_BIN -m application.src.serverless.serverless_pipeline \
    --s1-input application/data/supply_chain_data_s1.csv \
    --s2-input application/data/financial_data_s2.csv \
    --warehouse "$TMP_WH" \
    --model-dir "$TMP_MOD" \
    --catalog-type sqlite

log_ok "Serverless pipeline execution succeeded with verified R2 >= 0.85."
echo "================================================================================"
echo -e "${GREEN}  ALL SERVERLESS ALTERNATIVE GATES PASSED SUCCESSFULLY!${NC}"
echo "================================================================================"
