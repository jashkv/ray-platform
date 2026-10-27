# 11 — AWS Serverless Alternative Architecture

This document provides the architectural reference and deep-dive for the **AWS Serverless Alternative** implemented on the `serverless` branch.

It demonstrates how the corporate data engineering, deterministic entity resolution, Apache Iceberg lakehouse storage, and machine learning training pipeline can be orchestrated using AWS native serverless primitives—**AWS Step Functions, AWS Lambda, Amazon DynamoDB, AWS Glue Data Catalog, and Amazon S3**—achieving a **$0.00 idle baseline cost** with zero Kubernetes cluster management.

---

## 1. Architectural Diagram

```mermaid
flowchart TD
    subgraph TriggerLayer["Trigger & Event Ingestion"]
        S3_EVENT["Amazon EventBridge / S3 ObjectCreated"]
        CRON["Amazon EventBridge (Scheduled Cron: cron(0 2 * * ? *))"]
        API["Amazon API Gateway / Manual Step Functions Trigger"]
        S3_RAW["Amazon S3: incoming/\n(Raw CSV Datasets: S1 & S2)"]
    end

    subgraph Orchestration["AWS Step Functions State Machine (Orchestration Engine)"]
        SF_START(["State Machine Start\n(sfn-corporate-data-pipeline)"])

        subgraph S1_Stage["Stage 1: Discovery & Idempotency Claim"]
            L_DISC["AWS Lambda: handler_discovery\n- Computes SHA256 dataset hash\n- DynamoDB Conditional Put: status=CLAIMED\n- Memory: 512MB | Timeout: 60s"]
        end

        subgraph S2_Stage["Stage 2: Dynamic Schema Validation (Distributed Map)"]
            MAP_VALIDATE["Step Functions Distributed Map\n(Parallel Ingestion over Input Files)"]
            L_VAL_S1["AWS Lambda: handler_validator (S1)\n- Supply Chain CSV Dynamic Schema Discovery\n- Normalizes to canonical Pydantic model\n- Memory: 1024MB | Timeout: 120s"]
            L_VAL_S2["AWS Lambda: handler_validator (S2)\n- Financial CSV Dynamic Schema Discovery\n- Normalizes to canonical Pydantic model\n- Memory: 1024MB | Timeout: 120s"]
        end

        subgraph S3_Stage["Stage 3: Multi-Tier Entity Resolution"]
            L_RES["AWS Lambda: handler_resolver\n- Exact Tax ID Match\n- Fuzzy Levenshtein Name Match (Similarity >= 0.88)\n- Country & Founded Year Corroboration\n- Quarantines Ambiguous Records\n- Memory: 2048MB | Timeout: 300s"]
        end

        subgraph S4_Stage["Stage 4: Apache Iceberg Lakehouse Sink"]
            L_ICE["AWS Lambda: handler_iceberg_sink\n- PyIceberg ACID Upsert\n- AWS Glue Catalog Lock / Snapshot Commit\n- Partitioned Snappy Parquet\n- Memory: 2048MB | Timeout: 300s"]
        end

        subgraph S5_Stage["Stage 5: Gradient Boosting Regressor Training"]
            L_TRAIN["AWS Lambda: handler_trainer\n- Feature Engineering: Log-Revenue, Age, Confidence\n- Scikit-Learn GradientBoostingRegressor (or XGBoost)\n- Evaluates R^2 >= 0.85, RMSE, MAE\n- Serializes model to S3 /tmp\n- Memory: 3072MB | Timeout: 600s"]
        end

        subgraph S6_Stage["Stage 6: Ledger Finalization & Telemetry"]
            L_FIN["AWS Lambda: handler_finalizer\n- DynamoDB Ledger Status Update: COMPLETED\n- Emits CloudWatch Custom Metrics\n- Emits Summary JSON Payload\n- Memory: 512MB | Timeout: 60s"]
        end

        subgraph Failure_Stage["Error Handling & Dead-Letter Routing"]
            CATCH["Step Functions Catch States.ALL\n(Retry: 3x with Exponential Backoff)"]
            SQS_DLQ["Amazon SQS Dead-Letter Queue (DLQ)\n(14-Day Message Retention)"]
            DDB_FAIL["DynamoDB Ledger Status Update: FAILED"]
        end
    end

    subgraph StateStorage["State, Catalog & Storage Layer"]
        DDB[("Amazon DynamoDB\nray_processing_ledger\n(PK: execution_id, SK: timestamp)")]
        GLUE[("AWS Glue Data Catalog\ncorporate_data_db.corporate_registry")]
        S3_WH["Amazon S3: iceberg-warehouse/\n(Apache Iceberg v2 Parquet Metadata & Data)"]
        S3_QUAR["Amazon S3: quarantine/\n(Ambiguous Entity Records)"]
        S3_MOD["Amazon S3: models/\n(Trained Regressor revenue_model.joblib)"]
    end

    subgraph Telemetry["Observability & Monitoring"]
        CW_LOGS["Amazon CloudWatch Logs\n(/aws/lambda/sfn-corporate-*)"]
        CW_METRICS["Amazon CloudWatch Metrics\n(ExecutionDuration, RecordsProcessed, ModelR2)"]
    end

    %% Trigger Wiring
    S3_EVENT --> SF_START
    CRON --> SF_START
    API --> SF_START
    S3_RAW -.-> L_DISC
    S3_RAW -.-> L_VAL_S1
    S3_RAW -.-> L_VAL_S2

    %% State Machine Sequential Flow
    SF_START --> L_DISC
    L_DISC --> MAP_VALIDATE
    MAP_VALIDATE --> L_VAL_S1
    MAP_VALIDATE --> L_VAL_S2
    L_VAL_S1 --> L_RES
    L_VAL_S2 --> L_RES
    L_RES --> L_ICE
    L_ICE --> L_TRAIN
    L_TRAIN --> L_FIN

    %% Storage Connections
    L_DISC <-->|Conditional Put| DDB
    L_RES --> S3_QUAR
    L_ICE --> S3_WH
    L_ICE <-->|Snapshot Lock| GLUE
    L_TRAIN --> S3_MOD
    L_FIN -->|Mark Completed| DDB

    %% Error Handling Connections
    L_DISC -.->|Error| CATCH
    MAP_VALIDATE -.->|Error| CATCH
    L_RES -.->|Error| CATCH
    L_ICE -.->|Error| CATCH
    L_TRAIN -.->|Error| CATCH
    CATCH --> SQS_DLQ
    CATCH --> DDB_FAIL

    %% Observability Connections
    L_DISC -.-> CW_LOGS
    L_RES -.-> CW_LOGS
    L_ICE -.-> CW_LOGS
    L_TRAIN -.-> CW_LOGS
    L_FIN -.-> CW_METRICS
```

---

## 2. Core Architectural Pillars

### 2.1 State Machine Orchestration (AWS Step Functions)
- **Declarative Pipeline:** Formatted in Amazon States Language (ASL), defining states, execution branches, retries, and catches in JSON.
- **Distributed Map:** Dynamically iterates across raw S3 CSV objects (e.g. `supply_chain_data_s1.csv` and `financial_data_s2.csv`), running schema inspection and validation concurrently in parallel Lambda instances.
- **Deterministic Fault Recovery:** Every stage includes automated exponential backoff retries (`IntervalSeconds: 2`, `BackoffRate: 2.0`, `MaxAttempts: 3`). Any terminal failure is caught by `States.ALL`, notifying the SQS Dead-Letter Queue (DLQ) and marking the DynamoDB ledger record as `FAILED`.

### 2.2 Micro-Function Compute Layer (AWS Lambda)
- **Stage 1 (Discovery & Claim):** Computes a SHA256 checksum across input payloads to generate a deterministic `execution_id`. Executes an atomic DynamoDB conditional write (`attribute_not_exists(execution_id)`) to enforce run idempotency.
- **Stage 2 (Dynamic Schema Validation):** Reads unknown, evolving CSV structures, inspects case-insensitive header variants (`corporate_name` vs `company_name`, `tax_identifier` vs `ein`, `revenue_usd` vs `annual_revenue`), normalizes types, and filters malformed rows.
- **Stage 3 (Multi-Tier Entity Resolution):** Directly leverages the exact `EntityResolverEngine` business logic:
  - Exact Tax ID Match.
  - Fuzzy Levenshtein string matching on legal names (similarity threshold $\ge 0.88$).
  - Two-factor corroboration across jurisdiction (Country Code) and Founded Year.
  - Quarantining ambiguous candidates to S3 DLQ for auditor review.
- **Stage 4 (Apache Iceberg Lakehouse Sink):** Executes transactional ACID upserts into `corporate_data_db.corporate_registry` using PyIceberg, committing metadata snapshots to S3 backed by AWS Glue Data Catalog locks.
- **Stage 5 (Gradient Boosting Regressor Training):** Trains an annual revenue prediction model using Scikit-Learn/XGBoost, evaluating test set $R^2 \ge 0.85$, RMSE, and MAE, serializing model artifacts to `s3://.../models/revenue_model.joblib`.
- **Stage 6 (Finalization & Telemetry):** Updates DynamoDB ledger to `COMPLETED`, records execution duration and entity counts, and publishes custom CloudWatch metrics.

### 2.3 Storage & Catalog Layer
- **Amazon S3:** Divided into distinct object prefixes: `incoming/`, `iceberg-warehouse/`, `quarantine/`, and `models/`.
- **Amazon DynamoDB:** `ray_processing_ledger` stores run lifecycle states (`CLAIMED` -> `PROCESSING` -> `COMPLETED` / `FAILED`), record metrics, and snapshot IDs.
- **AWS Glue Data Catalog:** Manages Iceberg table schema, partitions, and atomic snapshot pointer updates using optimistic concurrency control (OCC).
- **Amazon SQS DLQ:** Retains failed Step Functions payloads for up to 14 days for forensic replay and debugging.

---

## 3. Operational Characteristics & Comparison

| Operational Metric | Amazon EKS + Ray Platform | AWS Serverless Alternative |
| :--- | :--- | :--- |
| **Idle Baseline Cost** | ~$140/mo (EKS Control Plane, NAT Gateways, System Nodes) | **$0.00/mo (Zero idle resources)** |
| **Cold Start Latency** | ~45s (Karpenter Spot Node provision + Container Pull) | **< 1.5s (Lambda container/zip initialization)** |
| **Execution Duration Limit** | Unbounded (Hours to Days for deep training) | **15 minutes per function invocation** |
| **Memory Allocation Limit** | Up to hundreds of GBs per node (e.g., `m6i.32xlarge`) | **10,240 MB (10 GiB) per Lambda** |
| **Operational Overhead** | Kubernetes upgrades, KubeRay CRDs, Karpenter NodePools | **Zero infrastructure maintenance** |
| **Best Suited For** | Continuous streaming, large models, multi-GB datasets | **Infrequent batch loads, scheduled runs, micro-costs** |
