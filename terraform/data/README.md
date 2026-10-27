# Terraform Data Lakehouse & IRSA Layer (`04-data`)

## Overview
This layer provisions the durable data storage, AWS Glue Data Catalog database, DynamoDB processing ledger, and IAM Roles for Service Accounts (IRSA) for Ray pods.

## Architecture & Security Controls

### 1. Amazon S3 Lakehouse Bucket
- **Durable Storage:** Versioning enabled, SSE-KMS encryption with customer-managed key, all public access blocked, strict TLS-only bucket policy.
- **Lakehouse Prefixes:**
  - `incoming/`: CSV landing zone for raw input datasets.
  - `manifests/`: Staging and batch manifest discovery pointers.
  - `quarantine/`: Invalid, schema-mismatched, or unresolvable records.
  - `iceberg-warehouse/`: Parquet data files and metadata trees for the Apache Iceberg `corporate_registry` table.
  - `models/`: Durable storage for trained XGBoost model artifacts and evaluation metrics JSON.

### 2. AWS Glue Data Catalog
- Managed database `${project_name}_${environment}_db` acts as the Apache Iceberg catalog.
- PyIceberg queries Glue via AWS SDK without needing a dedicated REST catalog server.

### 3. DynamoDB Processing Ledger
- Eliminates duplicate processing and race conditions.
- Uses conditional lease acquisitions (`attribute_not_exists(file_uri) OR lease_expiration < :now`).
- Tracks batch states: `CLAIMED`, `IN_PROGRESS`, `COMPLETED`, `FAILED`.

### 4. Zero-Trust IRSA (Workload Identity)
- IAM role trust policy explicitly checks `aud = sts.amazonaws.com` and `sub = system:serviceaccount:ray-workloads:ray-pipeline-sa`.
- Least-privilege permissions bounded strictly to the data lake bucket, Glue catalog database, and ledger table.
- **Zero static credentials** in containers or Kubernetes secrets.

## Validation
```bash
cd terraform/data
terraform fmt -check
terraform init -backend=false
terraform validate
```
