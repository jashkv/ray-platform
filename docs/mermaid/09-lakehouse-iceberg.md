# 09 — Apache Iceberg ACID Lakehouse Storage Architecture

This document describes the **Apache Iceberg Format v2 Transactional Storage Architecture**, detailing its hierarchical metadata tree, ACID commit mechanics, and AWS Glue integration.

---

## Iceberg Architecture Diagram

```mermaid
flowchart TD
    %% Apache Iceberg ACID Lakehouse Storage Architecture
    subgraph Compute_Engines["Compute & Query Layer"]
        RAY_WORKER["Ray Worker (PyIceberg / DuckDB / PySpark)"]
        ATHENA["Amazon Athena (Serverless SQL Querying)"]
    end

    subgraph Catalog_Layer["Catalog & Metastore (ACID Lock Manager)"]
        GLUE_CATALOG[("AWS Glue Data Catalog\nDatabase: corporate_data_db\nTable: corporate_registry\n- Atomic CAS Commit Lock\n- Points to: Current Table Metadata")]
    end

    subgraph S3_Metadata_Tree["S3 Iceberg Metadata Tree (iceberg-warehouse/corporate_registry/metadata/)"]
        direction TB

        META_JSON["Table Metadata File (v2.metadata.json)\n- Schema Definition & Field IDs\n- Partition Spec\n- Snapshot History & Current Snapshot ID"]

        SNAP_LIST["Manifest List File (snap-9182371982.avro)\n- List of Manifest Files\n- Snapshot Summary & Added/Deleted Counts\n- Partition Bounds for Fast Pruning"]

        subgraph Manifest_Files["Manifest Files (.avro)"]
            M1["Manifest File 1 (m1.avro)\n- File Paths\n- Column Min/Max Stats\n- Null Counts & Row Counts"]
            M2["Manifest File 2 (m2.avro)\n- File Paths\n- Column Min/Max Stats\n- Null Counts & Row Counts"]
        end
    end

    subgraph S3_Data_Files["S3 Data Files (iceberg-warehouse/corporate_registry/data/)"]
        direction LR
        PARQUET_1["Parquet Data File 1\n(part-00000-snappy.parquet)\n- Snappy Compressed\n- Dictionary Encoded"]
        PARQUET_2["Parquet Data File 2\n(part-00001-snappy.parquet)\n- Snappy Compressed\n- Dictionary Encoded"]
        PARQUET_N["Parquet Data File N\n(part-00002-snappy.parquet)\n- Columnar Layout"]
    end

    subgraph Quarantine_Storage["Isolation Storage (Corrupt & Ambiguous Records)"]
        S3_QUARANTINE[("S3: quarantine/ambiguous_entities/\n- Ambiguous Match Ratio (0.65 - 0.89)\n- Raw Corrupt CSV Rows\n- Isolated from Lakehouse")]
    end

    %% Engine to Catalog
    RAY_WORKER -->|"1. Read Current Metadata Pointer"| GLUE_CATALOG
    ATHENA -->|"1. Read Current Metadata Pointer"| GLUE_CATALOG
    GLUE_CATALOG -->|"2. Return Pointer to v2.metadata.json"| META_JSON

    %% Metadata Tree Traversal
    META_JSON -->|"3. References Current Snapshot"| SNAP_LIST
    SNAP_LIST -->|"4. Reads Partition Summaries"| M1
    SNAP_LIST -->|"4. Reads Partition Summaries"| M2
    M1 -->|"5. Predicate Pushdown Pruning"| PARQUET_1
    M2 -->|"5. Predicate Pushdown Pruning"| PARQUET_2
    M2 -->|"5. Predicate Pushdown Pruning"| PARQUET_N

    %% Atomic Commit Cycle
    RAY_WORKER -->|"6a. Stage New Data Files"| S3_Data_Files
    RAY_WORKER -->|"6b. Write New Manifest & Snapshot"| S3_Metadata_Tree
    RAY_WORKER -->|"6c. Atomic Compare-And-Swap (CAS) Lock"| GLUE_CATALOG

    %% Quarantine Divert
    RAY_WORKER -.->|"Divert Unmatched Ambiguities"| S3_QUARANTINE
```

---

## Transactional Guarantees & Features

### 1. Atomic Compare-And-Swap (CAS) Commits
- All write operations staged by Ray workers write immutable Parquet data files to `iceberg-warehouse/`.
- Once data and manifest avro trees are staged in S3, the commit is executed via an atomic CAS update on AWS Glue Data Catalog table parameter `metadata_location`.
- If a concurrent write commits first, the transaction performs an Optimistic Concurrency Control (OCC) retry, guaranteeing zero partial writes or phantom reads.

### 2. Snapshot Isolation & Time-Travel
- Every commit creates a distinct immutable snapshot ID (`snap-XXXXXXXXXX.avro`).
- Downstream query engines (Athena, DuckDB, Trino) can query historical state deterministically via `VERSION AS OF <snapshot_id>` or `TIMESTAMP AS OF <datetime>`.

### 3. Schema Evolution Without Table Rewrites
- Iceberg tracks columns by explicit numeric IDs, not column names or positions.
- New schema fields discovered in subsequent ingestion runs can be added, renamed, or reordered without rewriting existing Parquet data files.

### 4. Dead-Letter Quarantine
- Ambiguous entity matches ($0.65 \le \text{confidence} < 0.90$) and corrupt rows are diverted directly to `s3://test-ray-platform-data-*/quarantine/`.
- This ensures the production Iceberg table contains exclusively high-integrity, canonical records.
