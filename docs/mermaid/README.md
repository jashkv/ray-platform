# AWS Serverless Platform — Master Architecture Diagrams & Visual Reference

This directory serves as the centralized visual architecture library for the **AWS Serverless AI & Data Lakehouse Platform** on branch `serverless` (`test` environment).

Every diagram is authored in standard [Mermaid.js](https://mermaid.js.org/) syntax, allowing direct GitHub/IDE rendering and programmatic export to SVG, PNG, and PDF.

---

## Diagram Index

| # | Diagram Title | Scope & Description | Source File | Deep-Dive Document |
| :---: | :--- | :--- | :---: | :---: |
| **01** | [Complete Serverless Architecture](#01--complete-serverless-architecture) | End-to-end cloud infrastructure, Step Functions, Lambda handlers, S3 Lakehouse, DynamoDB ledger, and SQS DLQ. | [`01-complete-architecture.mmd`](01-complete-architecture.mmd) | [`01-complete-architecture.md`](01-complete-architecture.md) |
| **02** | [Network Isolation & Zero-Trust](#02--network-isolation--zero-trust-architecture) | VPC endpoints, AWS PrivateLink, Security Group egress controls, and KMS envelope encryption. | [`02-network-zero-trust.mmd`](02-network-zero-trust.mmd) | [`02-network-zero-trust.md`](02-network-zero-trust.md) |
| **03** | [Compute Architecture & Concurrency](#03--compute-architecture--concurrency-tiering) | Step Functions Distributed Map, Lambda Firecracker microVM concurrency, memory-to-vCPU allocation, and scale-to-zero. | [`03-compute-architecture.mmd`](03-compute-architecture.mmd) | [`03-compute-architecture.md`](03-compute-architecture.md) |
| **04** | [End-to-End Pipeline & Data Processing Flow](#04--end-to-end-pipeline--data-processing-flow) | CSV ingestion, dynamic schema inspection, multi-tier entity resolution, Iceberg ACID commit, and ML regression. | [`04-pipeline-flow.mmd`](04-pipeline-flow.mmd) | [`04-pipeline-flow.md`](04-pipeline-flow.md) |
| **05** | [Autoscaling & Event-Driven Concurrency](#05--autoscaling--event-driven-concurrency-lifecycle) | Sub-second cold start (<1.5s), parallel Lambda concurrency burst, and instant scale-to-zero ($0 idle cost). | [`05-autoscaling-lifecycle.mmd`](05-autoscaling-lifecycle.mmd) | [`05-autoscaling-lifecycle.md`](05-autoscaling-lifecycle.md) |
| **06** | [Lambda Execution Environment & MicroVM Topology](#06--lambda-execution-environment--microvm-topology) | Linux kernel cgroups, /tmp ephemeral NVMe storage, Python 3.12 runtime, and memory boundaries. | [`06-lambda-execution-environment.mmd`](06-lambda-execution-environment.mmd) | [`06-lambda-execution-environment.md`](06-lambda-execution-environment.md) |
| **07** | [Zero-Trust Security & Identity Architecture](#07--zero-trust-security--identity-architecture) | IAM execution roles, temporary STS tokens, GitHub Actions OIDC federation, and KMS CMK encryption. | [`07-security-identity.mmd`](07-security-identity.mmd) | [`07-security-identity.md`](07-security-identity.md) |
| **08** | [Observability, Metrics & Centralized Logging](#08--observability-metrics--centralized-logging-architecture) | CloudWatch structured JSON logs, custom metrics namespace, SQS DLQ alarms, and X-Ray distributed tracing. | [`08-observability-telemetry.mmd`](08-observability-telemetry.mmd) | [`08-observability-telemetry.md`](08-observability-telemetry.md) |
| **09** | [Apache Iceberg ACID Lakehouse Storage](#09--apache-iceberg-acid-lakehouse-storage-architecture) | AWS Glue Data Catalog CAS lock, snapshot hierarchy, Snappy Parquet files, and dead-letter quarantine. | [`09-lakehouse-iceberg.mmd`](09-lakehouse-iceberg.mmd) | [`09-lakehouse-iceberg.md`](09-lakehouse-iceberg.md) |
| **10** | [CI/CD Pipeline & GitOps Deployment](#10--cicd-pipeline--gitops-deployment-lifecycle) | Static testing gates, Terraform serverless provisioning, automated smoke tests, and verified outputs. | [`10-cicd-deployment.mmd`](10-cicd-deployment.mmd) | [`10-cicd-deployment.md`](10-cicd-deployment.md) |
| **11** | [Serverless Architectural Blueprint](#11--serverless-architectural-blueprint) | Master Step Functions state machine and 6 micro-functions blueprint. | [`11-serverless-architecture.mmd`](11-serverless-architecture.mmd) | [`11-serverless-architecture.md`](11-serverless-architecture.md) |

---

## 01 — Complete Serverless Architecture

```mermaid
flowchart TD
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

## 02 — Network Isolation & Zero-Trust Architecture

```mermaid
flowchart TD
    subgraph Identity["Identity & Cryptographic Foundations"]
        IAM_LAMBDA["IAM Execution Role: lambda_exec_role\n- Temporary STS Web Identity Token (Rotated Hourly)\n- Scoped to exact S3, DynamoDB, Glue ARNs"]
        IAM_SFN["IAM Execution Role: step_functions_role\n- Restricted to lambda:InvokeFunction\n- Restricted to sqs:SendMessage"]
        KMS["AWS KMS Customer Managed Key (CMK)\n(alias/ray-platform-test-key)"]
    end

    subgraph VPC["AWS Virtual Private Cloud (VPC: 10.0.0.0/16) - Private Subnets"]
        direction TB

        subgraph LambdaVPC["Serverless Compute Isolation"]
            L1["Lambda: Discovery (512MB)"]
            L2["Lambda: Validator (1024MB)"]
            L3["Lambda: Resolver (2048MB)"]
            L4["Lambda: Iceberg Sink (2048MB)"]
            L5["Lambda: ML Trainer (3072MB)"]
            L6["Lambda: Finalizer (512MB)"]
        end

        subgraph SecurityGroup["Security Group: sg-serverless-pipeline"]
            SG["Inbound: NONE (Deny All Ingress)\nOutbound: Port 443 strictly to VPC Endpoints"]
        end

        subgraph Endpoints["AWS PrivateLink VPC Endpoints (Zero Internet Gateway)"]
            VPCE_S3["Amazon S3 Gateway Endpoint\n(com.amazonaws.us-east-1.s3 - $0/GB)"]
            VPCE_DDB["Amazon DynamoDB Gateway Endpoint\n(com.amazonaws.us-east-1.dynamodb - $0/GB)"]
            VPCE_GLUE["AWS Glue Interface Endpoint\n(com.amazonaws.us-east-1.glue)"]
            VPCE_CW["CloudWatch Logs Interface Endpoint\n(com.amazonaws.us-east-1.logs)"]
            VPCE_SQS["Amazon SQS Interface Endpoint\n(com.amazonaws.us-east-1.sqs)"]
            VPCE_KMS["AWS KMS Interface Endpoint\n(com.amazonaws.us-east-1.kms)"]
        end
    end

    subgraph AWS_Services["Target AWS Managed Storage & State"]
        S3[("Amazon S3 Lakehouse Bucket\n- Public Access Block: All 4 True\n- KMS CMK Envelope Encryption\n- Bucket Key Enabled")]
        DDB[("Amazon DynamoDB Ledger\n- KMS CMK Encrypted\n- TLS 1.3 In-Transit")]
        GLUE_CAT[("AWS Glue Data Catalog\n- IAM Authenticated")]
        CW_LOGS["Amazon CloudWatch Logs\n- KMS Encrypted Log Groups"]
        SQS_DLQ["Amazon SQS DLQ\n- KMS Encrypted Queue"]
    end

    IAM_LAMBDA -.->|Attaches STS Token| LambdaVPC
    IAM_SFN -.->|Attaches STS Token| LambdaVPC
    LambdaVPC --- SecurityGroup

    LambdaVPC -->|TLS 1.3 via Gateway| VPCE_S3
    LambdaVPC -->|TLS 1.3 via Gateway| VPCE_DDB
    LambdaVPC -->|TLS 1.3 via PrivateLink| VPCE_GLUE
    LambdaVPC -->|TLS 1.3 via PrivateLink| VPCE_CW
    LambdaVPC -->|TLS 1.3 via PrivateLink| VPCE_SQS
    LambdaVPC -->|TLS 1.3 via PrivateLink| VPCE_KMS

    VPCE_S3 --> S3
    VPCE_DDB --> DDB
    VPCE_GLUE --> GLUE_CAT
    VPCE_CW --> CW_LOGS
    VPCE_SQS --> SQS_DLQ
    VPCE_KMS --> KMS
    KMS -.->|Envelope Encryption| S3
    KMS -.->|Envelope Encryption| DDB
    KMS -.->|Envelope Encryption| CW_LOGS
```

---

## 03 — Compute Architecture & Concurrency Tiering

```mermaid
flowchart TD
    subgraph TriggerSource["Trigger Sources"]
        EVENT["EventBridge Trigger / S3 PutObject"]
        CLI["AWS CLI / API Gateway Manual Start"]
    end

    subgraph StateMachine["AWS Step Functions (Orchestration Engine)"]
        SF_EXEC["Step Functions Execution Engine\n- State: RUNNING\n- Evaluates ASL JSON\n- Manages Context & Payload Passing"]
    end

    subgraph ComputeTier["AWS Lambda Micro-Function Compute Tier (Firecracker MicroVMs)"]
        direction TB

        subgraph F1["Stage 1: Discovery MicroVM"]
            M1["Memory: 512 MB\nCPU: ~0.3 vCPU\nTimeout: 60s\nEphemeral: 512 MB /tmp\nRole: SHA256 Hash + DynamoDB Claim"]
        end

        subgraph F2["Stage 2: Parallel Ingestion (Distributed Map)"]
            direction LR
            M2_A["Lambda MicroVM A (S1)\nMemory: 1024 MB (~0.6 vCPU)\nTimeout: 120s\nTask: Supply Chain CSV Normalization"]
            M2_B["Lambda MicroVM B (S2)\nMemory: 1024 MB (~0.6 vCPU)\nTimeout: 120s\nTask: Financial CSV Normalization"]
        end

        subgraph F3["Stage 3: Multi-Tier Entity Resolution MicroVM"]
            M3["Memory: 2048 MB\nCPU: ~1.2 vCPU\nTimeout: 300s\nEphemeral: 2048 MB /tmp\nRole: Pairwise Tax ID + Fuzzy Levenshtein (>= 0.88)"]
        end

        subgraph F4["Stage 4: Apache Iceberg Sink MicroVM"]
            M4["Memory: 2048 MB\nCPU: ~1.2 vCPU\nTimeout: 300s\nRole: PyIceberg ACID Upsert + Glue CAS Commit"]
        end

        subgraph F5["Stage 5: ML Regressor Training MicroVM"]
            M5["Memory: 3072 MB\nCPU: ~1.8 vCPU (High Clock Speed)\nTimeout: 600s\nRole: Gradient Boosting Regressor (R^2 >= 0.85)"]
        end

        subgraph F6["Stage 6: Finalizer & Telemetry MicroVM"]
            M6["Memory: 512 MB\nCPU: ~0.3 vCPU\nTimeout: 60s\nRole: Mark Ledger COMPLETED + Emit Metrics"]
        end
    end

    subgraph ScaleToZero["Instant Scale-to-Zero"]
        COMPLETE(["Execution Finishes"])
        ZERO_COST["All 6 MicroVMs Terminate\nActive vCPUs: 0\nActive Memory: 0 MB\nHourly Cost: $0.0000"]
    end

    EVENT --> SF_EXEC
    CLI --> SF_EXEC

    SF_EXEC --> M1
    M1 --> M2_A
    M1 --> M2_B
    M2_A --> M3
    M2_B --> M3
    M3 --> M4
    M4 --> M5
    M5 --> M6
    M6 --> COMPLETE
    COMPLETE --> ZERO_COST
```

---

## 04 — End-to-End Pipeline & Data Processing Flow

```mermaid
flowchart TD
    subgraph RawData["Raw Ingestion Datasets (2,400 Total Rows)"]
        S1["supply_chain_data_s1.csv\n(1,200 records - Heterogeneous Columns)"]
        S2["financial_data_s2.csv\n(1,200 records - Heterogeneous Columns)"]
    end

    subgraph Step1["Stage 1: Discovery & Idempotency Check"]
        CALC_HASH["Compute SHA256(S1_URI + S2_URI)\nGenerate ExecutionID: sfn-run-<sha256[:16]>"]
        DDB_CLAIM{"DynamoDB PutItem\nCondition: attribute_not_exists(execution_id)"}
        EXISTS["Duplicate Execution Detected\n-> Exit Gracefully with Cached Status"]
        CLAIMED["Ledger Initialized: status=CLAIMED"]
    end

    subgraph Step2["Stage 2: Parallel Dynamic Schema Validation (Distributed Map)"]
        direction TB
        MAP_BRANCH["Step Functions Distributed Map (MaxConcurrency: 5)"]
        NORM_HEADERS["Case-Insensitive Column Alias Detection:\n['corporate_name', 'company_name'] -> entity_name\n['tax_identifier', 'ein'] -> tax_id\n['annual_revenue', 'revenue_usd'] -> annual_revenue"]
        CLEANSE["Type Coercion & Data Cleansing:\n- Strip currency symbols\n- Parse founded year\n- Uppercase ISO country code"]
        PYDANTIC["Validate Pydantic Model (CorporateRecordInput)"]
        VALID_RECS["Normalized In-Memory Records:\n- S1: 1,200 Valid\n- S2: 1,200 Valid"]
    end

    subgraph Step3["Stage 3: Multi-Tier Deterministic Entity Resolution"]
        COLLECT["Aggregate 2,400 Valid Ingested Records"]
        
        subgraph MatchingEngine["EntityResolverEngine Algorithm"]
            TIER1{"Tier 1: Exact Tax ID Match?\n(Confidence: 1.00)"}
            TIER2{"Tier 2: Normalized Levenshtein >= 0.88\n+ Country Match + |Year Diff| <= 1?\n(Confidence: 0.92)"}
            AMBIG{"Ambiguity Threshold?\n(0.65 <= Similarity < 0.88)"}
            NEW_ENT["Distinct Entity Created\n(UUIDv5 Canonical ID: COMP-XXXXXXXX)"]
        end

        CANONICAL["1,557 Canonical Merged Entities\n(Enriched with Corroborated Fields)"]
        QUARANTINE["711 Ambiguous Records\n-> Divert to s3://.../quarantine/"]
    end

    subgraph Step4["Stage 4: Apache Iceberg Lakehouse Persistence"]
        PYICEBERG["PyIceberg Arrow Table Construction"]
        WRITE_PARQUET["Write Snappy-Compressed Parquet Data Files"]
        COMMIT_SNAPSHOT["Atomic CAS Commit to AWS Glue Catalog\n- Snapshot ID: e.g. 356891083480308578\n- ACID Transaction Guarantees"]
    end

    subgraph Step5["Stage 5: Gradient Boosting Regressor Training"]
        EXTRACT_FEATURES["Feature Engineering:\n- Age = CurrentYear - FoundedYear\n- Employee Count\n- Resolution Confidence Score\n- Target: log1p(annual_revenue)"]
        TRAIN_EVAL["Train GradientBoostingRegressor (100 Trees, LR: 0.1)\nEvaluate 80/20 Train/Test Split"]
        ASSERT_R2{"Test R^2 >= 0.85?\n(Achieved: 0.8725)"}
        SAVE_MODEL["Serialize revenue_model.joblib & metrics.json to S3"]
    end

    subgraph Step6["Stage 6: Finalization & Audit Telemetry"]
        UPDATE_DDB["Update DynamoDB Ledger:\n- status = COMPLETED\n- canonical_entities = 1557\n- iceberg_snapshot_id = 356891083480308578\n- model_r2_score = 0.8725"]
        EMIT_CW["Emit Custom CloudWatch Metrics & JSON Summary"]
    end

    S1 --> CALC_HASH
    S2 --> CALC_HASH
    CALC_HASH --> DDB_CLAIM
    DDB_CLAIM -->|Already Exists| EXISTS
    DDB_CLAIM -->|New Lease| CLAIMED
    CLAIMED --> MAP_BRANCH

    MAP_BRANCH --> NORM_HEADERS
    NORM_HEADERS --> CLEANSE
    CLEANSE --> PYDANTIC
    PYDANTIC --> VALID_RECS
    VALID_RECS --> COLLECT

    COLLECT --> TIER1
    TIER1 -->|Match| CANONICAL
    TIER1 -->|No Match| TIER2
    TIER2 -->|Match| CANONICAL
    TIER2 -->|No Match| AMBIG
    AMBIG -->|Ambiguous| QUARANTINE
    AMBIG -->|No Similarity| NEW_ENT
    NEW_ENT --> CANONICAL

    CANONICAL --> PYICEBERG
    PYICEBERG --> WRITE_PARQUET
    WRITE_PARQUET --> COMMIT_SNAPSHOT
    COMMIT_SNAPSHOT --> EXTRACT_FEATURES

    EXTRACT_FEATURES --> TRAIN_EVAL
    TRAIN_EVAL --> ASSERT_R2
    ASSERT_R2 -->|Pass| SAVE_MODEL
    SAVE_MODEL --> UPDATE_DDB
    UPDATE_DDB --> EMIT_CW
```

---

## 05 — Autoscaling & Event-Driven Concurrency Lifecycle

```mermaid
flowchart TD
    subgraph IdleState["1. Idle State (Zero Workload Demand)"]
        IDLE_SFN["Step Functions: IDLE\nActive Executions: 0"]
        IDLE_LAMBDA["Lambda Compute Fleet: SCALE-TO-ZERO\nActive MicroVMs: 0\nActive vCPUs: 0 | Active RAM: 0 MB"]
        IDLE_COST["Billed Compute Cost: $0.000000 / hour"]
    end

    subgraph BurstTrigger["2. Ingestion Burst Event"]
        EVENT["EventBridge Cron / S3 PutObject Arrival"]
        TRIGGER_EXEC["Step Functions: StartExecution\nExecution State: RUNNING"]
    end

    subgraph RapidScaling["3. Sub-Second Concurrency Scaling (< 1.5s)"]
        WARMUP["Firecracker MicroVM Initialization (< 1.2s cold start)"]
        MAP_BURST["Step Functions Distributed Map Scales Out:\n- Spawns Lambda MicroVM 1 (S1 Validator)\n- Spawns Lambda MicroVM 2 (S2 Validator)\nConcurrency: 2 parallel microVMs"]
    end

    subgraph StageExecution["4. Dynamic Sequential Stage Transitions"]
        STAGE_RES["Resolution Stage: 1 MicroVM (2048 MB, ~1.2 vCPU)\nProcesses 2,400 Records in ~28s"]
        STAGE_SINK["Iceberg Sink Stage: 1 MicroVM (2048 MB, ~1.2 vCPU)\nCommits Lakehouse Snapshot in ~1.1s"]
        STAGE_TRAIN["Training Stage: 1 MicroVM (3072 MB, ~1.8 vCPU)\nTrains Gradient Boosting Regressor in ~2.2s"]
        STAGE_FIN["Finalizer Stage: 1 MicroVM (512 MB)\nMarks Ledger COMPLETED in ~280ms"]
    end

    subgraph CompleteScaleZero["5. Immediate Scale-to-Zero Termination"]
        CLEANUP["Function Handlers Return 200 OK\nContext Flushed to CloudWatch"]
        TERMINATE["MicroVMs Terminate Instantly\nActive Concurrency Drops: 2 -> 1 -> 0\nNo 10-Minute Idle Waiting"]
        ZERO_RETURN["Platform Returns to $0.00 Idle Baseline"]
    end

    IDLE_LAMBDA --> EVENT
    EVENT --> TRIGGER_EXEC
    TRIGGER_EXEC --> WARMUP
    WARMUP --> MAP_BURST
    MAP_BURST --> STAGE_RES
    STAGE_RES --> STAGE_SINK
    STAGE_SINK --> STAGE_TRAIN
    STAGE_TRAIN --> STAGE_FIN
    STAGE_FIN --> CLEANUP
    CLEANUP --> TERMINATE
    TERMINATE --> ZERO_RETURN
    ZERO_RETURN --> IDLE_LAMBDA
```

---

## 06 — Lambda Execution Environment & MicroVM Topology

```mermaid
flowchart TD
    subgraph Host["AWS Bare-Metal Server (Nitro System)"]
        KVM["Linux Kernel-Based Virtual Machine (KVM)"]

        subgraph FirecrackerVM["Isolated AWS Firecracker MicroVM"]
            direction TB

            subgraph MicroVMKernel["MicroVM Dedicated Linux Kernel (v6.x)"]
                CGROUPS["Linux cgroups v2 (CPU Quotas & Memory Enforcers)"]
                SECCOMP["seccomp Filter (Restricted Syscall Boundary)"]
            end

            subgraph StorageBoundaries["Ephemeral Storage & Memory Boundaries"]
                TMP_DISK["Ephemeral Disk: /tmp (512 MB to 2,048 MB)\n- Inode space for PyIceberg local cache\n- Scratch storage for serialized joblib model artifacts"]
                HEAP_MEM["Hardware-Enforced RAM: 512 MB to 3,072 MB\n- In-Memory PyArrow Table Buffer\n- Python 3.12 Process Heap"]
            end

            subgraph RuntimeEnvironment["Language Runtime & Worker Process"]
                INIT_SYS["AWS Lambda Runtime Bootstrap Engine (Rapid)"]
                PY_RUNTIME["Python 3.12 Managed Execution Engine"]

                subgraph LoadedLibraries["Pre-Warmed In-Memory Data Science Engines"]
                    LIB_PYICEBERG["PyIceberg (ACID Lakehouse Client)"]
                    LIB_SKLEARN["Scikit-Learn (GradientBoostingRegressor)"]
                    LIB_ARROW["Apache Arrow (PyArrow Columnar Memory)"]
                    LIB_PANDAS["Pandas DataFrames"]
                    LIB_BOTO3["AWS SDK (boto3 - S3/DynamoDB/Glue/SQS)"]
                end

                subgraph HandlerSlot["Invoked Handler Execution Slot"]
                    HANDLER["handlers.py Entry Point:\n- handler_discovery\n- handler_validator\n- handler_resolver\n- handler_iceberg_sink\n- handler_trainer\n- handler_finalizer"]
                end
            end

            subgraph TelemetryAgent["Telemetry & Log Forwarding"]
                LOG_AGENT["CloudWatch Logs Streaming Daemon\n(Structured JSON Log Buffer)"]
            end
        end
    end

    KVM --> FirecrackerVM
    CGROUPS --> HEAP_MEM
    SECCOMP --> RuntimeEnvironment
    INIT_SYS --> PY_RUNTIME
    PY_RUNTIME --> LoadedLibraries
    LoadedLibraries --> HANDLER
    HANDLER --> TMP_DISK
    HANDLER --> HEAP_MEM
    HANDLER --> LOG_AGENT
```

---

## 07 — Zero-Trust Security, Identity & Cryptographic Architecture

```mermaid
flowchart TD
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

## 08 — Observability, Metrics & Centralized Logging Architecture

```mermaid
flowchart TD
    subgraph ExecutionPlane["Serverless Workload Execution"]
        SFN["AWS Step Functions State Machine\n(Detailed Execution History & Step Transitions)"]
        L1["Lambda: Discovery (512MB)"]
        L2["Lambda: Validator (1024MB)"]
        L3["Lambda: Resolver (2048MB)"]
        L4["Lambda: Iceberg Sink (2048MB)"]
        L5["Lambda: ML Trainer (3072MB)"]
        L6["Lambda: Finalizer (512MB)"]
        DLQ["Amazon SQS Dead-Letter Queue (DLQ)"]
    end

    subgraph CentralizedTelemetry["Amazon CloudWatch Observability Suite"]
        direction TB

        subgraph LogStreams["Structured JSON Log Groups (14-Day Retention)"]
            CW_L1["/aws/lambda/sfn-corporate-discovery"]
            CW_L2["/aws/lambda/sfn-corporate-validator"]
            CW_L3["/aws/lambda/sfn-corporate-resolver"]
            CW_L4["/aws/lambda/sfn-corporate-iceberg-sink"]
            CW_L5["/aws/lambda/sfn-corporate-trainer"]
            CW_L6["/aws/lambda/sfn-corporate-finalizer"]
        end

        subgraph CustomMetrics["CloudWatch Custom Metrics Namespace: CorporatePlatform"]
            M_DUR["Metric: PipelineExecutionDuration (Seconds)"]
            M_CAN["Metric: CanonicalEntitiesCount (1557)"]
            M_QUAR["Metric: QuarantinedEntitiesCount (711)"]
            M_R2["Metric: ModelR2Score (0.8725)"]
            M_SNAP["Metric: IcebergSnapshotID"]
        end

        subgraph Alarms["Operational Alarms & DLQ Alerts"]
            ALARM_DLQ["CloudWatch Alarm: SQS_DLQ_Messages_Present\nThreshold: VisibleMessages > 0"]
            ALARM_FAIL["CloudWatch Alarm: StepFunctions_Execution_Failed\nThreshold: FailedExecutions >= 1"]
        end

        subgraph XRay["AWS X-Ray Distributed Tracing"]
            TRACE["End-to-End Execution Trace Map:\nStep Functions -> Lambda Invocations -> S3/DynamoDB SDK Calls"]
        end
    end

    subgraph Dashboards["Platform Operator Visualization"]
        CW_DASH["CloudWatch Executive Dashboard:\n- End-to-end pipeline duration trends\n- Entity deduplication yield over time\n- Revenue ML model test R^2 scores"]
        SNS_ALERT["Amazon SNS Notification\n(Alerts On-Call Platform Engineer)"]
    end

    L1 --> CW_L1
    L2 --> CW_L2
    L3 --> CW_L3
    L4 --> CW_L4
    L5 --> CW_L5
    L6 --> CW_L6

    L6 --> M_DUR
    L6 --> M_CAN
    L6 --> M_QUAR
    L6 --> M_R2
    L6 --> M_SNAP

    SFN -.-> TRACE
    L1 -.-> TRACE
    L3 -.-> TRACE
    L5 -.-> TRACE

    DLQ --> ALARM_DLQ
    SFN --> ALARM_FAIL

    ALARM_DLQ --> SNS_ALERT
    ALARM_FAIL --> SNS_ALERT
    CustomMetrics --> CW_DASH
```

---

## 09 — Apache Iceberg ACID Lakehouse Storage Architecture

```mermaid
flowchart TD
    subgraph ComputeEngines["Serverless Compute & Analytics Engines"]
        LAMBDA_SINK["AWS Lambda: handler_iceberg_sink\n(PyIceberg ACID Lakehouse Writer)"]
        ATHENA["Amazon Athena\n(Serverless SQL Query Engine)"]
    end

    subgraph CatalogLayer["Metastore & Transactional Lock Manager"]
        GLUE_CATALOG[("AWS Glue Data Catalog\nDatabase: corporate_data_db\nTable: corporate_registry\n- Atomic CAS Commit Lock\n- Points to Current Snapshot Metadata")]
    end

    subgraph S3_MetadataTree["S3 Iceberg Metadata Tree (iceberg-warehouse/corporate_registry/metadata/)"]
        direction TB

        META_JSON["Table Metadata File (v2.metadata.json)\n- Schema Definition & Field IDs\n- Partition Spec\n- Snapshot History & Current Snapshot ID"]

        SNAP_LIST["Manifest List File (snap-356891083480308578.avro)\n- List of Manifest Files\n- Snapshot Summary & Added/Deleted Counts\n- Partition Bounds for Fast Pruning"]

        subgraph ManifestFiles["Manifest Files (.avro)"]
            M1["Manifest File 1 (m1.avro)\n- File Paths\n- Column Min/Max Stats\n- Null Counts & Row Counts"]
        end
    end

    subgraph S3_DataFiles["S3 Data Files (iceberg-warehouse/corporate_registry/data/)"]
        PARQUET_1["Parquet Data File 1\n(part-00000-snappy.parquet)\n- Snappy Compressed\n- Dictionary Encoded\n- 1,557 Canonical Entities"]
    end

    subgraph QuarantineStorage["Anomaly Dead-Letter Isolation Pool"]
        S3_QUARANTINE[("S3: quarantine/ambiguous_entities/\n- Ambiguous Match Ratio (0.65 - 0.87)\n- 711 Quarantined Corporate Records\n- Completely Isolated from Lakehouse")]
    end

    LAMBDA_SINK -->|"1. Read Current Metadata Pointer"| GLUE_CATALOG
    ATHENA -->|"1. Read Current Metadata Pointer"| GLUE_CATALOG
    GLUE_CATALOG -->|"2. Return Pointer to v2.metadata.json"| META_JSON
    META_JSON -->|"3. References Current Snapshot"| SNAP_LIST
    SNAP_LIST -->|"4. Reads Partition Summaries"| M1
    M1 -->|"5. Predicate Pushdown Pruning"| PARQUET_1

    LAMBDA_SINK -->|"6a. Stage New Data Files"| S3_DataFiles
    LAMBDA_SINK -->|"6b. Write New Manifest & Snapshot"| S3_MetadataTree
    LAMBDA_SINK -->|"6c. Atomic CAS Lock Commit"| GLUE_CATALOG
    LAMBDA_SINK -.->|"Divert Ambiguities"| S3_QUARANTINE
```

---

## 10 — CI/CD Pipeline & GitOps Deployment Lifecycle

```mermaid
flowchart TD
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

## 11 — Serverless Architectural Blueprint

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
