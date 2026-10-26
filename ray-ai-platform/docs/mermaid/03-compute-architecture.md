# 03 — Compute Architecture & Capacity Tiering

This document outlines the **Compute Architecture and Capacity Tiering Model** for the Ray AI Platform on Amazon EKS.

---

## Compute Topology Diagram

```mermaid
flowchart TD
    %% Compute Architecture & Capacity Tiering
    subgraph EKS_Cluster["Amazon EKS Cluster: ray-platform-test-eks (Kubernetes v1.30)"]
        direction TB

        subgraph ControlPlane["AWS Managed Control Plane (Multi-AZ)"]
            K8S_API["Kubernetes API Server (v1.30)"]
            ETCD["etcd State Store (Encrypted with AWS KMS)"]
            K8S_SCHED["kube-scheduler"]
            ACCESS_ENTRY["EKS Access Entries Engine\n(EC2_LINUX Type - Zero aws-auth ConfigMap)"]
        end

        subgraph Tier1_System["Tier 1: Stable System Node Group (EKS Managed - On-Demand)"]
            direction TB
            subgraph Node_System["EC2 Instance: m5.large (On-Demand | us-east-1a)"]
                SYS_LABELS["Labels: workload-role = ray-head-system\nTaints: None"]
                
                subgraph SysComponents["Cluster System Services"]
                    COREDNS["CoreDNS (2 replicas)"]
                    VPCCNI["AWS VPC-CNI & Kube-Proxy"]
                    EBS_CSI["AWS EBS CSI Driver"]
                end

                subgraph Operators["Platform Controllers"]
                    KUBERAY["KubeRay Operator (v1.2.2)\n- Reconciles RayJob & RayCluster CRDs"]
                    KARP_CTRL["Karpenter Controller (v1.0.8)\n- JIT EC2 Fleet Provisioner\n- Polls Interruption SQS"]
                end

                subgraph ObservabilityStack["Monitoring Stack"]
                    PROM["Prometheus Server (Scrapes :8080)"]
                    GRAF["Grafana (Private Dashboards)"]
                end

                subgraph RayHeadContainer["Ray Head Pod (Stable Orchestrator)"]
                    HEAD_GCS["Global Control Store (GCS Redis)"]
                    HEAD_AUTOSCALER["Ray In-Tree Autoscaler\n- Evaluates task backlog\n- idleTimeout: 60s"]
                    HEAD_RES["Custom Resource: entity_resolver_slot: 1\n(Pins stateful EntityResolver actor)"]
                end
            end
        end

        subgraph Tier2_Karpenter["Tier 2: Dynamic Karpenter Spot Compute Layer (Just-In-Time)"]
            direction TB

            subgraph NodePool_Spot["NodePool: ray-worker-spot (Weight: 100)"]
                SPOT_SPECS["Taints: workload-role = ray-worker:NoSchedule\nConsolidation: WhenEmptyOrUnderutilized (60s)\nDisruption Budget: 20%\nLimits: 64 vCPUs / 256 GiB RAM"]
                
                subgraph DiversifiedPools["Diversified EC2 Spot Instances (3 AZs x 8 Types = 24 Pools)"]
                    direction LR
                    INSTANCE_M6I["m6i.xlarge / 2xlarge\n(Intel Ice Lake)"]
                    INSTANCE_M5["m5.xlarge / 2xlarge\n(Intel Xeon)"]
                    INSTANCE_M5A["m5a.xlarge / 2xlarge\n(AMD EPYC)"]
                    INSTANCE_M6A["m6a.xlarge / 2xlarge\n(AMD Milan)"]
                end

                subgraph WorkerPods["Ray Worker Pods (0 to 8 Replicas)"]
                    WP1["Worker Pod 1\nRequests: 3 CPU / 12Gi\n/dev/shm: 4Gi tmpfs\nPlasma: 3.6Gi"]
                    WP2["Worker Pod 2\nRequests: 3 CPU / 12Gi\n/dev/shm: 4Gi tmpfs\nPlasma: 3.6Gi"]
                    WPN["Worker Pod N\nScale-to-Zero Capable\n$0.00 idle cost"]
                end
            end

            subgraph NodePool_OnDemand["NodePool: ray-worker-ondemand (Weight: 10)"]
                OD_FALLBACK["Fallback On-Demand NodePool\n(Triggers only upon 100% Spot Regional Exhaustion)"]
            end
        end

        subgraph InterruptionEngine["Proactive Spot Interruption Handling"]
            EVENTBRIDGE["AWS EventBridge\n(EC2 Spot Interruption / Rebalance)"]
            SQS_QUEUE["SQS Interruption Queue\n(2-Minute Notice Drain)"]
        end
    end

    %% Wiring
    K8S_API <--> K8S_SCHED
    K8S_API <--> KUBERAY
    K8S_API <--> KARP_CTRL

    %% Head & Scheduling
    KUBERAY -->|"Deploys & Monitors"| RayHeadContainer
    HEAD_AUTOSCALER -->|"Requests Worker Replicas (0 to 8)"| K8S_API
    K8S_SCHED -->|"Fails to Place Worker Pods (Insufficient Capacity)"| WorkerPods
    WorkerPods -->|"Unschedulable (Pending State)"| KARP_CTRL

    %% Karpenter Provisioning Loop
    KARP_CTRL -->|"Direct AWS EC2 Fleet API (<45s)"| DiversifiedPools
    DiversifiedPools -->|"Node Registers via EKS Access Entry"| ACCESS_ENTRY
    ACCESS_ENTRY -->|"Authenticates EC2_LINUX"| K8S_API
    K8S_SCHED -->|"Schedules Pending Workers onto Nodes"| WorkerPods

    %% Interruption Loop
    EVENTBRIDGE -->|"2-Min Interruption Notice"| SQS_QUEUE
    SQS_QUEUE -->|"Karpenter Polls SQS"| KARP_CTRL
    KARP_CTRL -->|"Proactive Cordon & Evict"| WorkerPods

    %% Scale to Zero Loop
    HEAD_AUTOSCALER -->|"Idle > 60s: Scales Workers to 0"| WorkerPods
    KARP_CTRL -->|"Consolidates & Terminates Empty EC2 Nodes"| DiversifiedPools
```

---

## Capacity Tier Specifications

### Tier 1: Stable System Node Group (On-Demand)
- **Role:** Dedicated control and system orchestration plane.
- **Instance Sizing:** `m5.large` (2 vCPU, 8 GiB RAM).
- **Scale Bounds:** Min: 1, Max: 2, Desired: 1.
- **Hosted Workloads:** CoreDNS, VPC-CNI, kube-proxy, EBS CSI Driver, KubeRay Operator (`v1.2.2`), Karpenter Controller (`v1.0.8`), Prometheus, Grafana, and the **Ray Head Pod**.
- **Resiliency Rationale:** Prevents cluster deadlocks. Because the Karpenter controller itself lives on stable On-Demand capacity, it never preempts its own host or loses the ability to launch replacement worker nodes.

### Tier 2: Dynamic Karpenter Spot Compute Layer
- **Role:** Pure stateless and elastic computational tasks (data ingestion, validation, normalization, distributed Ray Train).
- **Instance Diversification:** 8 instance types (`m6i.xlarge`, `m5.xlarge`, `m5a.xlarge`, `m6a.xlarge`, `m6i.2xlarge`, `m5.2xlarge`, `m5a.2xlarge`, `m6a.2xlarge`) spread across 3 Availability Zones ($8 \times 3 = 24$ distinct capacity pools).
- **Tolerations & Taints:** Nodes are tainted with `workload-role=ray-worker:NoSchedule`. Non-Ray pods are barred from landing on worker Spot capacity.
- **Consolidation Policy:** `WhenEmptyOrUnderutilized` with a 60-second idle threshold and a 20% disruption budget. When no Ray tasks are active, workers scale to 0 and all EC2 nodes are terminated within 60 seconds.

### Node Authentication via EKS Access Entries
Static or legacy `aws-auth` ConfigMaps have been eliminated. Nodes authenticate via `aws_eks_access_entry` configured with `type = "EC2_LINUX"` and `principal_arn = aws_iam_role.karpenter_node.arn`. This enables sub-45-second zero-trust node joining without ConfigMap mutex contention.
