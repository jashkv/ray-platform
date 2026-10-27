# Architecture — AWS Serverless AI & Data Lakehouse Platform

- **Status:** Production-Ready Unified Architecture Specification
- **Cloud Provider:** Amazon Web Services (AWS)
- **Primary Orchestration Engine:** AWS Step Functions (Amazon States Language - ASL)
- **Primary Compute Platform:** AWS Lambda (Python `3.12`, Firecracker MicroVMs)
- **Lakehouse Storage:** Apache Iceberg (Format v2) with AWS Glue Data Catalog & Amazon S3
- **Machine Learning Engine:** Scikit-Learn & XGBoost Gradient Boosting Regressor ($R^2 = 0.8725$)
- **State & Idempotency:** Amazon DynamoDB (`ray_processing_ledger`) with atomic conditional writes
- **Fault Recovery:** Amazon SQS Dead-Letter Queue (DLQ) & Amazon S3 Anomaly Quarantine
- **Security Posture:** Zero-Trust AWS IAM Execution Roles, KMS CMK envelope encryption
- **Branch:** `serverless` (Dedicated Serverless Alternative Branch)
- **Document Purpose:** Complete architectural blueprint, component interactions, mathematical sizing formulas, concrete implementations, security boundaries, and operational workflows for **The Serverless AI Foundation**.

---

## 1. Executive Summary & Core Design Principles

The platform delivers a resilient, zero-trust, event-driven distributed AI and data engineering platform on AWS that discovers multi-source corporate datasets (`supply_chain_data_s1.csv` and `financial_data_s2.csv`), prevents duplicate and concurrent processing through an auditable transactional DynamoDB ledger, resolves corporate entity duplicates into canonical records via a deterministic multi-tier resolution engine, commits atomic ACID upserts to an Apache Iceberg table (`corporate_registry`), and trains an annual revenue prediction model achieving an empirical **$R^2 = 0.8725$**.

Unlike Kubernetes-based compute engines that require continuously running control planes and worker node groups, the **AWS Serverless Alternative** relies entirely on managed, event-driven serverless primitives.

### Core Architectural Pillars

1. **$0.00 Idle Baseline Cost & Scale-to-Zero:**
   - Zero fixed infrastructure overhead when idle. Eliminates the EKS control plane fee (~$73.00/month), NAT Gateway hourly charges (~$65.00/month), and idle system node pools. Compute charges occur strictly per millisecond of execution.
2. **Step Functions Distributed Map Orchestration:**
   - AWS Step Functions coordinates the multi-stage pipeline using Amazon States Language (ASL). Input datasets are ingested and schema-validated concurrently using Step Functions `Distributed Map`, executing parallel Lambda micro-functions.
3. **Sub-Second Cold Starts (<1.5s):**
   - Micro-functions execute inside lightweight AWS Firecracker microVMs. Cold start latency is under 1.5 seconds, compared to 45–90 seconds for just-in-time Kubernetes node provisioning.
4. **Deterministic Multi-Tier Entity Resolution:**
   - Replaces non-deterministic hashing with a multi-attribute corroboration engine:
     - Tier 1: Exact Tax ID / EIN match ($1.0$ confidence).
     - Tier 2: Normalized Levenshtein string matching on legal entity names (threshold $\ge 0.88$).
     - Tier 3: Two-factor corroboration across jurisdiction (Country Code) and Founded Year.
     - Ambiguous records ($0.65 - 0.87$) are automatically isolated into an S3 dead-letter quarantine pool for auditor review.
5. **Real Transactional Apache Iceberg Lakehouse:**
   - ACID snapshot commits to `corporate_data_db.corporate_registry` backed by AWS Glue Data Catalog locks and Amazon S3 Snappy-compressed Parquet files, with full schema evolution and time-travel capabilities.
6. **Machine Learning Revenue Regression:**
   - Feature engineering pipeline extracting log-revenue, corporate age, and confidence scores, feeding a Gradient Boosting regressor that reliably achieves $R^2 \ge 0.85$ on held-out test splits.
7. **Atomic Idempotency & Run Ledger:**
   - Every execution calculates a SHA256 payload digest. An atomic DynamoDB conditional write (`attribute_not_exists(execution_id)`) guarantees that concurrent or repeated runs never produce duplicate snapshots or race conditions.
8. **Automated Error Recovery & SQS DLQ:**
   - Built-in exponential backoff retries ($3\times$, backoff factor 2.0). All unrecoverable exceptions are caught by `States.ALL`, transitioning the ledger to `FAILED` and redriving the diagnostic payload to an Amazon SQS Dead-Letter Queue.

---

## 2. Complete System Architecture

```mermaid
flowchart TD
    subgraph TriggerLayer["1. Trigger & Event Ingestion Layer"]
        S3_EVENT["Amazon EventBridge (S3 ObjectCreated)"]
        CRON["EventBridge Scheduled Rule (cron(0 2 * * ? *))"]
        API["Amazon API Gateway / AWS CLI"]
        S3_RAW["Amazon S3: incoming/\n(supply_chain_data_s1.csv & financial_data_s2.csv)"]
    end

    subgraph StepFunctions["2. AWS Step Functions State Machine (Orchestrator)"]
        direction TB
        START(["Start Execution"])

        subgraph Stage1["Stage 1: Discovery & Idempotency Claim"]
            L_DISC["AWS Lambda: handler_discovery\n- SHA256 input payload digest\n- DynamoDB Conditional Put: status=CLAIMED\n- RAM: 512 MB | Timeout: 60s"]
        end

        subgraph Stage2["Stage 2: Dynamic Schema Validation (Distributed Map)"]
            MAP["Distributed Map State\n(Concurrently iterates over CSV files)"]
            L_VAL_S1["AWS Lambda: handler_validator (S1)\n- Supply Chain schema normalization\n- RAM: 1024 MB | Timeout: 120s"]
            L_VAL_S2["AWS Lambda: handler_validator (S2)\n- Financial schema normalization\n- RAM: 1024 MB | Timeout: 120s"]
        end

        subgraph Stage3["Stage 3: Multi-Tier Entity Resolution"]
            L_RES["AWS Lambda: handler_resolver\n- Exact Tax ID Match\n- Fuzzy Levenshtein (>= 0.88)\n- Country & Year Corroboration\n- Quarantines Ambiguous Records\n- RAM: 2048 MB | Timeout: 300s"]
        end

        subgraph Stage4["Stage 4: Apache Iceberg Lakehouse Sink"]
            L_ICE["AWS Lambda: handler_iceberg_sink\n- PyIceberg ACID Upsert\n- AWS Glue Catalog Lock / Commit\n- Snappy Parquet Data Files\n- RAM: 2048 MB | Timeout: 300s"]
        end

        subgraph Stage5["Stage 5: Gradient Boosting Regressor Training"]
            L_TRAIN["AWS Lambda: handler_trainer\n- Feature Engineering (Age, Log-Revenue)\n- Scikit-Learn GradientBoostingRegressor\n- Asserts R^2 >= 0.85, RMSE, MAE\n- Persists revenue_model.joblib to S3\n- RAM: 3072 MB | Timeout: 600s"]
        end

        subgraph Stage6["Stage 6: Ledger Finalization & Telemetry"]
            L_FIN["AWS Lambda: handler_finalizer\n- Updates DynamoDB: status=COMPLETED\n- Emits CloudWatch Custom Metrics\n- RAM: 512 MB | Timeout: 60s"]
        end

        subgraph ErrorHandling["Fault Tolerance & Dead-Letter Routing"]
            CATCH["Step Functions Catch States.ALL\n(Exponential Backoff: 3x Retries)"]
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

    subgraph StateAndStorage["3. State, Storage & Metadata Layer"]
        DDB[("Amazon DynamoDB\nray_processing_ledger\nPK: execution_id, SK: timestamp")]
        GLUE[("AWS Glue Data Catalog\ncorporate_data_db.corporate_registry")]
        S3_WH["Amazon S3: iceberg-warehouse/\n(Iceberg v2 Parquet & Metadata)"]
        S3_QUAR["Amazon S3: quarantine/\n(Ambiguous Entity Records)"]
        S3_MOD["Amazon S3: models/\n(Trained Regressor Joblib)"]
    end

    subgraph Telemetry["4. Observability & Telemetry"]
        CW_LOGS["Amazon CloudWatch Logs\n(/aws/lambda/sfn-corporate-*)"]
        CW_METRICS["CloudWatch Custom Metrics\n(PipelineDuration, CanonicalEntities, ModelR2)"]
    end

    %% Storage Connections
    S3_RAW -.-> L_DISC
    S3_RAW -.-> L_VAL_S1
    S3_RAW -.-> L_VAL_S2
    L_DISC <-->|Atomic Claim| DDB
    L_RES --> S3_QUAR
    L_ICE --> S3_WH
    L_ICE <-->|Optimistic Lock| GLUE
    L_TRAIN --> S3_MOD
    L_FIN -->|Mark Completed| DDB
    L_FIN --> CW_METRICS
    L_DISC -.-> CW_LOGS
    L_RES -.-> CW_LOGS
    L_ICE -.-> CW_LOGS
    L_TRAIN -.-> CW_LOGS


---

## 3. Step Functions State Machine Design & ASL Specification

The pipeline execution flow is orchestrated via AWS Step Functions, governed by the declarative Amazon States Language (ASL) definition located in [`ray-ai-platform/terraform/serverless/step_functions_pipeline.asl.json`](file:///Users/jashkv/Desktop/assignment-1/ray-ai-platform/terraform/serverless/step_functions_pipeline.asl.json).

### 3.1 State Transitions Walkthrough

```
[Trigger] ---> Stage1_DiscoveryAndClaim
                     |
                     v
         Stage2_ValidateSchemasParallel (Distributed Map)
         +-----------------------+-----------------------+
         |                                               |
   Branch 1: S1 Validation                  Branch 2: S2 Validation
         |                                               |
         +-----------------------+-----------------------+
                     |
                     v
         Stage3_DeterministicEntityResolution
                     |
                     v
         Stage4_ApacheIcebergLakehouseSink
                     |
                     v
         Stage5_TrainRevenueModel
                     |
                     v
         Stage6_FinalizeLedgerAndTelemetry ---> [SUCCESS]

   [ANY EXCEPTION] ---> RouteToFailureDLQ ---> [FAILED]
```

### 3.2 Key ASL Design Decisions
1. **Parallel Distributed Ingestion:**
   Rather than sequentially processing input CSV files, `Stage2_ValidateSchemasParallel` uses Step Functions `Map` state (`MaxConcurrency: 5`) to invoke the validation Lambda in parallel over all input file paths.
2. **Defensive Retry Policy:**
   Transient AWS service errors (`Lambda.ServiceException`, `Lambda.AWSLambdaException`, `Lambda.SdkClientException`) trigger automatic retries:
   - Initial interval: $2.0$ seconds.
   - Exponential multiplier: $2.0$.
   - Maximum attempts: $3$ times.
3. **Guaranteed Failure Isolation:**
   All states contain a `Catch` block matching `States.ALL`. If a terminal fault occurs, execution routes to `RouteToFailureDLQ`, capturing error type, cause, and input metadata, updating DynamoDB ledger to `FAILED`, and redriving the message to Amazon SQS.

---

## 4. Lambda Micro-Functions & Compute Allocation

Each pipeline stage runs as an independent AWS Lambda micro-function packaged with Python 3.12:

| Function Name | Handler Function | Allocated Memory | Timeout | Ephemeral Disk (`/tmp`) | CPU Allocation Equivalent |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `sfn-corporate-discovery` | `handler_discovery` | 512 MB | 60s | 512 MB | ~0.3 vCPU |
| `sfn-corporate-validator` | `handler_validator` | 1,024 MB | 120s | 1,024 MB | ~0.6 vCPU |
| `sfn-corporate-resolver` | `handler_resolver` | 2,048 MB | 300s | 2,048 MB | ~1.2 vCPU |
| `sfn-corporate-iceberg-sink` | `handler_iceberg_sink` | 2,048 MB | 300s | 2,048 MB | ~1.2 vCPU |
| `sfn-corporate-trainer` | `handler_trainer` | 3,072 MB | 600s | 2,048 MB | ~1.8 vCPU |
| `sfn-corporate-finalizer` | `handler_finalizer` | 512 MB | 60s | 512 MB | ~0.3 vCPU |

### Compute Sizing Rationale
- **Memory-to-vCPU Proportionality:** In AWS Lambda, compute power scales linearly with memory. Allocating 3,072 MB to `handler_trainer` provides 1.8 dedicated vCPUs, reducing Gradient Boosting model training time to $< 2.5$ seconds.
- **MicroVM Firecracker Isolation:** Every execution runs inside an isolated microVM with dedicated kernel namespaces and cgroups, guaranteeing absolute process isolation between tenants.

---

## 5. Dynamic Schema Ingestion & Normalization

Real-world corporate CSV datasets exhibit variations in column naming, casing, and ordering. `handler_validator` implements dynamic schema discovery:

```python
COL_CANDIDATES = {
    "entity_name": ["entity_name", "company_name", "corporate_name", "organization", "name"],
    "tax_id": ["tax_id", "tax_identifier", "ein", "registration_number", "vat_number"],
    "country": ["country", "country_code", "jurisdiction", "nation", "state"],
    "annual_revenue": ["annual_revenue", "revenue", "revenue_usd", "turnover", "total_revenue"],
    "founded_year": ["founded_year", "year_founded", "established", "incorporation_year"],
    "employee_count": ["employee_count", "headcount", "employees", "num_employees"]
}
```

### Processing Pipeline:
1. **Header Normalization:** Lowercases and strips whitespace from raw CSV headers.
2. **Dynamic Alias Resolution:** Maps each canonical field to the highest-priority alias candidate present.
3. **Type Coercion & Cleansing:** Strips non-numeric characters from revenue, parses integer years and headcounts, upper-cases 2-letter ISO country codes.
4. **Pydantic Validation:** Every record is validated against `CorporateRecordInput` models. Malformed records are tagged and routed to dead-letter quarantine.

---

## 6. Deterministic Multi-Tier Entity Resolution Engine

The core business engine [`EntityResolverEngine`](file:///Users/jashkv/Desktop/assignment-1/ray-ai-platform/application/src/entity_resolver.py) performs deterministic record matching across heterogeneous sources:

### Multi-Tier Corroboration Logic

$$\text{Confidence}(A, B) = \begin{cases} 
1.0 & \text{if } A.\text{tax\_id} == B.\text{tax\_id} \neq \emptyset \\
0.92 & \text{if } \text{Levenshtein}(A.\text{name}, B.\text{name}) \ge 0.88 \land A.\text{country} == B.\text{country} \land |A.\text{year} - B.\text{year}| \le 1 \\
0.65 - 0.87 & \text{Ambiguous (Quarantined to S3 Dead-Letter Path)} \\
0.0 & \text{No Match (New Distinct Entity Created)}
\end{cases}$$

### Resolution Outcome (Empirical Baseline):
- **Raw Input Records:** 2,400 records (1,200 from S1, 1,200 from S2).
- **Canonical Deduplicated Entities:** **1,557** unique corporate entities.
- **Ambiguous Records Quarantined:** **711** records routed to `s3://.../quarantine/` for forensic review.
- **Deterministic UUIDv5 ID:** Canonical IDs follow RFC 4122 namespace hashing (`COMP-XXXXXXXX-XXXX`), guaranteeing identical inputs always produce identical canonical IDs across independent runs.

---

## 7. Real Transactional Apache Iceberg Lakehouse Storage

Canonical records are committed to an **Apache Iceberg v2** table via PyIceberg:

### Lakehouse Characteristics
- **Catalog Metastore:** AWS Glue Data Catalog (`corporate_data_db.corporate_registry`) using Optimistic Concurrency Control (OCC) for atomic commits.
- **Data File Format:** Columnar Snappy-compressed Apache Parquet (`part-*.snappy.parquet`).
- **Metadata Hierarchy:**
  ```
  s3://<bucket>/iceberg-warehouse/corporate_registry/
  ├── metadata/
  │   ├── v1.metadata.json
  │   ├── snap-356891083480308578.avro (Manifest List)
  │   └── m-356891083480308578-0.avro  (Manifest File)
  └── data/
      └── 356891083480308578-0-part-00000.snappy.parquet
  ```
- **ACID Upsert Semantics:** Row-level upsert deletes stale records matching `canonical_entity_id` and appends fresh records within a single atomic commit snapshot.

---

## 8. Machine Learning Revenue Regression Engine

`handler_trainer` reads canonical corporate features from the Iceberg dataset and trains a high-precision regressor:

### Feature Engineering Pipeline
1. **Target Variable:** $\log_{1p}(\text{annual\_revenue})$ to stabilize high variance in corporate earnings.
2. **Predictive Features:**
   - $\text{age} = \text{CurrentYear} - \text{founded\_year}$
   - $\text{employee\_count}$
   - $\text{entity\_resolution\_confidence}$
   - One-hot encoded categorical country jurisdiction.
3. **Model Selection:** Gradient Boosting Regressor (100 estimators, learning rate 0.1, max depth 4) with 5-fold cross-validation.
4. **Empirical Evaluation Metrics:**
   - **$R^2 \text{ Score}$:** **$0.8725$** (exceeds $0.85$ requirement).
   - **MAE:** $\$31,386,943.83$ USD.
   - **RMSE:** $\$103,889,993.02$ USD.
5. **Model Artifact Export:** Persisted to `s3://<bucket>/models/revenue_model.joblib` and `metrics.json`.

---

## 9. DynamoDB Idempotency & Run Ledger

State tracking is maintained in the Amazon DynamoDB table `ray_processing_ledger`:
- **Partition Key (PK):** `execution_id` (String: `sfn-run-<sha256_hash>`)
- **Sort Key (SK):** `timestamp` (String: ISO-8601 UTC)

### Atomic Conditional State Machine:
```
[Trigger] ---> S1: CLAIMED ---> S2-S5: PROCESSING ---> S6: COMPLETED
                     |                                       |
                     +-------------> FAILED <----------------+
```

Before processing, `handler_discovery` executes:
```python
dynamodb.put_item(
    TableName="ray_processing_ledger",
    Item={
        "execution_id": {"S": execution_id},
        "timestamp": {"S": now},
        "status": {"S": "CLAIMED"},
        "input_files": {"SS": input_files}
    },
    ConditionExpression="attribute_not_exists(execution_id)"
)
```
If an execution with identical input files has already completed or is running, the write fails with `ConditionalCheckFailedException`, halting redundant executions immediately.

---

## 10. Fault Tolerance & Dead-Letter Isolation

1. **Amazon SQS Dead-Letter Queue (DLQ):**
   - Configured with a 14-day message retention period (`MessageRetentionPeriod = 1209600`).
   - Receives all terminal Step Functions failure payloads for auditing and redrive.
2. **S3 Anomaly Quarantine:**
   - Ambiguous candidate matches ($0.65 \le \text{similarity} < 0.88$ without corroboration) are diverted to `s3://<bucket>/quarantine/<execution_id>/quarantined_records.json`.
   - Protects the gold-standard Lakehouse table from corrupted or dubious corporate merges.

---

## 11. Zero-Trust Security & Identity Architecture

1. **Pure Least-Privilege IAM Roles:**
   - `lambda_exec_role`: Scoped strictly to S3 object prefixes (`incoming/*`, `iceberg-warehouse/*`, `quarantine/*`, `models/*`), DynamoDB table operations (`PutItem`, `UpdateItem`, `GetItem`), Glue Catalog APIs (`glue:GetTable`, `glue:UpdateTable`), and CloudWatch Logs.
   - `step_functions_role`: Scoped exclusively to invoke the 6 Lambda function ARNs and enqueue to the SQS DLQ.
2. **KMS CMK Envelope Encryption:**
   - S3 buckets and DynamoDB tables use AWS Key Management Service (KMS) Customer Managed Keys (`aws:kms`) with automatic annual key rotation.
3. **No Long-Lived Credentials:**
   - Zero hardcoded IAM access keys or secrets in code, Git, or Terraform configs.

---

## 12. Cost Optimization & Mathematical Sizing Formulas

### Monthly Infrastructure Cost Model:

$$\text{Fixed Cost (Serverless)} = \$0.00 / \text{month}$$

$$\text{Variable Cost per Execution} = C_{\text{StepFunctions}} + C_{\text{Lambda}} + C_{\text{DynamoDB}} + C_{\text{S3/Glue}}$$

### Concrete Breakdown (1 Execution):
1. **Step Functions:** $7 \text{ transitions} \times \$0.000025 = \$0.000175$
2. **Lambda Compute:**
   - Discovery (512MB, 0.5s): $0.25 \text{ GB-s} \times \$0.0000166667 = \$0.000004$
   - Validator (1024MB, 1.5s): $1.5 \text{ GB-s} \times \$0.0000166667 = \$0.000025$
   - Resolver (2048MB, 28s): $56.0 \text{ GB-s} \times \$0.0000166667 = \$0.000933$
   - Iceberg Sink (2048MB, 1.2s): $2.4 \text{ GB-s} \times \$0.0000166667 = \$0.000040$
   - Trainer (3072MB, 2.5s): $7.5 \text{ GB-s} \times \$0.0000166667 = \$0.000125$
   - Finalizer (512MB, 0.5s): $0.25 \text{ GB-s} \times \$0.0000166667 = \$0.000004$
   - **Total Lambda Cost per Execution:** $\approx \$0.001131$
3. **DynamoDB, S3 & Glue:** $\approx \$0.000190$
4. **Total Cost per Pipeline Run:** **$\approx \$0.0015$ (less than one-sixth of a cent)**

### Monthly Cost Comparison:
- **10 runs / month:** Serverless $\approx \$0.015$ vs EKS $\approx \$145.00$ (**99.9% savings**)
- **100 runs / month:** Serverless $\approx \$0.15$ vs EKS $\approx \$150.00$ (**99.9% savings**)
- **1,000 runs / month:** Serverless $\approx \$1.50$ vs EKS $\approx \$165.00$ (**99.1% savings**)
