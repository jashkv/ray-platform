# 10 — CI/CD Pipeline, GitOps & Infrastructure Lifecycle

This document describes the **Automated CI/CD Deployment Lifecycle**, detailing the testing gates, Terraform layering, container build, Helm orchestration, and end-to-end verification.

---

## CI/CD Pipeline Diagram

```mermaid
flowchart TD
    %% CI/CD, GitOps & Infrastructure Lifecycle
    subgraph Source_Control["Source Control & Developer Workstation"]
        DEV["Platform / ML Engineer"]
        GIT_REPO["GitHub Repository: main branch"]
        MAKEFILE["Unified Makefile (make tf-apply-all / make deploy-all)"]
    end

    subgraph GHA_Workflow["GitHub Actions CI/CD Pipeline (.github/workflows/)"]
        direction TB

        subgraph Stage_Lint["Stage 1: Static Analysis & Unit Tests"]
            TEST_UNIT["make test-unit\n(Pytest: 7/7 Passing)"]
            TF_LINT["make lint-tf\n(Canonical Formatting)"]
            REPO_VAL["./scripts/validate_repo.sh\n(Layout, Credentials, Syntax)"]
            K8S_VAL["./scripts/validate_k8s_manifests.sh\n(YAML, Resources, CRDs)"]
        end

        subgraph Stage_Auth["Stage 2: Zero-Trust Cloud Authentication"]
            GHA_STS["AWS OIDC Federation\n(aws-actions/configure-aws-credentials)\n- Role: gha-deployment-role\n- Zero Long-Lived Secrets"]
        end

        subgraph Stage_Terraform["Stage 3: Terraform Layered Provisioning"]
            TF_BOOT["01-bootstrap: S3 State Bucket & Lock Table"]
            TF_NET["02-network: VPC, 3 AZs, PrivateLink Endpoints"]
            TF_EKS["03-eks: EKS 1.30, System NodeGroup, Karpenter Module"]
            TF_DATA["04-data: S3 Buckets, DynamoDB Ledger, KMS CMK, Glue"]
            TF_PLAT["05-platform: ECR Repository & Base Platform Config"]
            TF_BOOT --> TF_NET --> TF_EKS --> TF_DATA --> TF_PLAT
        end

        subgraph Stage_Docker["Stage 4: Container Build & Push"]
            DOCKER_BUILD["Docker Build (Multi-Stage Build)\n- Base: Ray 2.40.0-py310\n- Dependencies: PyIceberg, LightGBM, AWS SDK"]
            ECR_PUSH["Docker Push to Amazon ECR\n(123456789012.dkr.ecr.us-east-1.amazonaws.com)"]
        end

        subgraph Stage_K8s["Stage 5: Kubernetes & Helm GitOps Deployment"]
            HELM_KARP["Helm Install Karpenter v1.0.8"]
            APPLY_CRDS["kubectl apply:\n- EC2NodeClass\n- NodePool (Spot & On-Demand)"]
            HELM_KUBERAY["Helm Install KubeRay Operator v1.2.2"]
            APPLY_RAYCLUSTER["kubectl apply:\n- ray-cluster.yaml\n- ray-podmonitor.yaml\n- rbac.yaml"]
        end

        subgraph Stage_Verification["Stage 6: Smoke Test & Job Execution"]
            SMOKE_TEST["make ray-smoke-test\n(Submit lightweight Ray job)"]
            JOB_SUBMIT["Submit RayJob CRD\n(Data Processing & LightGBM Training)"]
            E2E_VERIFY["make e2e-verify\n(Assert Iceberg snapshot & DDB ledger)"]
        end
    end

    %% Wiring
    DEV -->|"git push origin main"| GIT_REPO
    DEV -.->|"Local Orchestration"| MAKEFILE
    GIT_REPO --> Stage_Lint
    Stage_Lint --> Stage_Auth
    Stage_Auth --> Stage_Terraform
    Stage_Terraform --> Stage_Docker
    Stage_Docker --> Stage_K8s
    Stage_K8s --> Stage_Verification
```

---

## Deployment Stage Descriptions

| Stage | Command / Trigger | Actions & Validations |
| :--- | :--- | :--- |
| **1. Static Analysis & Unit Tests** | Automated on PR / push | Runs `pytest`, `terraform fmt -check`, bash manifest validation, and zero-credential leak pre-checks. |
| **2. Zero-Trust OIDC Auth** | `aws-actions/configure-aws-credentials` | Obtains short-lived AWS STS token via GitHub Actions OIDC federation. No static keys stored in GitHub Secrets. |
| **3. Terraform Layered Apply** | `make tf-apply-all` | Applies the 5 decoupled layers in order: `bootstrap` $\to$ `network` $\to$ `eks` $\to$ `data` $\to$ `platform`. |
| **4. Container Image Build** | `make docker-build-push` | Builds multi-stage Docker container with pinned Ray, PyIceberg, and ML runtimes; pushes to AWS ECR. |
| **5. Helm & Kubernetes Deploy** | `make deploy-all` | Installs Karpenter `v1.0.8`, registers `EC2NodeClass` and `NodePool`, deploys KubeRay Operator `v1.2.2`, and launches the `RayCluster`. |
| **6. End-to-End Verification** | `make e2e-verify` | Submits Ray smoke job, tests dynamic autoscaling to Spot instances, validates Iceberg snapshot write, and confirms DynamoDB ledger completion. |
