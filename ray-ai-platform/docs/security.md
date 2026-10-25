# Security Architecture & Controls — Ray AI Platform

## 1. Zero-Trust Principles
The platform enforces a strict Zero-Trust security model across infrastructure, Kubernetes, and application layers:
1. **No Static Credentials:** Long-lived AWS access keys are completely barred from Git, container images, environment variables, and Kubernetes secrets.
2. **Workload Identity (IRSA):** Ray pods assume an IAM role dynamically via STS Web Identity tokens signed by the EKS OIDC provider.
3. **Private Network Boundaries:** All worker compute, Ray pods, and Iceberg lakehouse interactions execute inside private subnets without public IP addresses.

---

## 2. IAM Roles for Service Accounts (IRSA)

The Ray pipeline ServiceAccount (`ray-pipeline-sa`) is bound to an IAM Role via OIDC federation:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/..."
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "oidc.eks.us-east-1.amazonaws.com/id/...:sub": "system:serviceaccount:ray-workloads:ray-pipeline-sa",
          "oidc.eks.us-east-1.amazonaws.com/id/...:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
```

### Least-Privilege Permissions Matrix
- **Amazon S3:** Scoped exclusively to `arn:aws:s3:::ray-platform-dev-data-*/*`.
- **AWS Glue:** Scoped to `corporate_data_db` and tables therein.
- **DynamoDB:** Scoped strictly to `ray-platform-dev-processing-ledger`.
- **AWS KMS:** Scoped to `arn:aws:kms:us-east-1:<ACCOUNT_ID>:key/<DATA_KEY_ID>`.

---

## 3. Ray Dashboard Access Control

> [!WARNING]
> Exposing the Ray Dashboard without authentication allows unauthenticated remote code execution on the Ray cluster.

### Access Control Measures Implemented:
1. **Default ClusterIP:** The Ray Head service `ray-cluster-head-svc` is provisioned strictly as an internal `ClusterIP` service (no public LoadBalancer).
2. **Authorized Port-Forwarding (Primary Operator Path):**
   ```bash
   kubectl -n ray-workloads port-forward service/ray-cluster-head-svc 8265:8265
   ```
3. **Internal Authenticated Ingress (Optional Production Path):**
   - Ingress class: `alb` with `scheme: internal` (private to VPC/VPN).
   - Enforces OAuth2 / Cognito OIDC user pool authentication before requests reach the Ray dashboard (`alb.ingress.kubernetes.io/auth-type: cognito`).

---

## 4. Encryption & Data Protection
- **Encryption at Rest:** All S3 buckets (Terraform state, data lakehouse), DynamoDB tables, and EKS Kubernetes Secrets are encrypted with Customer Managed KMS Keys (CMKs) with annual key rotation enabled.
- **Encryption in Transit:** S3 bucket policies explicitly deny non-TLS requests (`Condition: {"aws:SecureTransport": "false"}`). Ray inter-node traffic travels within the private VPC.

---

## 5. Container & Runtime Hardening
- Container runs as non-root user `ray` (UID 1000).
- Root filesystem is read-only where feasible; ephemeral storage uses memory-backed emptyDir volumes.
- Dockerfile pinned with exact versions to ensure build reproducibility and prevent supply-chain package substitution.
