# 01 — Complete Platform Architecture (Serverless Alternative)

This document provides the high-level architecture overview of the **AWS Serverless AI & Data Lakehouse Platform** on branch `serverless`.

---

## 1. Architectural Diagram

```mermaid
flowchart TD
    %% Serverless Complete Platform Architecture Diagram
    subgraph External["External Triggers & Ingestion Sources"]
        S1["Source S1: Supply Chain CSV\n(1,200 records)"]
        S2["Source S2: Financial Records CSV\n(1,200 records)"]
        CRON["Amazon EventBridge (Scheduled Cron: cron(0 2 * * ? *))"]
        S3_EVT["S3 ObjectCreated Event (EventBridge)"]
        DEV["Data / DevOps Engineer (AWS CLI & Terraform)"]
        GHA["GitHub Actions CI/CD (OIDC Federated)"]
    end

    subgraph AWS["AWS Cloud (us-east-1) - Serverless Architecture"]
        subgraph IAM_KMS["Identity & Cryptographic Foundations"]
            KMS["AWS KMS Customer Managed Key (CMK)\n(alias/ray-platform-test-key)"]
            LAMBDA_ROLE["IAM Role: lambda_exec_role\n(S3, DynamoDB, Glue, SQS, Logs)"]
            SFN_ROLE["IAM Role: step_functions_role\n(InvokeFunction, SQS DLQ)"]
        end

        subgraph IngestionLanding["Amazon S3: Raw Landing Zone"]
            S3_IN["s3://test-ray-platform-data/incoming/\n(Raw Corporate CSVs)"]
        end

        subgraph OrchestrationEngine["AWS Step Functions State Machine (Orchestrator)"]
            direction TB
            START(["State Machine Execution Start"])

            subgraph S1_Stage["Stage 1: Discovery & Idempotency Claim"]
                L_DISC["AWS Lambda: handler_discovery\n- SHA256 input dataset digest\n- DynamoDB Conditional Put: status=CLAIMED\n- RAM: 512MB | Timeout: 60s"]
            end

            subgraph S2_Stage["Stage 2: Dynamic Schema Validation (Distributed Map)"]
                MAP["Step Functions Distributed Map State\n(Parallel Ingestion across S1 and S2)"]
                L_VAL_S1["AWS Lambda: handler_validator (S1)\n- Dynamic header normalization\n- Pydantic schema validation\n- RAM: 1024MB | Timeout: 120s"]
                L_VAL_S2["AWS Lambda: handler_validator (S2)\n- Dynamic header normalization\n- Pydantic schema validation\n- RAM: 1024MB | Timeout: 120s"]
            end

            subgraph S3_Stage["Stage 3: Multi-Tier Entity Resolution"]
                L_RES["AWS Lambda: handler_resolver\n- Exact Tax ID Match (1.0)\n- Fuzzy Levenshtein (>= 0.88)\n- Jurisdiction & Founded Year Corroboration\n- Ambiguity Quarantining\n- RAM: 2048MB | Timeout: 300s"]
            end

            subgraph S4_Stage["Stage 4: Apache Iceberg Lakehouse Sink"]
                L_ICE["AWS Lambda: handler_iceberg_sink\n- PyIceberg ACID Upsert\n- AWS Glue Catalog Lock / Commit\n- Snappy Parquet Data Files\n- RAM: 2048MB | Timeout: 300s"]
            end

            subgraph S5_Stage["Stage 5: Machine Learning Training"]
                L_TRAIN["AWS Lambda: handler_trainer\n- Feature Extraction (Log-Revenue, Age)\n- Gradient Boosting Regressor\n- Asserts R^2 >= 0.85, RMSE, MAE\n- RAM: 3072MB | Timeout: 600s"]
            end

            subgraph S6_Stage["Stage 6: Finalization & Telemetry"]
                L_FIN["AWS Lambda: handler_finalizer\n- Updates DynamoDB: status=COMPLETED\n- Emits CloudWatch Custom Metrics\n- RAM: 512MB | Timeout: 60s"]
            end

            subgraph ErrorHandling["Fault Tolerance & Dead-Letter Routing"]
                CATCH["Step Functions Catch States.ALL\n(Retry: 3x with Exponential Backoff)"]
                SQS_DLQ["Amazon SQS Dead-Letter Queue (DLQ)\n(14-Day Message Retention)"]
                DDB_FAIL["DynamoDB Ledger: status=FAILED"]
            end

            START --> L_DISC
            L_DISC --> MAP
            MAP --> L_VAL_S1
            MAP --> L_VAL_S2
            L_VAL_S1 --> L_RES
            L_VAL_S2 --> L_RES
            L_RES --> L_ICE
            L_ICE --> L_TRAIN
            L_TRAIN --> L_FIN

            L_DISC -.->|Error| CATCH
            MAP -.->|Error| CATCH
            L_RES -.->|Error| CATCH
            L_ICE -.->|Error| CATCH
            L_TRAIN -.->|Error| CATCH
            CATCH --> SQS_DLQ
            CATCH --> DDB_FAIL
        end

        subgraph StorageLayer["Data Lakehouse, State & Catalog Layer"]
            DDB[("Amazon DynamoDB: ray_processing_ledger\n(PK: execution_id, SK: timestamp)")]
            GLUE[("AWS Glue Data Catalog\ncorporate_data_db.corporate_registry")]
            S3_WH["Amazon S3: iceberg-warehouse/\n(Apache Iceberg v2 Parquet & Avro)"]
            S3_QUAR["Amazon S3: quarantine/\n(Ambiguous Records Dead-Letter)"]
            S3_MOD["Amazon S3: models/\n(Trained Regressor revenue_model.joblib)"]
        end

        subgraph TelemetryLayer["Observability & Centralized Logging"]
            CW_LOGS["Amazon CloudWatch Logs\n(/aws/lambda/sfn-corporate-*)"]
            CW_METRICS["Amazon CloudWatch Metrics\n(ExecutionDuration, CanonicalRecords, ModelR2)"]
        end
    end

    %% External Trigger Links
    S1 --> S3_IN
    S2 --> S3_IN
    CRON --> START
    S3_EVT --> START
    DEV --> START
    GHA -.-> AWS

    %% Storage Connections
    S3_IN -.-> L_DISC
    S3_IN -.-> L_VAL_S1
    S3_IN -.-> L_VAL_S2
    L_DISC <-->|Atomic Claim| DDB
    L_RES --> S3_QUAR
    L_ICE --> S3_WH
    L_ICE <-->|Optimistic Lock| GLUE
    L_TRAIN --> S3_MOD
    L_FIN -->|Mark Completed| DDB

    %% Observability Connections
    L_FIN --> CW_METRICS
    L_DISC -.-> CW_LOGS
    L_RES -.-> CW_LOGS
    L_ICE -.-> CW_LOGS
    L_TRAIN -.-> CW_LOGS
```

---

## 2. Component Mapping & Functional Summary

| Layer | AWS Service | Primary Functionality |
| :--- | :--- | :--- |
| **Orchestration** | AWS Step Functions | Coordinates the 6-stage pipeline using Amazon States Language (ASL) with Distributed Map and automatic retries. |
| **Compute** | AWS Lambda | 6 modular Python 3.12 functions running in isolated Firecracker microVMs. |
| **State & Idempotency**| Amazon DynamoDB | Atomic conditional lease claiming (`attribute_not_exists`) and execution state tracking. |
| **Lakehouse Storage** | Apache Iceberg on Amazon S3 | Snappy Parquet files with ACID metadata tree (v2). |
| **Lakehouse Catalog** | AWS Glue Data Catalog | Optimistic Concurrency Control (OCC) table lock and snapshot pointer management. |
| **Dead-Letter Recovery**| Amazon SQS DLQ | Captures terminal execution errors with 14-day retention. |
| **Anomaly Isolation** | Amazon S3 Quarantine | Diverts ambiguous entities ($0.65 - 0.87$ score) away from the production registry. |
| **Observability** | Amazon CloudWatch | Centralized structured JSON logging and custom performance metrics. |
