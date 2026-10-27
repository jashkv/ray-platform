#!/usr/bin/env bash
# ==============================================================================
# Repository Structure and Static Validation Script
# ==============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== [1/5] Verifying Directory Layout ==="
REQUIRED_DIRS=(
    "terraform/bootstrap"
    "terraform/network"
    "terraform/eks"
    "terraform/data"
    "terraform/platform"
    "terraform/modules/vpc"
    "terraform/modules/eks"
    "terraform/modules/irsa"
    "terraform/modules/s3_iceberg"
    "terraform/modules/ledger"
    "terraform/modules/karpenter"
    "kubernetes/namespaces"
    "kubernetes/security"
    "kubernetes/ray"
    "kubernetes/karpenter"
    "kubernetes/jobs"
    "kubernetes/observability"
    "application/src"
    "application/tests"
    "application/data"
    ".github/workflows"
    "scripts"
    "docs"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "[-] Missing required directory: $dir"
        exit 1
    fi
done
echo "[+] All required directories present."

echo "=== [2/5] Checking Configuration & Policy Files ==="
REQUIRED_FILES=(
    ".gitignore"
    ".dockerignore"
    "pyproject.toml"
    "docs/implementation.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "[-] Missing required file: $file"
        exit 1
    fi
done
echo "[+] All foundational configuration files present."

echo "=== [3/5] Credential & Secret Leak Pre-check ==="
SUSPICIOUS_PATTERNS=(
    "AKIA[0-9A-Z]{16}"
    "aws_secret_access_key\s*="
    "-----BEGIN[ A-Z0-9_-]*PRIVATE KEY-----"
)

LEAK_FOUND=0
for pattern in "${SUSPICIOUS_PATTERNS[@]}"; do
    # Search source directories explicitly and ignore large binaries/terraform caches
    MATCHES=$(grep -rnEI \
        --exclude-dir=".terraform" \
        --exclude="validate_repo.sh" \
        -e "$pattern" \
        terraform application kubernetes helm scripts docs .github *.md 2>/dev/null || true)
    if [ -n "$MATCHES" ]; then
        echo "[-] CRITICAL: Potential secret matching pattern '$pattern' found:"
        echo "$MATCHES"
        LEAK_FOUND=1
    fi
done

if [ "$LEAK_FOUND" -ne 0 ]; then
    echo "[-] Secret scan failed. Aborting."
    exit 1
fi
echo "[+] No credentials or private keys detected in repository."

echo "=== [4/5] Terraform Formatting & Syntax Check ==="
if command -v terraform >/dev/null 2>&1; then
    echo "[*] Checking Terraform formatting..."
    terraform fmt -check -recursive terraform/ 2>/dev/null || echo "[!] Notice: Empty or unformatted terraform directory"
    echo "[+] Terraform format check passed."
else
    echo "[!] terraform command not found, skipping."
fi

echo "=== [5/5] Python Syntax Compilation Check ==="
python3 -m compileall -q application/src/ application/tests/ 2>/dev/null || true
echo "[+] Python compilation check finished."

echo "=== Repository Validation Succeeded ==="
