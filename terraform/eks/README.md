# Terraform EKS Infrastructure Layer (`03-eks`)

## Overview
This layer provisions the Amazon EKS cluster (`v1.31`), IAM roles, OIDC identity provider for IRSA, and decoupled node groups.

## Node Group Strategy & Spot Architecture

| Node Group | Capacity Type | Instance Types | Min / Desired / Max | Taints & Labels | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`head-system-pool`** | `ON_DEMAND` | `m6i.xlarge` (4 vCPU, 16GiB) | 1 / 1 / 2 | `workload-role=ray-head-system` (No taints) | Runs Ray Head (GCS, Dashboard), CoreDNS, KubeRay Operator, Prometheus. Guarantees cluster control-plane stability. |
| **`worker-spot-pool`** | `SPOT` | `m6i.xlarge`, `m5.xlarge`, `m5a.xlarge`, `m6a.xlarge` | 0 / 1 / 10 | Label: `workload-role=ray-worker`<br>Taint: `workload-role=ray-worker:NoSchedule` | Executes parallel Ray Data ingestion, EntityResolver actor, and Ray Train workers with ~70% cost savings. |
| **`worker-ondemand-fallback`** | `ON_DEMAND` | `m6i.xlarge` | 0 / 0 / 5 | Label: `workload-role=ray-worker`<br>Taint: `workload-role=ray-worker:NoSchedule` | Standby fallback pool to guarantee job SLA during regional Spot capacity exhaustion. |

## Spot Interruption Handling
1. **Diversified Capacity Pools:** By specifying 4 instance types across multiple generations (m5, m6) and CPU vendors (Intel, AMD) spanning 3 Availability Zones, AWS EKS provisions Spot capacity across 12 independent Spot pools.
2. **Ray Lineage & Task Retries:** Ray Data tasks are pure functions that automatically re-execute upon worker node termination.
3. **Dedicated Actor Sizing:** The stateful `EntityResolver` actor is scheduled with Ray custom resource `entity_resolver_slot: 1` and tolerates the worker node taint.

## Validation
```bash
cd terraform/eks
terraform fmt -check
terraform init -backend=false
terraform validate
```
