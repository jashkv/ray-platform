# Terraform Network Layer (`02-network`)

## Overview
This layer provisions the networking topology required for the EKS cluster and Ray workloads, adhering to security isolation and cloud cost best practices.

## Architectural Design & Cost Optimization

### 1. Multi-AZ Private Subnet Layout
- EKS worker nodes and Ray pods run **strictly inside private subnets** across 3 Availability Zones (`us-east-1a`, `us-east-1b`, `us-east-1c`).
- No worker nodes or Ray pods receive public IP addresses.
- Multi-AZ placement provides failure domain isolation and allows the Spot worker pool to source Spot capacity across multiple instance pools.

### 2. S3 Gateway VPC Endpoint (Critical Cost Decision)
- Direct S3 Gateway VPC Endpoint is attached to both public and private route tables.
- **Cost Impact:** $0.00/hour, $0.00 data processing charges.
- **Throughput:** Unlimited wire-speed communication between Ray workers reading CSV files, writing Iceberg data files, and saving ML models to Amazon S3. Without this, petabyte-scale data flows would route through the NAT Gateway at \$0.045/GB data processing cost.

### 3. NAT Gateway Strategy
- In `test`, `enable_single_nat_gateway = true` uses 1 NAT Gateway (~$32.40/month baseline) rather than 3 NAT Gateways (~$97.20/month baseline), reducing cloud networking charges by 66%.
- Can be toggled (`enable_single_nat_gateway = false`) if multi-AZ NAT redundancy across all AZs is required.

### 4. Kubernetes Subnet Tags
- Public subnets tagged with `kubernetes.io/role/elb = 1`.
- Private subnets tagged with `kubernetes.io/role/internal-elb = 1` and `karpenter.sh/discovery = <cluster_name>`.

## Validation
```bash
cd terraform/network
terraform fmt -check
terraform init -backend=false
terraform validate
```
