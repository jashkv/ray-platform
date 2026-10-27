# Troubleshooting & Operational Runbook — AWS Serverless Platform

- **Status:** Complete / Production-Verified Serverless Troubleshooting Guide
- **Target Environment:** `test`
- **Cloud Provider:** Amazon Web Services (AWS)
- **Branch:** `serverless` (Dedicated Serverless Alternative Branch)

---

## 1. Quick Diagnostic Checklist

When triaging an issue with the serverless pipeline, run the following diagnostic commands:

```bash
# 1. Check recent Step Functions executions
STATE_MACHINE_ARN=$(cd terraform/serverless && terraform output -raw state_machine_arn)
aws stepfunctions list-executions --state-machine-arn "$STATE_MACHINE_ARN" --max-results 5

# 2. Inspect Dead-Letter Queue (DLQ) for failed messages
DLQ_URL=$(cd terraform/serverless && terraform output -raw dlq_url)
aws sqs get-queue-attributes --queue-url "$DLQ_URL" --attribute-names ApproximateNumberOfMessages

# 3. Check the DynamoDB processing ledger
aws dynamodb scan --table-name ray_processing_ledger --limit 5

# 4. Tail CloudWatch logs for the resolver function
aws logs tail /aws/lambda/sfn-corporate-resolver --since 15m
```

---

## 2. Common Serverless Failure Modes & Remediation

### Failure 1: Lambda Function Timeout (`Task timed out after X.XX seconds`)

- **Symptoms:** Step Functions execution fails at a Lambda task state with `Lambda.Unknown` or `Task timed out`.
- **Root Cause:** S1/S2 dataset volume exceeds the compute throughput of the current memory allocation, or network latency during S3 transfers caused a stall.
- **Remediation:**
  1. Inspect the function duration in CloudWatch:
     ```bash
     aws logs filter-log-events \
       --log-group-name /aws/lambda/sfn-corporate-resolver \
       --filter-pattern "REPORT RequestId"
     ```
  2. Increase the memory allocation in [`terraform/serverless/main.tf`](../terraform/serverless/main.tf). In AWS Lambda, increasing memory from 2,048 MB to 3,072 MB or 4,096 MB **linearly increases CPU clock speed**, reducing computation time by 40–60%.
  3. Increase the `timeout` parameter in `main.tf` (e.g. from 300s to 600s).

---

### Failure 2: Lambda Out of Memory (OOM) (`Runtime.ExitError: Memory limit exceeded`)

- **Symptoms:** Lambda terminates abruptly with `Runtime.ExitError` and CloudWatch logs report `Max Memory Used: 2048 MB (Memory Size: 2048 MB)`.
- **Root Cause:** Large batch of raw CSV records caused pandas or PyArrow memory exhaustion during dataframe transformations.
- **Remediation:**
  1. Adjust `memory_size` for the affected Lambda in `terraform/serverless/main.tf`:
     ```hcl
     resource "aws_lambda_function" "resolver" {
       function_name = "sfn-corporate-resolver"
       memory_size   = 4096 # Scaled from 2048 to 4096
       timeout       = 300
       # ...
     }
     ```
  2. Apply the Terraform update:
     ```bash
     cd terraform/serverless && terraform apply -target=aws_lambda_function.resolver
     ```

---

### Failure 3: DynamoDB Conditional Check Failure (`ConditionalCheckFailedException`)

- **Symptoms:** `Stage1_DiscoveryAndClaim` fails with `DynamoDb.ConditionalCheckFailedException`.
- **Root Cause:** A pipeline run for the exact same input dataset hash is already in progress or has already completed. The idempotency guardrail correctly prevented redundant processing.
- **Remediation:**
  1. Query the ledger to check the existing execution:
     ```bash
     aws dynamodb get-item \
       --table-name ray_processing_ledger \
       --key '{"execution_id": {"S": "<execution_id>"}, "timestamp": {"S": "<timestamp>"}}'
     ```
  2. If the previous execution failed and needs to be re-run, delete the stale claim item:
     ```bash
     aws dynamodb delete-item \
       --table-name ray_processing_ledger \
       --key '{"execution_id": {"S": "<execution_id>"}, "timestamp": {"S": "<timestamp>"}}'
     ```
  3. Trigger the state machine execution again.

---

### Failure 4: Apache Iceberg Optimistic Lock Conflict (`CommitFailedException`)

- **Symptoms:** `Stage4_ApacheIcebergLakehouseSink` fails with `pyiceberg.exceptions.CommitFailedException: Table metadata changed during commit`.
- **Root Cause:** Another process committed a snapshot to the AWS Glue Data Catalog table `corporate_registry` simultaneously.
- **Remediation:**
  1. PyIceberg automatically retries snapshot commits with exponential jitter.
  2. If retries fail, ensure that Step Functions executions are not running multiple concurrent sink writes by inspecting `list-executions`:
     ```bash
     aws stepfunctions list-executions --state-machine-arn "$STATE_MACHINE_ARN" --status-filter RUNNING
     ```

---

### Failure 5: Machine Learning Test Performance Below Threshold ($R^2 < 0.85$)

- **Symptoms:** `Stage5_TrainRevenueModel` raises `ValueError: Model test R^2 score < 0.85`.
- **Root Cause:** The input CSV dataset has missing or corrupted revenue values, insufficient numeric rows, or zero variance.
- **Remediation:**
  1. Inspect validator output to verify that valid numeric records were extracted:
     ```bash
     aws logs tail /aws/lambda/sfn-corporate-validator --filter-pattern "Valid Records"
     ```
  2. Check the quarantine path in S3 to see if valid rows were improperly classified as ambiguous:
     ```bash
     aws s3 ls s3://test-ray-platform-data-123456789012/quarantine/
     ```

---

### Failure 6: SQS Dead-Letter Queue (DLQ) Message Triaging & Redrive

- **Symptoms:** Messages appear in `test-ray-platform-sfn-dlq`.
- **Root Cause:** A terminal failure was caught by Step Functions `States.ALL` and routed to the DLQ.
- **Remediation:**
  1. Receive and inspect the dead-letter payload:
     ```bash
     DLQ_URL=$(cd terraform/serverless && terraform output -raw dlq_url)
     aws sqs receive-message --queue-url "$DLQ_URL" --max-number-of-messages 1
     ```
  2. Examine the `"error"` and `"input"` attributes inside the message body to identify the failing state.
  3. Fix the underlying data or code issue.
  4. Redrive the execution using the payload input.

---

## 3. CloudWatch Logs Insights Forensic Queries

Use these queries in the **AWS CloudWatch Logs Insights** console:

### 1. Identify Slow Lambda Invocations (> 5 seconds):
```sql
fields @timestamp, @duration, @billedDuration, @maxMemoryUsed
| filter @type = "REPORT" and @duration > 5000
| sort @duration desc
| limit 20
```

### 2. Track Memory Saturation Across All Handlers:
```sql
fields @timestamp, @logStream, (@maxMemoryUsed / 1024 / 1024) as maxMemMB, @memorySize / 1024 / 1024 as allocMemMB
| filter @type = "REPORT"
| stats max(maxMemMB) by bin(5m)
```

### 3. Track Model $R^2$ Scores Over Time:
```sql
fields @timestamp, @message
| filter @message like /Model Performance/
| parse @message "R^2 = *, RMSE" as r2_score
| sort @timestamp desc
| limit 10
```
