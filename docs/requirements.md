# Enterprise Ray & Serverless AI Platform — Architecture & System Requirements Specification

- **Document ID:** SPEC-RAY-SERVERLESS-DATA-ML-01
- **Status:** APPROVED & BASELINE SPECIFICATION
- **Target Compute Platforms:**
  - **Kubernetes / Ray (Primary):** Amazon Web Services (AWS) EKS 1.31 / Distributed Ray 2.40.0
  - **Serverless (Alternative):** AWS Step Functions / AWS Lambda / Apache Iceberg Lakehouse
- **Authors:** Platform Engineering & Distributed Data Infrastructure Teams

---

## 1. Executive Summary & Purpose

The **Distributed AI Platform** is an enterprise data and distributed machine learning foundation deployed on Amazon Web Services (AWS). It establishes an automated, event-driven data lakehouse pipeline that continuously ingests corporate datasets in CSV format from disparate source systems, resolves multi-source corporate records to canonical entities using evidence-based deterministic algorithms, maintains an ACID-compliant enterprise corporate registry in Apache Iceberg, and trains distributed revenue prediction models.

This document establishes the binding functional requirements, architectural boundaries, and non-functional specifications governing the infrastructure, data engineering pipelines, compute elasticity, and security posture across both the **Ray on Kubernetes (Amazon EKS)** and **AWS Serverless Alternative (Step Functions + Lambda)** implementations.

---

## 2. Business Problem & Domain Context

Enterprises frequently ingest company-level data from multiple heterogeneous systems (e.g., enterprise resource planning, vendor supply-chain platforms, credit agencies, and audited financial filings). These incoming datasets present severe data quality and distributed processing challenges:

1. **Entity Collision & Name Variation:** Identical corporate entities appear with divergent legal suffixes (e.g., *Corp*, *Corporation*, *LLC*, *GmbH*, *Holdings*), variable capitalization, typographical errors, and missing strong identifiers.
2. **Complementary & Conflicting Attributes:** Supply chain records contain spend volume and operational risk metrics, while financial records contain audited annual revenues, balance sheet metrics, and credit ratings.
3. **Data Volume & Parallel Processing:** Large enterprise CSV batches requiring low-latency parallel processing exceed single-node memory and CPU limits.
4. **Transaction Integrity & Schema Evolution:** Concurrent updates require atomic snapshot isolation, preventing dirty reads or lost updates in downstream analytics and ML training sets.
5. **Predictive Downstream ML:** Data science teams require clean, harmonized canonical feature matrices to train regression models that predict corporate annual revenue.

---

## 3. Core Functional Requirements

### FR-01: Disparate Dataset Ingestion & Validation
- **Requirement:** The platform must ingest corporate CSV datasets from multiple independent sources.
- **Specification:**
  - Standard reference datasets include `supply_chain_data_s1.csv` and `financial_data_s2.csv`, each containing at least $\ge 1,000$ discrete corporate records.
  - Strict Pydantic v2 schemas (`SupplyChainInputRecord`, `FinancialInputRecord`) enforce field-level constraints, non-negative employee counts, positive founded years, and non-null revenue representations.
  - Malformed or structurally corrupted rows must be quarantined with error context and excluded from corrupting the lakehouse without stopping the pipeline.

### FR-02: Event-Driven Pipeline Trigger & Idempotent Ledger
- **Requirement:** Workload execution must trigger automatically upon data availability without manual human intervention, backed by strict idempotency guarantees.
- **Specification:**
  - Ingestion triggers via Amazon EventBridge.
  - An atomic transactional ledger in Amazon DynamoDB (`ray_processing_ledger`) records file SHA256 checksums, execution lease tokens, and timestamped lifecycle states (`CLAIMED`, `PROCESSING`, `COMPLETED`, `FAILED`).
  - Duplicate events or retried submissions within a 24-hour lease window are rejected safely, preventing duplicate compute runs or double-processing.

### FR-03: Multi-Tier Deterministic Entity Resolution
- **Requirement:** The platform must deterministically resolve records referring to the same real-world corporate entity without reliance on fragile non-deterministic hash functions.
- **Specification:**
  - **Tier 1 (Strong Identifier Matching):** Exact matching on standardized National Tax Identifiers / Corporate Registration Numbers ($1.00$ confidence).
  - **Tier 2 (Corroborated Normalized Similarity):** Strips legal suffixes, normalizes Unicode NFKD, and computes Levenshtein edit distance ($s \ge 0.88$) corroborated by geographic boundary (headquarters country) and incorporation date ($\pm 2$ years).
  - **Tier 3 (Ambiguity Quarantine):** Records exhibiting similarity between $0.65$ and $0.87$, or high name similarity with conflicting countries, are quarantined for governance review.
  - **Tier 4 (Canonical Identity Generation):** Resolved entities receive an immutable, deterministic UUIDv5 identifier (`COMP-XXXXXXXX-XXXX`) salted with the platform's internal DNS namespace.

### FR-04: ACID Lakehouse Persistence (Apache Iceberg)
- **Requirement:** Harmonized corporate records must be persisted into an Apache Iceberg table (`corporate_registry`) with full ACID semantics.
- **Specification:**
  - Implemented via PyIceberg with AWS Glue Data Catalog integration for AWS production, and deterministic SQLite catalog for local hermetic verification.
  - Commits generate verifiable snapshot IDs, write Parquet data files with gzip/snappy compression, and support schema evolution and time travel.
  - Commits are verified programmatically by asserting snapshot lineage and exact row counts immediately post-commit.

### FR-05: Machine Learning & Model Evaluation
- **Requirement:** Harmonized canonical entities must be converted into feature matrices to train and evaluate a revenue prediction regression model.
- **Specification:**
  - Model fitting executes via Gradient Boosting / Ray Train regressor predicting annual revenue in USD.
  - Features include employee count, founded year, company age, one-hot encoded industry sector, and country.
  - Evaluation requires held-out test splits ($20\%$), reporting Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and Coefficient of Determination ($R^2 \ge 0.70$, empirical $R^2 = 0.8725$).
  - Model weights (`revenue_model.joblib`) and metrics metadata (`metrics.json`) are versioned and exported to Amazon S3.

---

## 4. Compute Architecture Implementations

The platform delivers two interchangeable, production-grade compute implementations operating against identical data contracts and Iceberg lakehouses:

| Architectural Dimension | Primary: Ray on AWS EKS | Alternative: AWS Serverless |
| :--- | :--- | :--- |
| **Compute Engine** | Distributed Ray Cluster (Head + Worker Pods) | AWS Step Functions + AWS Lambda |
| **Orchestrator** | KubeRay Operator (`v1.2.2`) | AWS Step Functions (Standard Workflow) |
| **Parallel Processing** | Ray Data (`Dataset.map_batches`) | Step Functions Distributed Map |
| **Stateful Deduplication** | Ray Actor (`EntityResolver`) with Custom Resource Placement | Lambda Memory Context / DynamoDB Caching |
| **Autoscaling** | Karpenter v1 (Spot + On-Demand NodePools) | Native AWS Serverless Auto-Concurrency |
| **Cold Start Overhead** | 0s (Dedicated System Node) / 45s (Karpenter Node Scale-Out) | 200ms–800ms (Lambda Container / Runtime Init) |
| **Idle Cost** | ~$245/month (EKS Control Plane + On-Demand Head) | **$0.00/month (True Pay-per-Execution)** |
| **Best Suited For** | High-volume batch streams, large datasets (>100k rows), continuous distributed training | Event-driven bursty workloads, small/medium datasets (<50k rows), cost-minimal environments |

---

## 5. Traceability Matrix

| Requirement ID | System Component | Primary Implementation File | Verification Test / Automation |
| :--- | :--- | :--- | :--- |
| **FR-01** | Ingestion & Schema | `application/src/schema_validator.py`, `ingest.py` | `application/tests/test_dataset_generator.py` |
| **FR-02** | Ledger & Scheduling | `terraform/data/dynamodb.tf`, `modules/ledger` | `make test-ledger`, `scripts/run_local_e2e.sh` |
| **FR-03** | Entity Resolution | `application/src/entity_resolver.py`, `normalizer.py` | `application/tests/test_entity_resolver.py` |
| **FR-04** | Apache Iceberg Sink | `application/src/iceberg_sink.py`, `catalog_factory.py` | `application/tests/test_iceberg_sink.py` |
| **FR-05** | Distributed ML | `application/src/train_model.py`, `ray_pipeline.py` | `application/tests/test_pipeline.py` |
| **SRV-01** | Serverless Handlers | `application/src/serverless/handlers.py` | `application/tests/test_serverless_pipeline.py` |
| **SRV-02** | Step Functions ASL | `terraform/serverless/step_functions_pipeline.asl.json` | `scripts/run_serverless_local.sh` |
| **NFR-01** | Terraform Layers | `terraform/bootstrap`, `network`, `eks`, `data`, `platform`, `serverless` | `make tf-validate-all` |
| **NFR-02** | Compute Elasticity | `kubernetes/ray/ray-cluster.yaml`, `kubernetes/karpenter/` | `scripts/validate_k8s_manifests.sh` |
| **NFR-03** | Zero-Trust IAM | `terraform/modules/irsa`, `platform/github_oidc.tf`, `serverless/iam.tf` | `make test-security-audit` |
| **NFR-04** | Observability | `kubernetes/observability/`, `helm/kuberay-operator/` | `scripts/check_ray_health.sh` |
