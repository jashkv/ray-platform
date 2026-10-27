# 07 — Zero-Trust Security, Identity & Cryptographic Architecture (Serverless Alternative)

This document provides the security, identity federation, and cryptographic envelope encryption architecture of the **AWS Serverless Platform**.

---

## 1. Architectural Diagram

```mermaid
flowchart TD
    %% Serverless Zero-Trust Security, Identity & Cryptographic Architecture
    subgraph IdentityFederation["Zero-Trust Identity Federation"]
        GHA["GitHub Actions CI/CD Pipeline"]
        AWS_OIDC["AWS IAM OpenID Connect (OIDC) Provider\n(token.actions.githubusercontent.com)"]
        DEPLOY_ROLE["IAM Role: github-actions-serverless-deployer\n(Condition: repo:org/repo:ref:refs/heads/serverless)"]
    end

    subgraph RuntimeWorkloadIdentity["Serverless Workload Identity (AWS Native STS)"]
        LAMBDA_EXEC_ROLE["IAM Role: lambda_exec_role\n- Temporary 1-Hour STS Credentials\n- Zero Long-Lived API Keys"]
        SFN_ROLE["IAM Role: step_functions_role\n- Restricted to lambda:InvokeFunction\n- Restricted to sqs:SendMessage"]
    end

    subgraph CryptographicFoundations["Cryptographic Key Management"]
        KMS_CMK["AWS KMS Customer Managed Key (CMK)\nKey ID: alias/ray-platform-test-key\n- Automatic 365-day rotation\n- Key Policy restricting usage to Lambda role"]
    end

    subgraph ResourcePolicies["Least-Privilege Resource Policies & Endpoints"]
        S3_POLICY["Amazon S3 Lakehouse Bucket Policy:\n- Deny Insecure HTTP (aws:SecureTransport: false)\n- Deny Unencrypted Uploads (s3:x-amz-server-side-encryption)\n- Block All 4 Public Access Settings"]
        DDB_POLICY["DynamoDB Table Policy:\n- SSE Specification Enabled (KMS)\n- Attribute-level conditional write enforcement"]
        GLUE_POLICY["AWS Glue Data Catalog Policy:\n- Database & Table IAM authentication only"]
        SQS_POLICY["SQS DLQ Policy:\n- SSE-KMS Encrypted\n- Strictly allows SendMessage from Step Functions"]
    end

    GHA -->|1. Presents JWT Token| AWS_OIDC
    AWS_OIDC -->|2. Validates Claims & Issues STS Session| DEPLOY_ROLE
    DEPLOY_ROLE -->|3. Deploys Serverless IaC| RuntimeWorkloadIdentity

    LAMBDA_EXEC_ROLE -->|Reads/Writes Data Files| S3_POLICY
    LAMBDA_EXEC_ROLE -->|Claims/Finalizes Leases| DDB_POLICY
    LAMBDA_EXEC_ROLE -->|Updates Table Pointer| GLUE_POLICY
    SFN_ROLE -->|Enqueues on Failure| SQS_POLICY

    KMS_CMK -.->|Envelope Encryption| S3_POLICY
    KMS_CMK -.->|Envelope Encryption| DDB_POLICY
    KMS_CMK -.->|Envelope Encryption| SQS_POLICY
```

---

## 2. Core Security Guarantees

1. **Zero Static Long-Lived Credentials:**
   All execution is authenticated via temporary AWS STS tokens rotated automatically every hour. No AWS keys are stored anywhere.
2. **KMS CMK Envelope Encryption:**
   S3 buckets, DynamoDB ledger items, and SQS messages are encrypted with an AWS KMS Customer Managed Key (`alias/ray-platform-test-key`).
3. **No Container Host Escapes:**
   By relying on Firecracker microVMs, hardware-enforced boundaries isolate every Lambda execution.
