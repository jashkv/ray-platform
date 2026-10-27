# Terraform Bootstrap Layer (`01-bootstrap`)

## Overview
This layer provisions the foundational AWS infrastructure required to host Terraform remote state and distributed state locking across all subsequent platform layers (`network`, `eks`, `data`, `platform`).

## Resources Provisioned
- **S3 Bucket (`aws_s3_bucket`):**
  - Unique naming: `${var.project_name}-${var.environment}-tfstate-${ACCOUNT_ID}`
  - Object versioning enabled (`aws_s3_bucket_versioning`)
  - Server-side encryption using customer-managed KMS key (`aws_kms_key`)
  - All public access blocked (`aws_s3_bucket_public_access_block`)
  - Strict HTTPS/TLS enforcement policy (`aws_s3_bucket_policy`)
  - `prevent_destroy = true` lifecycle rule
- **KMS Customer Managed Key (`aws_kms_key`):**
  - Dedicated key for state encryption with annual automatic key rotation enabled.
- **DynamoDB State Lock Table (`aws_dynamodb_table`):**
  - Table name: `${var.project_name}-${var.environment}-tflock`
  - Partition key: `LockID` (String)
  - On-Demand billing (`PAY_PER_REQUEST`)
  - Server-side encryption with KMS CMK
  - Point-in-time recovery (PITR) enabled

## Initial Provisioning Procedure (One-Time Bootstrap)

> [!IMPORTANT]
> This bootstrap layer uses a local state file during its initial `apply` because the S3 bucket does not yet exist. Once provisioned, the state can be migrated to the S3 bucket if desired.

1. Navigate to the bootstrap directory:
   ```bash
   cd terraform/bootstrap
   ```
2. Copy the example variables file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```
3. Initialize Terraform with local state:
   ```bash
   terraform init
   ```
4. Generate and inspect the execution plan:
   ```bash
   terraform plan -out=bootstrap.tfplan
   ```
5. Apply the plan upon authorization:
   ```bash
   terraform apply bootstrap.tfplan
   ```
6. Capture the output backend configuration snippet and configure subsequent layers (`network/`, `eks/`, `data/`, `platform/`).

## Disaster Recovery & State Rollback
- In the event of state corruption, previous state versions can be restored directly via S3 Object Versioning.
- If a stale lock persists after an interrupted pipeline, verify no other process is running before executing:
  ```bash
  terraform force-unlock <LOCK_ID>
  ```
