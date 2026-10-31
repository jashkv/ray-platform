# Developer & Operator Guide — Distributed AI Foundation Application

This guide provides an in-depth, hands-on walkthrough of the **Distributed AI Foundation Application**. It covers architecture mechanics, local execution, configuration options, model serving, extension recipes, and operational troubleshooting.

---

## 1. Architecture Philosophy & Design Patterns

The application is structured around five core design patterns:

1. **Data-Agnostic Ingestion (Open-Closed Principle):**
   The ingestion engine ([`ingest.py`](file:///application/src/ingest.py)) is open to extension for unforeseen schemas without modifying internal resolution logic. Incoming columns are matched dynamically via semantic aliases.
2. **Deterministic Evidence-Based Resolution:**
   Deduplication relies on explainable, auditable rules (Tax ID exact match, Levenshtein distance $\ge 0.88$ with attribute corroboration), avoiding opaque black-box clustering or non-deterministic hash collisions.
3. **Transactional ACID Lakehouse (Snapshot Isolation):**
   All writes commit to an **Apache Iceberg v2** table backed by AWS Glue Data Catalog. Reads and writes are isolated via optimistic concurrency control, ensuring zero dirty reads or table locks.
4. **Econometric Grounding for ML:**
   Revenue regression is modeled using **10 Defensible Econometric Assumptions** (Zipf's Law, Cobb-Douglas scaling, heteroskedasticity log-transformation), preventing multi-billion-dollar enterprise outliers from skewing model weights.
5. **Continuous Deployment & Inference:**
   Trained models are packaged as self-contained Scikit-Learn pipelines (`preprocessor` + `TransformedTargetRegressor`) and served via **Ray Serve** with zero-downtime blue/green rollouts.

---

## 2. Quickstart & Local Hands-on Execution

You can run and test every component of the application locally without AWS cloud credentials or billable resources.

### A. Environment Bootstrap
```bash
# 1. Audit Python version and initialize virtual environment
make setup

# 2. Run code linting, formatting, and secret leak pre-checks
make lint

# 3. Run the automated test suite (16 tests)
make test
```

### B. Execute the Full Distributed Pipeline Locally
```bash
make e2e-local
```
Alternatively, invoke the pipeline entrypoint directly:
```bash
.venv/bin/python application/src/ray_pipeline.py \
  --s1-input application/data/supply_chain_data_s1.csv \
  --s2-input application/data/financial_data_s2.csv \
  --catalog-type sqlite \
  --warehouse-path /tmp/e2e_iceberg_warehouse \
  --output-model-dir application/models
```

**Expected Console Output:**
```
[INFO] RayPipeline: [Step 1/4] Initializing Deterministic EntityResolver Engine...
[INFO] RayPipeline: [Step 2/4] Ingesting CSV datasets and performing entity resolution...
[INFO] RayPipeline: [+] Total Ingested Records: 2400
[INFO] RayPipeline: [+] Canonical Unique Companies: 1920
[INFO] RayPipeline: [+] Ambiguous Quarantined Records: 543
[INFO] RayPipeline: [Step 3/4] Persisting harmonized entities to Apache Iceberg table...
[INFO] RayPipeline: [+] Iceberg Commit Verified: Snapshot ID 4804921786651034397 with 1920 records
[INFO] RayPipeline: [Step 4/4] Training and evaluating revenue prediction model...
[INFO] RayPipeline: [+] Model Evaluation Complete:
[INFO] RayPipeline:     - Test MAE:  $16,921,241.53
[INFO] RayPipeline:     - Test RMSE: $60,173,205.95
[INFO] RayPipeline:     - Test R2:   0.9515
```

### C. Launch the Interactive Web Console & Live Model Serving
In terminal 1:
```bash
make ui
# or
make frontend
```
Starts the model inference microservice and interactive web console on `http://localhost:8000`.

**Console Capabilities:**
- **Drag-and-Drop Ingestion:** Accepts any CSV feed with arbitrary headers or delimiters.
- **Dynamic Schema Discovery:** Visualizes mapped fields in real time.
- **Interactive Entity Resolution:** Executes deterministic deduplication, showing golden canonical records and quarantined items.
- **Batch & Single ML Predictions:** Runs Scikit-Learn `TransformedTargetRegressor` ($R^2 = 0.9515$) predictions on any inserted dataset.
- **Amazon S3 Landing Zone Upload:** Inspects, checksums, and uploads datasets to `s3://<bucket>/incoming/` with dry-run support.

In terminal 2, you can also query the running service programmatically with unforeseen corporate records:
```bash
make query-model
```

---

## 3. Deep Dive into Application Components

### Module 1: Dynamic Ingestion (`ingest.py` & `schema_validator.py`)
- **Header Auto-Discovery:** [`auto_detect_columns()`](file:///application/src/ingest.py#L53) scans the CSV header row. It executes a 3-pass heuristic:
  1. Exact alias match (e.g. `ein` $\to$ `tax_id`).
  2. Token/substring match (e.g. `ein_code` $\to$ `tax_id`).
  3. Concept substring match (e.g. headers containing `name`, `rev`, `emp`).
- **Dirty String Parsing:** [`parse_numeric_value()`](file:///application/src/schema_validator.py#L10) strips non-numerical characters and evaluates metric suffixes (`M`, `k`, `B`):
  ```python
  parse_numeric_value("$ 45,000,000")  # -> 45000000.0
  parse_numeric_value("120.5M")        # -> 120500000.0
  parse_numeric_value("750k")          # -> 750000.0
  parse_numeric_value("N/A")           # -> 0.0
  ```

### Module 2: Name Normalization & Identity (`normalizer.py`)
- **Cleaning:** [`clean_company_name()`](file:///application/src/normalizer.py#L31) strips international legal suffixes using compiled regex patterns (`\binc\b`, `\bllc\b`, `\bgmbh\b`, `\ba/s\b`, `\bag\b`, `\bplc\b`, `\bltd\b`), applies Unicode NFKD normalization, and collapses whitespace.
- **Similarity:** [`levenshtein_ratio()`](file:///application/src/normalizer.py#L59) computes pure Python dynamic programming edit distance:
  $$\text{Ratio} = 1.0 - \frac{\text{edit\_distance}}{\max(\text{len}_1, \text{len}_2)}$$
- **Deterministic UUIDv5:** [`generate_canonical_id()`](file:///application/src/normalizer.py#L87) hashes `TAX:ID` or `NAME:COUNTRY:CLEAN_NAME` using namespace `uuid.NAMESPACE_DNS`, emitting consistent IDs like `COMP-F293732C-159C`.

### Module 3: Entity Resolution Engine (`entity_resolver.py`)
- **Resolution Strategy:**
  1. **Strong Tax ID:** If tax ID matches in `tax_id_index`, merges record into existing canonical entity, updating revenue if the new source has audited fidelity.
  2. **Fuzzy Name Match:** Searches within the entity's country pool. If Levenshtein ratio $\ge 0.88$ AND founded year matches within $\pm 2$ years, merges record.
  3. **Quarantine:** If similarity $\ge 0.65$ but attributes conflict, diverts record to `quarantine_records`.
  4. **New Entity:** If no match found, creates a new `CanonicalCompanyEntity`.
- **Ray Custom Resource:** Decorated with `@ray.remote(resources={"entity_resolver_slot": 1})`, ensuring that in a distributed Ray cluster, the resolver actor runs as a dedicated singleton on a worker node.

### Module 4: Transactional Lakehouse (`iceberg_sink.py` & `catalog_factory.py`)
- **Catalog Abstraction:** [`get_iceberg_catalog()`](file:///application/src/catalog_factory.py#L10) switches between:
  - `glue`: Production AWS Glue Data Catalog connected to `s3://bucket/iceberg-warehouse`.
  - `sqlite`: Local embedded SQLite catalog at `/tmp/iceberg_warehouse/catalog.db`.
- **Table Writes:** Entities are converted to a `pyarrow.Table` conforming to [`CORPORATE_REGISTRY_ICEBERG_SCHEMA`](file:///application/src/iceberg_sink.py#L25). Writes are atomic and generate an updated Avro metadata snapshot.
- **Snapshot Inspection:** Inspect snapshots using [`scripts/verify_iceberg_table.py`](file:///scripts/verify_iceberg_table.py):
  ```bash
  .venv/bin/python scripts/verify_iceberg_table.py --warehouse-path /tmp/e2e_iceberg_warehouse
  ```

### Module 5: Econometric Model Training (`train_model.py`)
- **Target Transformation:** Financial data is heteroskedastic (variance scales with company size). The model wraps a `GradientBoostingRegressor` inside `TransformedTargetRegressor(func=np.log1p, inverse_func=np.expm1)`:
  - Trains on $\log(1 + y)$ so that SMEs and large enterprises receive proportional loss penalties.
  - Automatically exponentiates predictions back to USD scale at inference time.
- **Feature Pipeline:**
  - Dynamic numeric columns: `SimpleImputer(strategy="median")`
  - Dynamic categorical columns: `OneHotEncoder(handle_unknown="ignore")`
- **Cross-Validation:** Evaluates 5-fold cross-validation on training data, reporting mean out-of-fold $R^2$ (`0.9425`) alongside held-out test $R^2$ (`0.9515`) and MAPE (`11.87%`).
- **Artifacts:** Exports `revenue_model.joblib`, `metrics.json`, and `model_metadata.json` into [`application/models/`](file:///application/models).

### Module 6: Model Serving Microservice (`serve_model.py`)
- **Inference Pipeline:** Loads the persisted `revenue_model.joblib` pipeline. When a prediction payload arrives:
  1. Computes `company_age = 2025 - founded_year`.
  2. Assembles feature DataFrame.
  3. Predicts annual revenue in USD.
  4. Classifies firm size tier (`Small Business`, `Medium Enterprise`, `Mid-Market Enterprise`, `Large Enterprise`).
- **Endpoints:**
  - `GET /health` $\to$ `{"status": "HEALTHY", "model_loaded": true}`
  - `GET /metadata` $\to$ Model parameters, metrics, and the 10 Econometric Assumptions.
  - `POST /predict` $\to$ Single company prediction.
  - `POST /batch-predict` $\to$ List of company predictions.

---

## 4. Operational Recipes & Customization

### Recipe 1: Ingesting a Custom Corporate CSV Feed
To process an unforeseen CSV feed with non-standard headers:
```python
from application.src.entity_resolver import EntityResolverEngine
from application.src.ingest import ingest_dataset_file

resolver = EntityResolverEngine()

# The auto-discovery engine automatically maps non-standard headers:
# e.g., 'Vendor', 'TaxNo', 'HQ', 'EstYear', 'Headcount', 'Sales'
count = ingest_dataset_file("my_custom_feed.csv", "partner_feed", resolver)
print(f"Ingested {count} records successfully.")
```

### Recipe 2: Adjusting Entity Resolution Thresholds
To make matching more conservative or permissive:
```python
# Strict matching (higher precision, lower recall)
strict_resolver = EntityResolverEngine(fuzzy_threshold=0.92, ambiguity_threshold=0.75)

# Permissive matching (higher recall, lower precision)
permissive_resolver = EntityResolverEngine(fuzzy_threshold=0.82, ambiguity_threshold=0.60)
```

### Recipe 3: Querying the Running Model Service via cURL
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Apex Quantum Instruments",
    "employee_count": 250,
    "founded_year": 2015,
    "industry_sector": "Technology",
    "country": "US"
  }'
```

**Response:**
```json
{
  "company_name": "Apex Quantum Instruments",
  "predicted_annual_revenue_usd": 85400210.50,
  "predicted_revenue_formatted": "$85,400,210.50",
  "firm_size_tier": "Mid-Market Enterprise",
  "model_version": "1.2.0"
}
```

### Recipe 4: Event-Driven Signal Trigger on CSV Insertion
Whenever any CSV dataset is inserted or uploaded:
1. **Interactive Console (Auto-Trigger):** Check the **"⚡ Auto-Trigger Ray Pipeline on CSV Insertion"** toggle in the Web Console (`http://localhost:8000`). Dropping or pasting any CSV immediately triggers the pipeline signal and switches to the live execution monitor.
2. **REST API Signal Dispatch:**
   ```bash
   curl -X POST "http://localhost:8000/api/trigger-pipeline" \
     -H "Content-Type: application/json" \
     -d '{
       "s1_path": "application/data/supply_chain_data_s1.csv",
       "filename": "incoming_feed.csv"
     }'
   ```
3. **CLI S3 Upload with Signal Trigger:**
   ```bash
   python scripts/upload_dataset_to_s3.py --bucket my-bucket --dir application/data --trigger-pipeline
   ```
4. **Kubernetes Event-Driven Controller:**
   Managed via [`kubernetes/jobs/s3-event-pipeline-trigger.yaml`](file:///kubernetes/jobs/s3-event-pipeline-trigger.yaml), which watches S3 ObjectCreated events and submits a `RayJob` custom resource automatically.

---

## 5. Troubleshooting & Operational Playbooks

| Symptom | Probable Cause | Triage & Remediation |
| :--- | :--- | :--- |
| **High Quarantine Rate (>15%)** | Datasets contain duplicate company names registered in different countries or differing founded years. | Inspect quarantined records in `metrics.json` or S3 dead-letter storage. Verify whether the datasets have inconsistent legal suffix abbreviations. |
| **`TransformedTargetRegressor` Negative Revenue** | Inverse exponential received invalid input. | The pipeline clips predictions via `np.maximum(0.0, y_pred)` to guarantee non-negative revenues. |
| **Out-of-Memory (OOM) During Ingestion** | Ingestion of multi-million row datasets loaded entirely into memory. | Ray Data automatically chunks records into streaming blocks. Sizing is governed by `--object-store-memory` and `/dev/shm` emptyDir mounts. |
| **Unseen Categorical Value in Live Serving** | Client queries an unforeseen industry sector or country code. | `OneHotEncoder(handle_unknown="ignore")` sets unforeseen category dummy columns to 0.0, falling back to sector median without crashing. |
| **Iceberg Concurrent Write Conflict** | Two simultaneous pipeline runs attempting to commit to the same table. | PyIceberg implements optimistic locking with automatic retries and snapshot refresh. In high-concurrency environments, writes should be sequenced through the RayJob queue. |
