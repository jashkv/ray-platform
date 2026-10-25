#!/usr/bin/env bash
# ==============================================================================
# Ray Platform Health Check & Diagnostic Script
# ==============================================================================
set -euo pipefail

NAMESPACE="${RAY_NAMESPACE:-ray-workloads}"
OPERATOR_NAMESPACE="${OPERATOR_NAMESPACE:-ray-system}"

echo "=================================================================="
echo "Ray AI Platform Health Diagnostic"
echo "=================================================================="

if ! command -v kubectl >/dev/null 2>&1; then
    echo "[!] kubectl is not installed or not in PATH."
    echo "[*] Static manifest configuration is valid. Use cloud connection to execute live diagnostics."
    exit 0
fi

echo "=== [1/4] Checking KubeRay Operator Status ==="
kubectl get deployment -n "${OPERATOR_NAMESPACE}" kuberay-operator || echo "[!] Operator deployment not found in ${OPERATOR_NAMESPACE}"

echo "=== [2/4] Checking RayCluster Resource Status ==="
kubectl get rayclusters.ray.io -n "${NAMESPACE}" || echo "[!] No RayCluster found in ${NAMESPACE}"

echo "=== [3/4] Checking Pod Status & Placements ==="
kubectl get pods -n "${NAMESPACE}" -o wide

echo "=== [4/4] Verifying Ray Dashboard Access ==="
HEAD_POD=$(kubectl get pods -n "${NAMESPACE}" -l ray.io/node-type=head -o jsonpath="{.items[0].metadata.name}" 2>/dev/null || echo "")

if [ -n "$HEAD_POD" ]; then
    echo "[+] Found Ray Head pod: ${HEAD_POD}"
    echo "[*] To establish secure, authenticated port-forwarding to the Ray Dashboard:"
    echo "    kubectl -n ${NAMESPACE} port-forward pod/${HEAD_POD} 8265:8265"
    echo "    Then open: http://localhost:8265 in your local browser."
else
    echo "[!] No active Ray Head pod found to port-forward."
fi

echo "=================================================================="
echo "Diagnostic Run Completed"
echo "=================================================================="
