# 03 — Compute Architecture & Concurrency Tiering (Serverless Alternative)

This document provides the compute sizing, concurrency model, and microVM lifecycle for the **AWS Serverless Platform**.

---

## 1. Architectural Diagram

```mermaid
flowchart TD
    %% Serverless Compute Architecture Diagram
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

## 2. Compute Allocation & Sizing Specifications

| Stage | Lambda Function | Memory | Sized vCPU | Max Timeout | Ephemeral Storage | Compute Category |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Stage 1** | `sfn-corporate-discovery` | 512 MB | ~0.3 vCPU | 60s | 512 MB | I/O Bound (SHA256, DDB Claim) |
| **Stage 2** | `sfn-corporate-validator` | 1,024 MB | ~0.6 vCPU | 120s | 1,024 MB | Mixed I/O & Parsing (CSV Ingest) |
| **Stage 3** | `sfn-corporate-resolver` | 2,048 MB | ~1.2 vCPU | 300s | 2,048 MB | Memory & CPU Intensive (Levenshtein) |
| **Stage 4** | `sfn-corporate-iceberg-sink` | 2,048 MB | ~1.2 vCPU | 300s | 2,048 MB | Memory & Parquet I/O (Iceberg commit) |
| **Stage 5** | `sfn-corporate-trainer` | 3,072 MB | ~1.8 vCPU | 600s | 2,048 MB | High Compute (Gradient Boosting ML) |
| **Stage 6** | `sfn-corporate-finalizer` | 512 MB | ~0.3 vCPU | 60s | 512 MB | I/O Bound (DDB Update, Metrics) |

---

## 3. Scale-to-Zero Efficiency

Unlike Kubernetes worker nodes that continue drawing power and incurring billing while waiting for scale-down timers (e.g. 10 minutes), AWS Lambda microVMs terminate the exact millisecond the return statement executes. Idle cost between runs is strictly **$0.0000**.
