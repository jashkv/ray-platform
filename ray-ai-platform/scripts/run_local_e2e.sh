#!/usr/bin/env bash
# ==============================================================================
# Master End-to-End Local Validation Script
# Runs full test suite, validates Terraform & K8s, and executes pipeline
# ==============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=================================================================="
echo "Master End-to-End Local Validation — Ray AI Platform"
echo "=================================================================="

echo "=== [1/7] Running Repository & Secret Pre-checks ==="
./scripts/validate_repo.sh

echo "=== [2/7] Running Terraform Formatting & Static Validation ==="
terraform fmt -check -recursive terraform/
LAYERS=("bootstrap" "network" "eks" "data" "platform")
for layer in "${LAYERS[@]}"; do
    echo "[*] Validating terraform/${layer}..."
    (cd "terraform/${layer}" && terraform validate)
done
echo "[+] All 5 Terraform layers validated successfully."

echo "=== [3/7] Validating Kubernetes & Helm Manifests ==="
./scripts/validate_k8s_manifests.sh

echo "=== [4/7] Generating Synthetic Datasets & Asserting Row Counts ==="
.venv/bin/python application/src/generate_datasets.py
S1_COUNT=$(wc -l < application/data/supply_chain_data_s1.csv | tr -d ' ')
S2_COUNT=$(wc -l < application/data/financial_data_s2.csv | tr -d ' ')
echo "[+] S1 Supply Chain Rows: ${S1_COUNT} (Header + 1200 records)"
echo "[+] S2 Financial Rows:    ${S2_COUNT} (Header + 1200 records)"
if [ "$S1_COUNT" -lt 1001 ] || [ "$S2_COUNT" -lt 1001 ]; then
    echo "[-] Dataset record count requirement failed (<1000 records)"
    exit 1
fi

echo "=== [5/7] Running Pytest Test Suite ==="
.venv/bin/pytest application/tests/ -v

echo "=== [6/7] Running End-to-End Ray AI Pipeline ==="
WAREHOUSE_DIR="/tmp/e2e_iceberg_warehouse"
rm -rf "$WAREHOUSE_DIR" application/models/*
.venv/bin/python application/src/ray_pipeline.py \
    --s1-input application/data/supply_chain_data_s1.csv \
    --s2-input application/data/financial_data_s2.csv \
    --output-model-dir application/models \
    --catalog-type sqlite \
    --warehouse-path "$WAREHOUSE_DIR"

echo "=== [7/7] Auditing Apache Iceberg Lakehouse Table ==="
.venv/bin/python scripts/verify_iceberg_table.py --warehouse-path "$WAREHOUSE_DIR"

echo "=================================================================="
echo "ALL END-TO-END VALIDATION GATES PASSED SUCCESSFULLY!"
echo "=================================================================="
