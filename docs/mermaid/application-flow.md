# Application Flow & Visual Architecture

This document contains visual workflow diagrams, sequence interactions, and decision trees for the **Distributed AI Foundation Application**.

---

## 1. End-to-End Application Data Lifecycle

```mermaid
flowchart TD
    subgraph DataSources["1. Multi-Source Ingestion Feeds"]
        S1["Supply Chain Feed (S1)\n- corporate_name, tax_identifier\n- Dirty strings ($14.5M, EUR)"]
        S2["Financial Registry (S2)\n- legal_name, registration_number\n- Missing IDs, alternate suffixes"]
        UNFORESEEN["Unforeseen CSV Feeds\n- Arbitrary headers & formats"]
    end

    subgraph IngestionEngine["2. Data-Agnostic Ingestion & Normalization"]
        DETECT["Schema Auto-Discovery\n(Semantic Alias Matcher)"]
        SANITIZE["parse_numeric_value()\n(Sanitizes Currencies & Suffixes)"]
        NORM["Normalizer\n(Unicode NFKD + Strip Legal Types)"]
    end

    subgraph EntityResolution["3. Isolated Ray Actor Entity Resolver"]
        ACTOR["EntityResolver Actor\n(Custom Resource: entity_resolver_slot: 1)"]
        INDEX_TAX[("Tax ID Primary Index")]
        INDEX_NAME[("Country Partitioned Name Index")]
        QUAR_STORE[("Ambiguity Quarantine Pool")]
    end

    subgraph Lakehouse["4. Transactional Lakehouse Storage"]
        ICEBERG["Apache Iceberg Table\ncorporate_data_db.corporate_registry"]
        GLUE[("AWS Glue Data Catalog\n(Atomic CAS Lock)")]
        S3_DATA["Amazon S3: data/*.parquet\n(Snappy Parquet Data Files)"]
        S3_META["Amazon S3: metadata/*.avro\n(Snapshots & Manifest Lists)"]
    end

    subgraph MLTraining["5. Econometric Model Training (Ray Train)"]
        ASSUMPTIONS["10 Econometric Assumptions\n(Zipf's Law, Cobb-Douglas Scaling)"]
        PIPELINE["Model Pipeline\n- Median Imputer + OneHot\n- Log1p Target Regressor\n- Gradient Boosting Trees"]
        EVAL["5-Fold Cross Validation\n(R² = 0.9515, MAPE = 11.87%)"]
        ARTIFACT["Export: revenue_model.joblib\n+ model_metadata.json"]
    end

    subgraph ModelServing["6. Production Inference (Ray Serve)"]
        RAY_SERVE["Ray Serve Microservice\n(Replicas 1..8 Autoscaling)"]
        REST_API["REST Endpoints\n- POST /predict\n- POST /batch-predict"]
        CLIENT["Live Client Applications\n(Unforeseen Company Queries)"]
    end

    S1 --> DETECT
    S2 --> DETECT
    UNFORESEEN --> DETECT
    DETECT --> SANITIZE
    SANITIZE --> NORM
    NORM --> ACTOR
    ACTOR <--> INDEX_TAX
    ACTOR <--> INDEX_NAME
    ACTOR -.->|Quarantine Ambiguous| QUAR_STORE
    ACTOR -->|Canonical Entities| ICEBERG
    ICEBERG <--> GLUE
    ICEBERG --> S3_DATA
    ICEBERG --> S3_META
    ICEBERG --> ASSUMPTIONS
    ASSUMPTIONS --> PIPELINE
    PIPELINE --> EVAL
    EVAL --> ARTIFACT
    ARTIFACT --> RAY_SERVE
    RAY_SERVE --> REST_API
    CLIENT <--> REST_API
```

---

## 2. Dynamic Schema Auto-Discovery Decision Flow

```mermaid
flowchart TD
    START["Read CSV Header Row"] --> NORM_HDR["Normalize Headers\n(lowercase, strip whitespace & underscores)"]
    NORM_HDR --> PASS1{"Pass 1: Exact Semantic Alias Match?"}
    
    PASS1 -- YES --> MAP_EXACT["Assign Concept to Header"]
    PASS1 -- NO --> PASS2{"Pass 2: Token / Substring Match?"}
    
    PASS2 -- YES --> MAP_TOKEN["Assign Concept (e.g. 'ein_code' -> tax_id)"]
    PASS2 -- NO --> PASS3{"Pass 3: Heuristic Keyword Match?"}
    
    PASS3 -- YES --> MAP_HEUR["Assign Concept (contains 'name', 'rev', 'emp')"]
    PASS3 -- NO --> DEFAULT_NAME["Fallback: First Column is Name, others unmapped"]

    MAP_EXACT --> ROW_LOOP["Iterate Data Rows"]
    MAP_TOKEN --> ROW_LOOP
    MAP_HEUR --> ROW_LOOP
    DEFAULT_NAME --> ROW_LOOP

    ROW_LOOP --> CLEAN_NUM["Sanitize Numeric Fields\n(Strip '$', 'EUR', commas; evaluate 'M', 'k', 'B')"]
    CLEAN_NUM --> PRESERVE["Preserve Unmapped Columns in entity.metadata"]
    PRESERVE --> EMIT["Forward Clean Record to Entity Resolver"]
```

---

## 3. Multi-Tier Entity Resolution Decision Tree

```mermaid
flowchart TD
    IN["Incoming Raw Record\n(Name, Tax ID, Country, Year, Headcount, Revenue)"] --> TIER1{"Tier 1: Tax ID / Registration # Present?"}
    
    TIER1 -- YES --> LOOKUP_TAX{"Tax ID in Primary Index?"}
    LOOKUP_TAX -- MATCH --> MERGE_TAX["Merge with Existing Canonical Entity\n- Append Source Dataset to Provenance\n- Update Audited Financial Revenue\n- Retain Canonical ID"]
    LOOKUP_TAX -- NO MATCH --> NEW_TAX["Create New Canonical Entity\n- Generate UUIDv5(TAX:id)\n- Index Tax ID in Primary Map\n- Index in Country Name Pool"]

    TIER1 -- NO --> TIER2["Tier 2: Clean Name Normalization\n(Unicode NFKD + Strip Legal Suffixes)"]
    TIER2 --> SEARCH_POOL["Search Country-Partitioned Name Pool"]
    SEARCH_POOL --> CALC_LEV["Calculate Levenshtein Similarity Ratio"]
    
    CALC_LEV --> CHECK_FUZZY{"Score >= 0.88 (Fuzzy Threshold)?"}
    
    CHECK_FUZZY -- YES --> CORROBORATE{"Corroborate Attributes:\nAbs(Year Difference) <= 2 years?"}
    CORROBORATE -- YES --> MERGE_FUZZY["Merge with Matched Entity\n- Rule: RULE_FUZZY_NAME_CORROBORATED\n- Confidence: Levenshtein Score"]
    CORROBORATE -- NO --> QUAR_CONFLICT["Send to Quarantine Dead-Letter\n- Reason: High Name Similarity with Conflicting Year"]

    CHECK_FUZZY -- NO --> CHECK_AMBIG{"Score >= 0.65 (Ambiguity Threshold)?"}
    CHECK_AMBIG -- YES --> QUAR_AMBIG["Send to Quarantine Dead-Letter\n- Reason: Borderline Similarity without Corroboration"]
    CHECK_AMBIG -- NO --> NEW_NAME["Create New Canonical Entity\n- Generate UUIDv5(NAME:country:clean_name)\n- Index in Country Pool"]
```

---

## 4. Apache Iceberg Transactional Commit Sequence

```mermaid
sequenceDiagram
    autonumber
    participant Pipeline as Ray Pipeline Driver
    participant Sink as Iceberg Sink (iceberg_sink.py)
    participant Catalog as AWS Glue Data Catalog
    participant S3_Data as Amazon S3 (Data Files)
    participant S3_Meta as Amazon S3 (Metadata Tree)

    Pipeline->>Sink: write_to_iceberg(entities, catalog_type="glue")
    Sink->>Catalog: load_table("corporate_data_db.corporate_registry")
    Catalog-->>Sink: Table Metadata (Current Snapshot ID & Schema)
    
    Sink->>Sink: Convert Entities to PyArrow Table (Enforce Iceberg Schema)
    Sink->>S3_Data: Write Snappy Parquet Data Files (UUID-named part files)
    S3_Data-->>Sink: Parquet File Paths & Column Min/Max Metrics

    Sink->>S3_Meta: Write Manifest File (.avro) with Data File Pointers
    Sink->>S3_Meta: Write Manifest List File (snap-{id}.avro)
    Sink->>S3_Meta: Write Versioned Metadata File (v{N}.metadata.json)

    Sink->>Catalog: Commit Transaction via Atomic Compare-And-Swap (CAS)
    alt Commit Succeeded
        Catalog-->>Sink: Commit Acknowledged (New Snapshot ID Active)
        Sink-->>Pipeline: Return Commit Summary (Status: TRANSACTION_COMMITTED)
    else Conflict Detected (Concurrent Writer)
        Catalog-->>Sink: Commit Failed (Snapshot Changed)
        Sink->>Sink: Retry with Exponential Backoff & Snapshot Refresh
    end
```

---

## 5. Machine Learning Training & Econometric Modeling Pipeline

```mermaid
flowchart LR
    subgraph DataPrep["1. Feature Extraction & Econometric Grounding"]
        ENTITIES["Canonical Entities\n(from Iceberg Table)"] --> FILTER["Filter Valid Revenue\n(revenue > 0, headcount > 0)"]
        FILTER --> MATRIX["Feature Matrix\n- Headcount (Zipf Power-Law)\n- Founded Year & Company Age\n- Industry Sector (Productivity Multipliers)\n- Country (Purchasing Power Parity)"]
    end

    subgraph Preprocessing["2. Robust Scikit-Learn Preprocessing"]
        MATRIX --> NUM_PIPE["Numeric Transformer:\nSimpleImputer(strategy='median')"]
        MATRIX --> CAT_PIPE["Categorical Transformer:\nOneHotEncoder(handle_unknown='ignore')"]
        NUM_PIPE --> MERGE_FEAT["ColumnTransformer"]
        CAT_PIPE --> MERGE_FEAT
    end

    subgraph ModelTrain["3. Transformed Target Regression"]
        MERGE_FEAT --> TTR["TransformedTargetRegressor\n- func: np.log1p(y)\n- inverse: np.expm1(y_pred)"]
        TTR --> GBR["GradientBoostingRegressor\n- n_estimators: 120\n- max_depth: 4\n- subsample: 0.85"]
    end

    subgraph Evaluation["4. Generalization Evaluation & Artifacts"]
        GBR --> CV["5-Fold Cross Validation\n(CV Mean R² = 0.9425)"]
        GBR --> TEST["Held-Out Test Set (20%)\n- R² = 0.9515\n- MAPE = 11.87%\n- MAE = $16.9M"]
        TEST --> DUMP["Persist: revenue_model.joblib\n+ model_metadata.json"]
    end
```

---

## 6. Model Serving & Real-Time Inference Sequence

```mermaid
sequenceDiagram
    autonumber
    participant Client as External Application
    participant Ingress as AWS ALB / Ingress (Cognito OAuth2)
    participant RayServe as Ray Serve Microservice (serve_model.py)
    participant Model as Serialized Pipeline (revenue_model.joblib)

    Client->>Ingress: POST /predict {"company_name": "Valence BioSystems", "employee_count": 180, ...}
    Ingress->>Ingress: Authenticate Token (Cognito / OIDC)
    Ingress->>RayServe: Forward HTTP Request to Router (:8000)

    RayServe->>RayServe: Route to Available Replica Worker
    RayServe->>Model: pipeline.predict(DataFrame)
    
    Note over Model: 1. Impute missing values with medians<br/>2. One-hot encode (ignore unseen categories)<br/>3. Predict log-revenue via Gradient Boosting<br/>4. Inverse transform via expm1(y_log)

    Model-->>RayServe: Predicted Revenue USD ($68,420,150.25)
    RayServe->>RayServe: Classify Firm Size Tier ("Medium Enterprise")
    RayServe-->>Ingress: JSON Response Payload
    Ingress-->>Client: 200 OK Response
```

---

## 7. Anomaly & Ambiguity Quarantine Flow

```mermaid
flowchart TD
    IN_REC["Input Corporate Record"] --> EVAL{"Evaluate Matching Rules"}
    
    EVAL -- Corrupted Schema --> ERR_PARSE["Schema Parsing Exception"]
    EVAL -- Borderline Name Similarity (0.65 <= Score < 0.88) --> ERR_AMBIG["Ambiguity Threshold Triggered"]
    EVAL -- High Name Similarity but Conflicting Founded Year --> ERR_YEAR["Attribute Conflict Triggered"]

    ERR_PARSE --> LOG_REASON["Attach Diagnostic Reason & Metadata:\n- Raw Row Contents\n- Source Dataset & Timestamp\n- Error Traceback"]
    ERR_AMBIG --> LOG_REASON
    ERR_YEAR --> LOG_REASON

    LOG_REASON --> MEM_QUAR["quarantine_records Array (In-Memory)"]
    MEM_QUAR --> S3_DEADLETTER["Write to Dead-Letter Storage:\ns3://bucket/quarantine/date=YYYY-MM-DD/anomalies.json"]
    S3_DEADLETTER --> CW_METRIC["Emit CloudWatch Anomaly Metric\n(Alert Data Engineering if Quarantine Rate > 10%)"]
    
    NOTE["Pipeline Continues Processing\nClean Records Without Interruption"] -.-> MEM_QUAR
```
