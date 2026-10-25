#!/usr/bin/env bash
# ==============================================================================
# Kubernetes Manifests & CRD Static Validation Script
# ==============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== [1/2] Verifying YAML Syntax Across Kubernetes Manifests ==="
.venv/bin/python3 -c "
import yaml
import glob
import sys

manifest_files = glob.glob('kubernetes/**/*.yaml', recursive=True) + glob.glob('helm/**/*.yaml', recursive=True)
if not manifest_files:
    print('[-] No YAML manifests found!')
    sys.exit(1)

for path in manifest_files:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            docs = list(yaml.safe_load_all(f))
            assert len(docs) > 0, 'Empty document'
            for doc in docs:
                if doc is None:
                    continue
                assert 'apiVersion' in doc or 'image' in doc, 'Invalid Kubernetes or Helm manifest structure'
            print(f'[+] Valid YAML: {path} ({len(docs)} documents)')
    except Exception as e:
        print(f'[-] Invalid YAML in {path}: {e}')
        sys.exit(1)
"
echo "[+] All Kubernetes manifests passed YAML syntax validation."

echo "=== [2/2] Validating Sizing, /dev/shm, and Scheduling Constraints ==="
.venv/bin/python3 -c "
import yaml

with open('kubernetes/ray/ray-cluster.yaml', 'r') as f:
    cluster = yaml.safe_load(f)

# 1. Verify Head Group
head = cluster['spec']['headGroupSpec']
assert head['template']['spec']['nodeSelector']['workload-role'] == 'ray-head-system', 'Head nodeSelector must be ray-head-system'
assert head['rayStartParams']['num-cpus'] == '0', 'Head must advertise num-cpus=0'

# 2. Verify Worker Group
worker = cluster['spec']['workerGroupSpecs'][0]
assert worker['template']['spec']['nodeSelector']['workload-role'] == 'ray-worker', 'Worker nodeSelector must be ray-worker'

# Verify /dev/shm volume
volumes = {v['name']: v for v in worker['template']['spec']['volumes']}
assert 'dshm' in volumes, 'Worker missing dshm volume'
assert volumes['dshm']['emptyDir']['medium'] == 'Memory', '/dev/shm must be Memory-backed'

# Verify Custom Resource for EntityResolver
start_params = worker['rayStartParams']
assert 'entity_resolver_slot' in start_params['resources'], 'Worker must advertise entity_resolver_slot'
assert 'object-store-memory' in start_params, 'Worker must configure object-store-memory'

print('[+] Head/Worker nodeSelectors verified.')
print('[+] /dev/shm memory mount verified.')
print('[+] entity_resolver_slot custom resource verified.')
"

echo "=== Kubernetes Manifest Validation Succeeded ==="
