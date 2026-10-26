# Troubleshooting & Operational Runbook — Ray AI Platform

## 1. Quick Diagnostic Checklist
When diagnosing an issue with the cluster or pipeline, run the diagnostic script:
```bash
./scripts/check_ray_health.sh
```

---

## 2. Common Operational Failure Modes & Remediation

### Failure 1: Ray Worker Pod OOMKilled / CrashLoopBackOff
- **Symptoms:** Ray worker pod restarts with `ExitCode 137` (OOMKilled).
- **Root Cause:** In-memory object store or shared memory (`/dev/shm`) exceeded pod limits.
- **Remediation:**
  1. Inspect pod memory usage:
     ```bash
     kubectl describe pod -l app.kubernetes.io/name=ray-worker -n ray-workloads
     ```
  2. Verify `/dev/shm` size limit in `kubernetes/ray/ray-cluster.yaml`:
     ```yaml
     volumes:
       - name: dshm
         emptyDir:
           medium: Memory
           sizeLimit: 4Gi
     ```
  3. Ensure `--object-store-memory` does not exceed $35\%$ of total pod memory limit.

---

### Failure 2: `EntityResolver` Actor Placement Pending / Unschedulable
- **Symptoms:** RayJob logs show `Actor ray.remote(resources={'entity_resolver_slot': 1}) is waiting for resources`.
- **Root Cause:** No worker node is advertising the `entity_resolver_slot` custom resource, or worker pods cannot tolerate the worker node taint.
- **Remediation:**
  1. Check worker Raylet start parameters:
     ```bash
     kubectl logs -l app.kubernetes.io/name=ray-worker -n ray-workloads | grep "resources"
     ```
  2. Verify the worker group spec in `kubernetes/ray/ray-cluster.yaml` has:
     ```yaml
     rayStartParams:
       resources: '{"entity_resolver_slot": 1}'
     ```
  3. Verify node tolerations match the EKS node group taint:
     ```yaml
     tolerations:
       - key: "workload-role"
         value: "ray-worker"
         operator: "Equal"
         effect: "NoSchedule"
     ```

---

### Failure 3: Spot Worker Interruption
- **Symptoms:** Node is terminated by AWS EC2 Spot market conditions; worker pod terminates abruptly.
- **Observed Behavior:**
  - Ray GCS detects worker heartbeat timeout after 30 seconds.
  - Ray Data automatically re-executes interrupted block tasks using lineage reconstruction.
  - EKS autoscaler replaces the worker node using another instance type from the diversified pool (`m6i`, `m5`, `m5a`, `m6a`).
- **Remediation:** No manual action required. If Spot capacity across all 4 instance families in an AZ is exhausted, the Priority Expander scales the `worker-ondemand-fallback` node group.

---

### Failure 4: Apache Iceberg Commit Failure / Schema Mismatch
- **Symptoms:** `ValueError: Mismatch in fields` or `CommitFailedException`.
- **Root Cause:** Incoming Arrow table schema does not match the Iceberg table definition in `corporate_registry`.
- **Remediation:**
  1. Run the Iceberg table inspector:
     ```bash
     ./scripts/verify_iceberg_table.py --warehouse-path /tmp/iceberg_warehouse
     ```
  2. Ensure timestamps use `pa.timestamp("us", tz="UTC")` matching `TimestamptzType()`.
  3. Inspect conflicting commit snapshots in the Glue Console or SQLite database.

---

### Failure 5: IRSA Access Denied (AWS S3 / Glue 403 Forbidden)
- **Symptoms:** `botocore.exceptions.ClientError: An error occurred (AccessDenied) when calling the PutObject operation`.
- **Remediation:**
  1. Verify the ServiceAccount annotation:
     ```bash
     kubectl get sa ray-pipeline-sa -n ray-workloads -o yaml
     ```
     Must contain `eks.amazonaws.com/role-arn: arn:aws:iam::<ACCOUNT_ID>:role/ray-platform-test-ray-pipeline-irsa`.
  2. Verify the projected token mount inside the pod:
     ```bash
     kubectl exec -it <pod-name> -n ray-workloads -- env | grep AWS_
     ```
     `AWS_ROLE_ARN` and `AWS_WEB_IDENTITY_TOKEN_FILE` must be present.
