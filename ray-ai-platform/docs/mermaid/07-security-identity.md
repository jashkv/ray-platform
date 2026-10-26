# 07 — Zero-Trust Security, Identity & Cryptographic Architecture

This document presents the **Zero-Trust Security, Identity Federation, and Encryption Architecture** protecting compute workloads, persistent storage, and access boundaries.

---

## Security Architecture Diagram

```mermaid
flowchart TD
    %% Zero Trust Security, Workload Identity & Cryptographic Architecture
    subgraph Identity_Providers["Identity & Authentication Providers"]
        AWS_IAM["AWS Identity & Access Management (IAM)"]
        OIDC_EKS["EKS IAM OpenID Connect (OIDC) Provider\noidc.eks.us-east-1.amazonaws.com/id/..."]
        GHA_OIDC["GitHub Actions OIDC Provider\ntoken.actions.githubusercontent.com"]
    end

    subgraph EKS_Auth["EKS Modern Authentication Engine"]
        ACCESS_ENTRY["EKS Access Entries (v1.30+)\n- Zero aws-auth ConfigMap\n- Principal: karpenter-node-role\n- Type: EC2_LINUX"]
        K8S_RBAC["Kubernetes RBAC (ClusterRole / RoleBinding)\n- Principle of Least Privilege\n- Namespace Scoped: ray-system"]
    end

    subgraph ServiceAccounts["Kubernetes ServiceAccounts (IRSA Bound)"]
        SA_RAY["ServiceAccount: ray-pipeline-sa\nannotation: eks.amazonaws.com/role-arn = ray-workload-role"]
        SA_KARP["ServiceAccount: karpenter\nannotation: eks.amazonaws.com/role-arn = karpenter-controller-role"]
    end

    subgraph Cryptographic_Foundation["Cryptographic Encryption Layer (AWS KMS)"]
        KMS_CMK["AWS KMS Customer Managed Key (CMK)\nalias/ray-platform-test-key\n- Automatic 1-Year Key Rotation\n- Enforces Envelope Encryption"]
    end

    subgraph AWS_Resources["Protected AWS Resources (Encrypted at Rest & in Transit)"]
        S3_DATA[("Amazon S3 Buckets\n- Server-Side Encryption: aws:kms\n- Bucket Policy: Deny Non-TLS (aws:SecureTransport)\n- Block All Public Access: TRUE")]
        DDB[("Amazon DynamoDB: ray_processing_ledger\n- KMS Managed Encryption\n- Point-In-Time Recovery (PITR) Enabled")]
        EBS[("EC2 Host EBS Volumes (gp3)\n- KMS CMK Encrypted Blocks")]
        SQS_INT[("SQS Interruption Queue\n- KMS SQS SSE Enabled")]
        ECR_REG[("Amazon ECR: ray-data-processor\n- KMS Encryption & Image Scan On Push")]
    end

    subgraph Pod_Runtime_Security["Pod & Host Hardening (Defense-in-Depth)"]
        IMDSV2["IMDSv2 Enforced\n- HttpTokens: Required\n- HttpPutResponseHopLimit: 1\n(Blocks Pod Credential Theft)"]
        SEC_CTX["Pod SecurityContext\n- allowPrivilegeEscalation: false\n- readOnlyRootFilesystem: true (where feasible)\n- drop: ALL capabilities"]
        NET_POL["Kubernetes NetworkPolicy\n- Default Deny Ingress\n- Whitelist Intra-Ray RPC (:6379, :10001)"]
    end

    %% Identity Federation
    OIDC_EKS --> SA_RAY
    OIDC_EKS --> SA_KARP
    GHA_OIDC -->|"Federated CI/CD AssumeRole"| AWS_IAM
    AWS_IAM --> ACCESS_ENTRY

    %% Role Bounds
    SA_RAY -->|"Assumes via STS AssumeRoleWithWebIdentity"| AWS_IAM
    SA_KARP -->|"Assumes via STS AssumeRoleWithWebIdentity"| AWS_IAM

    %% Cryptographic Ties
    KMS_CMK -.->|"Encrypts Data at Rest"| S3_DATA
    KMS_CMK -.->|"Encrypts Ledger at Rest"| DDB
    KMS_CMK -.->|"Encrypts Node Volumes"| EBS
    KMS_CMK -.->|"Encrypts Interruption Messages"| SQS_INT
    KMS_CMK -.->|"Encrypts Container Images"| ECR_REG

    %% Node Hardening
    ACCESS_ENTRY --> EBS
    IMDSV2 --- SEC_CTX
    SEC_CTX --- NET_POL
```

---

## Security Pillars

1. **Workload Identity (IRSA):** Pods obtain short-lived AWS STS credentials via IAM OpenID Connect federation. No permanent AWS access keys or secrets exist in Git, configuration files, or container layers.
2. **KMS Envelope Encryption:** A dedicated Customer Managed Key (CMK) with annual rotation encrypts all data at rest across S3 buckets, DynamoDB ledgers, Karpenter node EBS root disks, and SQS interruption queues.
3. **Transit Encryption Enforcement:** All S3 bucket policies reject any HTTP requests that do not specify `aws:SecureTransport: true` (TLS 1.2+ mandatory).
4. **Zero Legacy `aws-auth`:** Karpenter Spot nodes register via AWS EKS Access Entries (`EC2_LINUX`), isolating node authentication from user permissions.
5. **IMDSv2 Defense:** Node metadata responses require session tokens and are restricted to a hop limit of `1`, barring pods from querying the EC2 instance identity metadata service.
