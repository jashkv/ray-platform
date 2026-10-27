# 10 — CI/CD Pipeline & GitOps Deployment Lifecycle (Serverless Alternative)

This document provides the CI/CD pipeline, automated testing gates, and GitOps infrastructure lifecycle for the **AWS Serverless Platform**.

---

## 1. Architectural Diagram

```mermaid
flowchart TD
    %% Serverless CI/CD Pipeline & GitOps Deployment Lifecycle
    subgraph SourceControl["Source Control & Developer Workstation"]
        DEV["Data / DevOps Engineer"]
        GIT_REPO["GitHub Repository: serverless branch"]
        MAKEFILE["Unified Makefile (make tf-plan-serverless / make e2e-serverless-local)"]
    end

    subgraph GHA_Workflow["GitHub Actions CI/CD Pipeline (.github/workflows/)"]
        direction TB

        subgraph Stage_Lint["Stage 1: Static Analysis & Unit Tests"]
            TEST_UNIT["make test-serverless\n(Pytest: 5/5 Passing in ~96s)"]
            TF_LINT["make lint-tf\n(Canonical Formatting Check)"]
            REPO_VAL["./scripts/validate_repo.sh\n(Layout, Credentials, Syntax)"]
        end

        subgraph Stage_Auth["Stage 2: Zero-Trust Cloud Authentication"]
            GHA_STS["AWS OIDC Federation\n(aws-actions/configure-aws-credentials)\n- Role: gha-serverless-deployer\n- Zero Long-Lived Secrets"]
        end

        subgraph Stage_Terraform["Stage 3: Serverless Terraform Provisioning"]
            TF_INIT["make tf-init-serverless\n(Download AWS & Archive Providers)"]
            TF_VAL["make tf-validate-serverless\n(Validate ASL & HCL Syntax)"]
            TF_PLAN["make tf-plan-serverless\n(Plan State Machine, Lambdas, SQS, IAM)"]
            TF_APPLY["terraform apply -auto-approve\n(Deploys complete stack in < 90s)"]
            TF_INIT --> TF_VAL --> TF_PLAN --> TF_APPLY
        end

        subgraph Stage_Verification["Stage 4: Automated Cloud Smoke Test"]
            TRIGGER_SFN["aws stepfunctions start-execution\n(Submit test pipeline execution)"]
            POLL_EXEC["Poll Execution Status -> SUCCEEDED"]
            ASSERT_OUTPUTS["Assert Iceberg Snapshot ID & DynamoDB Ledger Status: COMPLETED"]
            TRIGGER_SFN --> POLL_EXEC --> ASSERT_OUTPUTS
        end
    end

    DEV -->|"git push origin serverless"| GIT_REPO
    DEV -.->|"Local Orchestration"| MAKEFILE
    GIT_REPO --> Stage_Lint
    Stage_Lint --> Stage_Auth
    Stage_Auth --> Stage_Terraform
    Stage_Terraform --> Stage_Verification
```

---

## 2. Automated Pipeline Stages

1. **Stage 1 (Static Analysis & Unit Tests):**
   - Runs Pytest across serverless handlers (`make test-serverless`).
   - Checks canonical Terraform formatting (`make lint-tf`).
   - Validates repository layout and secret pre-checks (`validate_repo.sh`).
2. **Stage 2 (OIDC Cloud Authentication):**
   - Authenticates to AWS via GitHub Actions OpenID Connect (OIDC) without long-lived secret keys.
3. **Stage 3 (Serverless Terraform Provisioning):**
   - Plans and deploys the Step Functions state machine, 6 Lambda functions, SQS DLQ, and IAM roles in under 90 seconds.
4. **Stage 4 (Cloud Smoke Test):**
   - Triggers a test Step Functions execution and asserts completion status in DynamoDB.
