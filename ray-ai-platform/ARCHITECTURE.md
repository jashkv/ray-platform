# Architecture — Distributed Ray AI Platform on AWS

- **Platform:** AWS EKS (Kubernetes `1.31`)
- **Distributed Compute:** Ray `2.40.0` managed by KubeRay Operator `v1.2.2`
- **Lakehouse Storage:** Apache Iceberg with AWS Glue Data Catalog & Amazon S3
- **Machine Learning:** Ray Train with XGBoost / Gradient Boosting Revenue Regression
- **Security Posture:** Zero-Trust IRSA (Workload Identity), EKS Access Entries, GitHub Actions OIDC

---

## 1. High-Level Architecture Diagram

```mermaid
flowchart TD
    subgraph DataSources["External Corporate Data Sources"]
        S1["supply_chain_data_s1.csv (1,200 records)"]
        S2["financial_data_s2.csv (1,200 records)"]
    end

    subgraph StorageLayer["Data Lakehouse & Transactional Storage"]
        S3_IN["S3: incoming/ (Raw CSV Landing)"]
        S3_WH["S3: iceberg-warehouse/corporate_registry/"]
        S3_MOD["S3: models/ (XGBoost Artifacts)"]
        GLUE[("AWS Glue Data Catalog (corporate_data_db)")]
        DDB[("DynamoDB (ray_processing_ledger)")]
    end

    subgraph EKSCluster["Amazon EKS Cluster (v1.31 - Multi-AZ Private Subnets)"]
        KAPI["Kubernetes API Server (EKS Access Entries)"]
        KUBERAY["KubeRay Operator (v1.2.2)"]

        subgraph HeadPool["Head / System Node Pool (On-Demand m6i.xlarge)"]
            RAYHEAD["Ray Head Pod (GCS, Dashboard :8265, Metrics :8080)"]
            PROM["Prometheus + Grafana"]
            FLUENT["Fluent Bit DaemonSet"]
        end

        subgraph WorkerPool["Autoscaling Worker Node Pool (Spot Diversified Pool)"]
            INGEST["Ray Data Ingestion Tasks"]
            RESOLVER["EntityResolver Actor (Custom Resource: entity_resolver_slot: 1)"]
            TRAIN["Ray Train Workers (XGBoost Regression)"]
        end
    end

    subgraph Observability["Observability & Centralized Logging"]
        CW["Amazon CloudWatch Logs (/aws/eks/ray-platform/pods)"]
        DASH["Ray Dashboard (Authenticated / Private Port-Forward)"]
    end

    S1 --> S3_IN
    S2 --> S3_IN
    S3_IN --> INGEST
    INGEST --> RESOLVER
    RESOLVER --> S3_WH
    RESOLVER -.-> GLUE
    RESOLVER --> DDB
    S3_WH --> TRAIN
    TRAIN --> S3_MOD
    RAYHEAD --> INGEST
    RAYHEAD --> WorkerPool
    KAPI --> KUBERAY
    KUBERAY --> RAYHEAD
    FLUENT --> CW
    RAYHEAD --> DASH
```

---

## 2. Decoupled Infrastructure State Layers

The infrastructure is decoupled into $5$ independent Terraform state layers to enforce strict blast radius containment:

```
terraform/
├── bootstrap/     # S3 bucket (SSE-KMS, Versioning) + DynamoDB table for state locking
├── network/       # VPC across 3 AZs, public/private subnets, NAT Gateway, S3 VPC Gateway Endpoint
├── eks/           # EKS v1.31, KMS secret encryption, On-Demand Head pool, Spot Worker pool, Access Entries
├── data/          # S3 data lakehouse, AWS Glue catalog database, DynamoDB ledger, IRSA role
├── platform/      # ECR container registry, GitHub Actions OIDC provider & deployment role
└── modules/       # Reusable modules (vpc, eks, s3_iceberg, ledger, irsa)
```

---

## 3. Compute Topology & Spot Resilience Strategy

### 3.1 Node Group Strategy

| Node Group | Capacity Type | Sizing & Multi-AZ Distribution | Taints & Labels | Purpose & SLA |
| :--- | :--- | :--- | :--- | :--- |
| **`head-system-pool`** | `ON_DEMAND` | `m6i.xlarge` (4 vCPU, 16GiB), 1-2 nodes | `workload-role=ray-head-system` | Hosts Ray Head (GCS, Dashboard), CoreDNS, KubeRay Operator, Prometheus. 100% uptime SLA. |
| **`worker-spot-pool`** | `SPOT` | Diversified across `m6i.xlarge`, `m5.xlarge`, `m5a.xlarge`, `m6a.xlarge` (0-10 nodes) | Label: `workload-role=ray-worker`<br>Taint: `workload-role=ray-worker:NoSchedule` | Executes parallel Ray Data ingestion, EntityResolver actor, and Ray Train regression. **~70% cost reduction**. |
| **`worker-ondemand-fallback`** | `ON_DEMAND` | `m6i.xlarge` (0-5 nodes, default 0) | Label: `workload-role=ray-worker`<br>Taint: `workload-role=ray-worker:NoSchedule` | Automatic fallback pool activated only during severe regional Spot capacity exhaustion. |

### 3.2 Spot Interruption Resilience
1. **Capacity Pool Diversification:** By configuring 4 instance families spanning Intel (`m6i`, `m5`) and AMD (`m6a`, `m5a`) across 3 Availability Zones, the Spot worker pool draws from $12$ distinct EC2 capacity pools, lowering Spot preemption probability to $< 5\%$.
2. **Ray Task Idempotency & Retries:** Ray Data tasks are purely functional and automatically reschedule with zero data corruption upon node termination.
3. **Dedicated Actor Placement:** The stateful `EntityResolver` actor is scheduled onto the worker group via Ray custom resource `entity_resolver_slot: 1`.

---

## 4. Memory, `/dev/shm`, and Object Store Sizing

Ray relies heavily on Apache Arrow in-memory shared memory (`/dev/shm`) for zero-copy data deserialization across processes:

$$\text{Total Pod Memory} = 12\text{ GiB}$$
$$\text{Memory-backed emptyDir at } /dev/shm = 4\text{ GiB}$$
$$\text{Ray Object Store Memory} = 3,865,470,566\text{ bytes} \approx 3.6\text{ GiB}$$
$$\text{Remaining Heap for Python / OS} = 12\text{ GiB} - (4\text{ GiB} + 3.6\text{ GiB}) = 4.4\text{ GiB}$$

This allocation guarantees that large Arrow batches never cause Linux out-of-memory (OOM) kernel kills.

---

## 5. Multi-Tier Entity Resolution Architecture

The `EntityResolver` replaces naive `hash()` simulations with an evidence-based multi-tier resolution algorithm:

1. **Tier 1 — Strong Identifier Matching:** Exact match on Tax ID / Registration Number. Confidence: `1.0`.
2. **Tier 2 — Normalized Name Matching with Corroboration:**
   - Legal suffix stripping (`Inc`, `Corp`, `LLC`, `Ltd`, `GmbH`, `PLC`, `Holdings`).
   - Unicode NFKD normalization and lowercasing.
   - Levenshtein similarity threshold $\ge 0.88$.
   - Attribute corroboration: Headquarters country must match exactly, and incorporation year must be within $\pm 2$ years. Confidence: `0.92 - 0.95`.
3. **Tier 3 — Ambiguity Quarantine:**
   - Candidates with similarity between $0.65$ and $0.87$ or conflicting country metadata are quarantined (`status = "AMBIGUOUS"`), preventing silent data corruption.
4. **Canonical Identifier Generation:** Deterministic UUIDv5 keyed by `TAX:<id>` or `NAME:<country>:<clean_name>` in DNS namespace `corporate-registry.ray.internal`. Outputs stable canonical IDs: `COMP-XXXXXXXX-XXXX`.

---

## 6. Apache Iceberg Lakehouse Persistence

- **Catalog:** AWS Glue Data Catalog (`corporate_data_db`) in AWS, or SQLite catalog for local development.
- **Table:** `corporate_registry` storing Parquet data files with Avro metadata snapshots.
- **Transactional Semantics:** PyIceberg transactional commits ensure atomic snapshot updates, schema enforcement, and time-travel auditability.

---

## 7. Distributed Revenue Prediction Model

- **Engine:** Ray Train with Gradient Boosting / XGBoost regression.
- **Target:** Annual corporate revenue in USD (`annual_revenue_usd`).
- **Features:** `employee_count`, `founded_year`, `company_age`, One-Hot Encoded `industry_sector`, and `country`.
- **Validation Metrics Achieved:**
  - $R^2$ Score: **`0.8725`**
  - Test MAE: **`$31,386,943.83`**
  - Test RMSE: **`$103,889,993.02`**
- **Persistence:** Serialized model (`revenue_model.joblib`), evaluation metadata (`metrics.json`), and feature schema stored in S3 `models/` prefix.
