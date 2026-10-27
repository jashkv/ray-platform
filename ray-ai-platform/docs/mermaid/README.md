# Ray AI Platform — Master Architecture Diagrams & Visual Reference

This directory serves as the centralized visual architecture library for the **Distributed Ray AI Platform** on AWS EKS (`test` environment).

Every diagram is authored in standard [Mermaid.js](https://mermaid.js.org/) syntax, allowing direct GitHub/IDE rendering and programmatic export to SVG, PNG, and PDF.

---

## Diagram Index

| # | Diagram Title | Scope & Description | Source File | Deep-Dive Document |
| :---: | :--- | :--- | :---: | :---: |
| **01** | [Complete Platform Architecture](#01--complete-platform-architecture) | End-to-end cloud infrastructure, VPC, EKS, KubeRay, Karpenter, S3 Lakehouse, DynamoDB ledger, and CI/CD. | [`01-complete-architecture.mmd`](01-complete-architecture.mmd) | [`01-complete-architecture.md`](01-complete-architecture.md) |
| **02** | [Network Isolation & Zero-Trust](#02--network-isolation--zero-trust-architecture) | 3-tier Multi-AZ subnet topology, AWS PrivateLink VPC endpoints, Security Group chaining, NetworkPolicies, and IMDSv2. | [`02-network-zero-trust.mmd`](02-network-zero-trust.mmd) | [`02-network-zero-trust.md`](02-network-zero-trust.md) |
| **03** | [Compute Architecture & Capacity Tiering](#03--compute-architecture--capacity-tiering) | EKS Control Plane, On-Demand System Node Group, Karpenter JIT Spot NodePool, Fallback On-Demand, and EKS Access Entries. | [`03-compute-architecture.mmd`](03-compute-architecture.mmd) | [`03-compute-architecture.md`](03-compute-architecture.md) |
| **04** | [End-to-End Pipeline & Data Processing Flow](#04--end-to-end-pipeline--data-processing-flow) | CSV ingestion, dynamic schema inspection, multi-tier entity resolution, Ray Train ML regression, and Iceberg ACID commit. | [`04-pipeline-flow.mmd`](04-pipeline-flow.mmd) | [`04-pipeline-flow.md`](04-pipeline-flow.md) |
| **05** | [Two-Level Autoscaling & Spot Interruption](#05--two-level-autoscaling-lifecycle--spot-interruption) | KubeRay pod scaling, Karpenter sub-45s JIT EC2 provisioning, EventBridge 2-min Spot notice drain, and scale-to-zero ($0 cost). | [`05-autoscaling-lifecycle.mmd`](05-autoscaling-lifecycle.mmd) | [`05-autoscaling-lifecycle.md`](05-autoscaling-lifecycle.md) |
| **06** | [Ray Worker Node & Pod Internal Topology](#06--ray-worker-node--pod-internal-topology) | Linux kernel cgroups v2, 4 GiB `/dev/shm` tmpfs memory mount, Apache Arrow Plasma object store (3.6 GiB), and Raylet agents. | [`06-ray-worker-node.mmd`](06-ray-worker-node.mmd) | [`06-ray-worker-node.md`](06-ray-worker-node.md) |
| **07** | [Zero-Trust Security & Identity Federation](#07--zero-trust-security-identity--cryptographic-architecture) | IAM Roles for Service Accounts (IRSA), GitHub OIDC, AWS KMS CMK envelope encryption, EKS Access Entries, and RBAC. | [`07-security-identity.mmd`](07-security-identity.mmd) | [`07-security-identity.md`](07-security-identity.md) |
| **08** | [Observability, Metrics & Centralized Logging](#08--observability-metrics--centralized-logging-architecture) | Prometheus `PodMonitor` scraping port `:8080`, Grafana dashboards, Fluent Bit DaemonSet, and CloudWatch Logs over PrivateLink. | [`08-observability-telemetry.mmd`](08-observability-telemetry.mmd) | [`08-observability-telemetry.md`](08-observability-telemetry.md) |
| **09** | [Apache Iceberg ACID Lakehouse Storage](#09--apache-iceberg-acid-lakehouse-storage-architecture) | AWS Glue Data Catalog CAS lock, snapshot hierarchy, metadata tree, Snappy Parquet files, and dead-letter quarantine. | [`09-lakehouse-iceberg.mmd`](09-lakehouse-iceberg.mmd) | [`09-lakehouse-iceberg.md`](09-lakehouse-iceberg.md) |
| **10** | [CI/CD Pipeline & GitOps Deployment](#10--cicd-pipeline-gitops--infrastructure-lifecycle) | Static testing gates, 5 decoupled Terraform layers, multi-stage Docker build, ECR publishing, Helm releases, and smoke tests. | [`10-cicd-deployment.mmd`](10-cicd-deployment.mmd) | [`10-cicd-deployment.md`](10-cicd-deployment.md) |
| **11** | [Serverless Alternative Architecture](#11--aws-serverless-alternative-architecture) | AWS Step Functions, Lambda handlers (S1-S6), SQS DLQ, S3 lakehouse, DynamoDB ledger, and Glue Catalog. | [`11-serverless-architecture.mmd`](11-serverless-architecture.mmd) | [`11-serverless-architecture.md`](11-serverless-architecture.md) |

---

## 01 — Complete Platform Architecture

```mermaid
flowchart TD
    subgraph External["External World & Source Data"]
        S1["Source S1: Supply Chain CSV"]
        S2["Source S2: Financial Records CSV"]
        DEV["DevOps / Data Engineer (kubectl & AWS CLI)"]
        GHA["GitHub Actions CI/CD (OIDC Federated)"]
    end

    subgraph AWS["AWS Cloud (us-east-1) - Test Environment"]
        subgraph IAM_KMS["Identity & Cryptographic Foundations"]
            OIDC["AWS IAM OpenID Connect Provider"]
            KMS["AWS KMS Customer Managed Key (CMK)"]
            IRSA_RAY["IRSA: ray-workload-role"]
            IRSA_KARP["IRSA: karpenter-controller-role"]
            NODE_ROLE["IAM Role: karpenter-node-role"]
        end

        subgraph VPC["AWS VPC: 10.0.0.0/16 (3 AZs: us-east-1a, 1b, 1c)"]
            subgraph PublicSubnets["Public Subnets (NAT Gateway & IGW)"]
                NAT["NAT Gateways (Multi-AZ)"]
                ALB["Internal Ingress / ALB Controller"]
            end

            subgraph PrivateEndpoints["VPC Endpoints (AWS PrivateLink)"]
                VPCE_S3["S3 Gateway Endpoint"]
                VPCE_DDB["DynamoDB Gateway Endpoint"]
                VPCE_ECR["ECR API & DKR Interface Endpoints"]
                VPCE_CW["CloudWatch Logs Interface Endpoint"]
                VPCE_STS["STS Interface Endpoint"]
                VPCE_SQS["SQS Interface Endpoint"]
            end

            subgraph EKS["Amazon EKS Cluster: ray-platform-test-eks (v1.30)"]
                EKS_API["EKS Control Plane & Kubernetes API Server"]

                subgraph SystemNodeGroup["System Capacity: On-Demand Node Group (m5.large)"]
                    COREDNS["CoreDNS & VPC-CNI"]
                    KUBERAY["KubeRay Operator (v1.2.2)"]
                    KARP_CTRL["Karpenter Controller (v1.0.8)"]
                    PROM["Prometheus Server & Node Exporter"]
                    GRAFANA["Grafana Dashboards"]
                    FLUENT["AWS Fluent Bit DaemonSet"]
                end

                subgraph RayHeadPlacement["Ray Head Placement (On-Demand System Tier)"]
                    RAY_HEAD["Ray Head Pod (ray-cluster-kuberay-head)\n- GCS Global Control Store\n- In-Tree Autoscaler\n- Dashboard Port: 8265\n- Metrics Port: 8080\n- Custom Resource: entity_resolver_slot: 1"]
                end

                subgraph KarpenterCompute["Dynamic Compute Layer: Karpenter JIT Provisioned"]
                    subgraph SpotFleet["Diversified EC2 Spot Instances (m6i, m5, m5a, m6a)"]
                        RAY_WORKER_1["Ray Worker Pod 1\n- 4 CPU / 16GiB RAM\n- 4GiB /dev/shm tmpfs\n- Plasma Store: 3.6GiB"]
                        RAY_WORKER_2["Ray Worker Pod 2\n- Ingestion & Validation\n- Feature Extraction"]
                        RAY_WORKER_N["Ray Worker Pod N\n- Ray Train Distributed ML\n- Scale-to-Zero Capable"]
                    end
                end
            end
        end

        subgraph Eventing["Event-Driven Interruption & Orchestration"]
            EB_SPOT["AWS EventBridge (Spot Interruption & Rebalance Notice)"]
            SQS_KARP["SQS Interruption Queue\n(ray-platform-test-eks-karpenter-interruption)"]
            EB_CRON["EventBridge Cron Trigger (rate: 15m)"]
            LAMBDA["Discovery Lambda (S3 Poller & Ledger Registrar)"]
        end

        subgraph Storage["Storage & Transactional Lakehouse"]
            S3_DATA[("Amazon S3 Data Bucket\n- incoming/ (Raw CSVs)\n- quarantine/ (Ambiguous Rows)\n- iceberg-warehouse/ (Parquet)\n- models/ (LightGBM Artifacts)")]
            DDB_LEDGER[("DynamoDB Processing Ledger\n(ray_processing_ledger)\n- Conditional Locks\n- Idempotency Tracking")]
            GLUE_CATALOG[("AWS Glue Data Catalog\n(corporate_data_db)")]
        end

        subgraph Registry["Container & Artifact Registry"]
            ECR["Amazon ECR: ray-data-processor"]
        end

        subgraph Logs["Observability & Auditing"]
            CW_LOGS["Amazon CloudWatch Logs\n(/aws/eks/ray-platform-test/workloads)"]
        end
    end

    S1 -->|"Upload Raw CSV"| S3_DATA
    S2 -->|"Upload Raw CSV"| S3_DATA
    EB_CRON -->|"Trigger Discovery"| LAMBDA
    LAMBDA -->|"Inspect S3 incoming/"| S3_DATA
    LAMBDA <-->|"Acquire Atomic Lease"| DDB_LEDGER
    LAMBDA -->|"Submit RayJob CRD"| EKS_API
    DEV -->|"Git Push"| GHA
    GHA -->|"Authenticate via OIDC"| OIDC
    GHA -->|"Build & Push Container"| ECR
    GHA -->|"Deploy Helm & Manifests"| EKS_API
    EKS_API -->|"Reconcile RayJob"| KUBERAY
    KUBERAY -->|"Manage Cluster Lifecycle"| RAY_HEAD
    RAY_HEAD -->|"Workload Demand (Scale 0 to 8)"| RAY_WORKER_1
    RAY_HEAD -->|"Demand Triggers Unschedulable Pods"| KARP_CTRL
    KARP_CTRL -->|"Launch EC2 Spot Fleet (<45s)"| SpotFleet
    EB_SPOT -->|"2-Minute Preemption Warning"| SQS_KARP
    SQS_KARP -->|"Poll & Proactive Cordon/Drain"| KARP_CTRL
    RAY_WORKER_1 <-->|"Read Raw CSVs"| S3_DATA
    RAY_WORKER_1 <-->|"Update Stage Progress"| DDB_LEDGER
    RAY_WORKER_1 -->|"Commit ACID Upserts"| GLUE_CATALOG
    RAY_WORKER_1 -->|"Write Parquet & Manifests"| S3_DATA
    RAY_WORKER_1 -->|"Quarantine Ambiguous Records"| S3_DATA
    RAY_HEAD -->|"Export Metrics (:8080)"| PROM
    RAY_WORKER_1 -->|"Export Metrics (:8080)"| PROM
    PROM -->|"Visualize"| GRAFANA
    FLUENT -->|"Ship Pod Logs via PrivateLink"| CW_LOGS
```

---

## 02 — Network Isolation & Zero-Trust Architecture

```mermaid
flowchart TD
    subgraph InternetZone["Public Internet (External)"]
        CLIENT["Authenticated Developer / CI Runner"]
    end

    subgraph AWS_Cloud["AWS Cloud (us-east-1)"]
        IGW["Internet Gateway (IGW)"]

        subgraph VPC["VPC: 10.0.0.0/16 (Isolated Network Boundary)"]
            subgraph PublicSubnets["Tier 1: Public Subnets (10.0.0.0/20, 10.0.16.0/20, 10.0.32.0/20)"]
                NAT_A["NAT Gateway (us-east-1a)"]
                NAT_B["NAT Gateway (us-east-1b)"]
                ALB_INGRESS["Private/Internal ALB Ingress Controller\n(Port 443 with TLS 1.3 Termination)"]
            end

            subgraph PrivateComputeSubnets["Tier 2: Private Compute Subnets (10.0.128.0/20, 10.0.144.0/20, 10.0.160.0/20)"]
                direction TB
                subgraph SG_ControlPlane["Security Group: EKS Control Plane"]
                    EKS_ENI["EKS Managed ENIs\n- Private API Server Endpoint (:443)\n- No Public Route"]
                end

                subgraph SG_SystemNodes["Security Group: System Node Group"]
                    SYSTEM_NODE["System EC2 Instances (m5.large)\n- KubeRay Operator\n- Karpenter Controller\n- CoreDNS (:53)\n- Prometheus (:9090)"]
                end

                subgraph SG_KarpenterNodes["Security Group: Karpenter Worker Fleet (karpenter.sh/discovery)"]
                    HEAD_POD["Ray Head Pod\n- GCS: 6379\n- Client: 10001\n- Dashboard: 8265\n- Metrics: 8080"]
                    WORKER_PODS["Ray Worker Pods\n- Intra-Ray: 10000-19999\n- Zero Inbound from Internet\n- IMDSv2 Hop Limit = 1"]
                end

                subgraph K8s_Network_Policy["Kubernetes NetworkPolicy Enforcement (Calico / VPC CNI)"]
                    NP_INGRESS["Default Deny All Ingress\nAllow Only Head <--> Worker on Ray Ports"]
                    NP_EGRESS["Restricted Egress\nAllow Only VPC CIDR + AWS PrivateLink Endpoints + DNS:53"]
                end
            end

            subgraph IsolatedDataSubnets["Tier 3: Isolated Data Subnets (10.0.192.0/20, 10.0.208.0/20, 10.0.224.0/20)"]
                DATA_ENIS["Isolated ENIs (No Default Route / No NAT Access)"]
            end

            subgraph PrivateLinkEndpoints["AWS PrivateLink & Gateway VPC Endpoints (Zero Internet Egress)"]
                direction LR
                VPCE_S3_GW["S3 Gateway Endpoint\n(Prefix List: pl-63a5400a)\n(Bucket Policy Restricted)"]
                VPCE_DDB_GW["DynamoDB Gateway Endpoint\n(Prefix List: pl-6ba54002)\n(Table Policy Restricted)"]
                VPCE_ECR_API["ECR API Interface Endpoint (:443)"]
                VPCE_ECR_DKR["ECR DKR Interface Endpoint (:443)"]
                VPCE_STS["STS Interface Endpoint (:443)"]
                VPCE_CW["CloudWatch Logs Endpoint (:443)"]
                VPCE_SQS["SQS Interface Endpoint (:443)"]
                VPCE_KMS["KMS Interface Endpoint (:443)"]
            end
        end

        subgraph AWSServices["AWS Managed Services (Private Backbone Access Only)"]
            S3["Amazon S3 Buckets (test-ray-platform-*)"]
            DDB["Amazon DynamoDB (ray_processing_ledger)"]
            ECR["Amazon ECR Registry"]
            CW["Amazon CloudWatch Logs"]
            STS["AWS Security Token Service (STS)"]
            SQS["Amazon SQS (Karpenter Interruption)"]
            KMS["AWS Key Management Service (KMS)"]
        end
    end

    CLIENT -->|"TLS VPN / Bastion (SSM Session Mgr)"| EKS_ENI
    IGW -.->|"Egress Only for Updates via NAT"| NAT_A
    NAT_A -.->|"No Ingress Allowed"| PrivateComputeSubnets
    EKS_ENI <-->|"Mutual TLS Port 10250 (Kubelet)"| SYSTEM_NODE
    EKS_ENI <-->|"Mutual TLS Port 10250 (Kubelet)"| HEAD_POD
    HEAD_POD <-->|"RPC Ports: 6379, 10001, 10000-19999"| WORKER_PODS
    WORKER_PODS -->|"VPC Route (No NAT cost)"| VPCE_S3_GW
    WORKER_PODS -->|"VPC Route (No NAT cost)"| VPCE_DDB_GW
    WORKER_PODS -->|"Private ENI (Port 443)"| VPCE_ECR_API
    WORKER_PODS -->|"Private ENI (Port 443)"| VPCE_ECR_DKR
    WORKER_PODS -->|"Private ENI (Port 443)"| VPCE_STS
    WORKER_PODS -->|"Private ENI (Port 443)"| VPCE_CW
    WORKER_PODS -->|"Private ENI (Port 443)"| VPCE_SQS
    WORKER_PODS -->|"Private ENI (Port 443)"| VPCE_KMS
    VPCE_S3_GW --> S3
    VPCE_DDB_GW --> DDB
    VPCE_ECR_API --> ECR
    VPCE_ECR_DKR --> ECR
    VPCE_STS --> STS
    VPCE_CW --> CW
    VPCE_SQS --> SQS
    VPCE_KMS --> KMS
```

---

## 03 — Compute Architecture & Capacity Tiering

```mermaid
flowchart TD
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
            subgraph Node_System["EC2 Instance: m7g.xlarge (Graviton3 On-Demand | us-east-1a)"]
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
                
                subgraph DiversifiedPools["Diversified Graviton EC2 Spot Instances (3 AZs x 8 Types = 24 Pools)"]
                    direction LR
                    INSTANCE_M7G["m7g.xlarge / 2xlarge\n(AWS Graviton3 ARM64)"]
                    INSTANCE_M6G["m6g.xlarge / 2xlarge\n(AWS Graviton2 ARM64)"]
                    INSTANCE_C7G["c7g.2xlarge / 4xlarge\n(Compute Graviton3)"]
                    INSTANCE_R7G["r7g.xlarge / 2xlarge\n(Memory Graviton3)"]
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

    K8S_API <--> K8S_SCHED
    K8S_API <--> KUBERAY
    K8S_API <--> KARP_CTRL
    KUBERAY -->|"Deploys & Monitors"| RayHeadContainer
    HEAD_AUTOSCALER -->|"Requests Worker Replicas (0 to 8)"| K8S_API
    K8S_SCHED -->|"Fails to Place Worker Pods (Insufficient Capacity)"| WorkerPods
    WorkerPods -->|"Unschedulable (Pending State)"| KARP_CTRL
    KARP_CTRL -->|"Direct AWS EC2 Fleet API (<45s)"| DiversifiedPools
    DiversifiedPools -->|"Node Registers via EKS Access Entry"| ACCESS_ENTRY
    ACCESS_ENTRY -->|"Authenticates EC2_LINUX"| K8S_API
    K8S_SCHED -->|"Schedules Pending Workers onto Nodes"| WorkerPods
    EVENTBRIDGE -->|"2-Min Interruption Notice"| SQS_QUEUE
    SQS_QUEUE -->|"Karpenter Polls SQS"| KARP_CTRL
    KARP_CTRL -->|"Proactive Cordon & Evict"| WorkerPods
    HEAD_AUTOSCALER -->|"Idle > 60s: Scales Workers to 0"| WorkerPods
    KARP_CTRL -->|"Consolidates & Terminates Empty EC2 Nodes"| DiversifiedPools
```

---

## 04 — End-to-End Pipeline & Data Processing Flow

```mermaid
flowchart TD
    subgraph S0_Ingestion["Stage 0: Ingestion & Trigger"]
        CSV_S1["Raw S1 CSV: Supply Chain (1,200 rows)"]
        CSV_S2["Raw S2 CSV: Financial Data (1,200 rows)"]
        S3_IN["S3: incoming/"]
        LAMBDA["Discovery Lambda"]
        DDB_LEDGER[("DynamoDB Ledger: ray_processing_ledger")]
        K8S_RAYJOB["RayJob Submission (ray-job.yaml)"]
    end

    subgraph S1_Validation["Stage 1: Dynamic Schema Inspection & Validation"]
        RAY_DATA_READ["Ray Data: read_csv (Distributed Slices)"]
        SCHEMA_DETECT["Dynamic Schema Inspector\n- Detect Unknown Columns\n- Identify Tax ID, Name, Revenue Candidates\n- Handle Missing / Corrupt Types"]
        VALID_RECORDS["Validated Record Stream"]
        CORRUPT_RECORDS["Unparseable Records"]
        S3_MALFORMED["S3: dead-letter/malformed/"]
    end

    subgraph S2_Normalization["Stage 2: Canonical Normalization & Cleaning"]
        CLEAN_TEXT["String Sanitization\n- Lowercase & Unicode normalize\n- Strip Corporate Suffixes (Inc, LLC, Corp, GmbH, Ltd)\n- Whitespace collapsing"]
        CLEAN_TAX["Tax ID Normalization\n- Strip hyphens, spaces, punctuation\n- Uppercase alphanumeric"]
        CLEAN_GEO["ISO Country Code Standardization\n- Map aliases to ISO 3166-1 alpha-2"]
    end

    subgraph S3_EntityResolution["Stage 3: Multi-Tier Deterministic Entity Resolution"]
        ACTOR_CALL["Call EntityResolver Actor\n(Pinned via entity_resolver_slot: 1)"]
        MATCH_TIER1{"Tier 1:\nExact Tax ID Match?"}
        MATCH_TIER2{"Tier 2:\nToken Sort Ratio >= 0.90\n& Country / Year Match?"}
        MATCH_TIER3{"Tier 3:\nAmbiguous Score\n(0.65 <= Ratio < 0.90)?"}
        ASSIGN_EXISTING["Merge with Existing Entity\n(Assign Known Entity ID)"]
        ASSIGN_NEW["Mint New Canonical ID\n(UUIDv5: COMP-XXXXXXXX-XXXX)"]
        QUARANTINE_RECORD["Quarantine Ambiguous Entity\n(Human Review Queue)"]
        S3_QUARANTINE["S3: quarantine/ambiguous_entities/"]
    end

    subgraph S4_ML_Training["Stage 4: Ray Train Distributed Machine Learning"]
        FEATURE_ENG["Feature Engineering\n- Log Transform Target (Annual Revenue)\n- One-Hot Country & Industry Encodings\n- ESG & Risk Score Scaling"]
        TRAIN_SPLIT["Distributed Train/Test Split (80/20)"]
        RAY_TRAINER["Ray Train Distributed Regressor\n(Gradient Boosting / LightGBM)"]
        EVAL_METRICS["Model Evaluation\n- Target R² >= 0.85\n- Calculate RMSE & MAE"]
        SAVE_MODEL["Persist Model Artifacts\n- S3: models/model.tar.gz\n- S3: models/metrics.json"]
    end

    subgraph S5_Lakehouse["Stage 5: Apache Iceberg Transactional Lakehouse"]
        ICEBERG_TABLE[("Apache Iceberg Table:\ncorporate_data_db.corporate_registry")]
        GLUE_CATALOG[("AWS Glue Data Catalog (Lock & Metastore)")]
        S3_WAREHOUSE[("S3: iceberg-warehouse/corporate_registry/\n- Data Parquet Files\n- Avro Manifests & Snapshot Logs")]
    end

    subgraph S6_Finalize["Stage 6: Ledger Finalization & Audit"]
        AUDIT_METRICS["Compile Run Statistics\n- Total Rows Processed\n- Entities Resolved\n- Quarantine Count\n- Model R² Score"]
        DDB_COMPLETE[("Update DynamoDB Status: COMPLETED\n(Atomic Conditional Update)")]
    end

    CSV_S1 --> S3_IN
    CSV_S2 --> S3_IN
    S3_IN --> LAMBDA
    LAMBDA <-->|"Conditional Lease Lock"| DDB_LEDGER
    LAMBDA -->|"Submit Job"| K8S_RAYJOB
    K8S_RAYJOB --> RAY_DATA_READ
    RAY_DATA_READ --> SCHEMA_DETECT
    SCHEMA_DETECT -->|Valid Schema| VALID_RECORDS
    SCHEMA_DETECT -->|Corrupt Schema| CORRUPT_RECORDS
    CORRUPT_RECORDS --> S3_MALFORMED
    VALID_RECORDS --> CLEAN_TEXT
    CLEAN_TEXT --> CLEAN_TAX
    CLEAN_TAX --> CLEAN_GEO
    CLEAN_GEO --> ACTOR_CALL
    ACTOR_CALL --> MATCH_TIER1
    MATCH_TIER1 -->|Yes (Confidence: 1.0)| ASSIGN_EXISTING
    MATCH_TIER1 -->|No| MATCH_TIER2
    MATCH_TIER2 -->|Yes (Confidence >= 0.90)| ASSIGN_EXISTING
    MATCH_TIER2 -->|No| MATCH_TIER3
    MATCH_TIER3 -->|Yes (0.65 - 0.89)| QUARANTINE_RECORD
    MATCH_TIER3 -->|No (Confidence < 0.65)| ASSIGN_NEW
    QUARANTINE_RECORD --> S3_QUARANTINE
    ASSIGN_EXISTING --> FEATURE_ENG
    ASSIGN_NEW --> FEATURE_ENG
    FEATURE_ENG --> TRAIN_SPLIT
    TRAIN_SPLIT --> RAY_TRAINER
    RAY_TRAINER --> EVAL_METRICS
    EVAL_METRICS --> SAVE_MODEL
    ASSIGN_EXISTING --> ICEBERG_TABLE
    ASSIGN_NEW --> ICEBERG_TABLE
    ICEBERG_TABLE <-->|"Acquire Catalog Commit Lock"| GLUE_CATALOG
    ICEBERG_TABLE -->|"Write Parquet & Manifests"| S3_WAREHOUSE
    ICEBERG_TABLE --> AUDIT_METRICS
    SAVE_MODEL --> AUDIT_METRICS
    AUDIT_METRICS --> DDB_COMPLETE
```

---

## 05 — Two-Level Autoscaling Lifecycle & Spot Interruption

```mermaid
sequenceDiagram
    autonumber
    box rgb(240, 245, 255) "Workload Layer (KubeRay)"
    participant RayJob as RayJob Pipeline
    participant Head as Ray Head (Autoscaler)
    participant K8sAPI as K8s API Server
    participant Worker as Ray Worker Pods
    end

    box rgb(255, 248, 240) "Compute Layer (Karpenter v1.0.8)"
    participant Sched as K8s Scheduler
    participant Karpenter as Karpenter Controller
    participant EC2Fleet as AWS EC2 Fleet API
    participant SpotNode as EC2 Spot Instance
    end

    box rgb(255, 240, 245) "Interruption Resiliency"
    participant EventBridge as AWS EventBridge
    participant SQS as SQS Interruption Queue
    end

    RayJob->>Head: Submit parallel ingestion & training tasks
    Head->>Head: Detect pending tasks > CPU slots (Backlog trigger)
    Head->>K8sAPI: Patch RayCluster replicas (0 -> 4 worker pods)
    K8sAPI->>Sched: Schedule 4 worker pods
    Sched-->>K8sAPI: Pods in "Pending" (Insufficient node capacity)
    Karpenter->>K8sAPI: Watch unschedulable pending pods
    Karpenter->>Karpenter: Calculate binpack & select cheapest diversified Spot type
    Karpenter->>EC2Fleet: Request EC2 Spot instance (e.g., m6i.2xlarge)
    EC2Fleet-->>SpotNode: Launch EC2 instance (AL2023, IMDSv2)
    SpotNode->>K8sAPI: Register via EKS Access Entry (EC2_LINUX)
    K8sAPI-->>Sched: Node condition: Ready
    Sched->>K8sAPI: Bind 4 pending Ray worker pods to Spot Node
    K8sAPI->>Worker: Start containers (mount 4GiB /dev/shm)
    Worker->>Head: Connect to GCS (:6379) & register Plasma store
    Head->>Worker: Dispatch data ingestion & training tasks
    Worker-->>Head: Tasks completed successfully
    Head->>Head: Worker idle timer > 60 seconds (idleTimeoutSeconds: 60)
    Head->>K8sAPI: Scale down replicas (4 -> 0)
    K8sAPI->>Worker: Terminate worker pods
    Karpenter->>K8sAPI: Detect node is empty (consolidationPolicy: WhenEmptyOrUnderutilized)
    Karpenter->>Karpenter: Wait 60s consolidation timer
    Karpenter->>K8sAPI: Cordon & Drain EC2 Spot Node
    Karpenter->>EC2Fleet: Terminate EC2 instance
    EventBridge->>SQS: Send EC2 Spot Interruption / Rebalance event
    SQS->>Karpenter: Karpenter polls SQS interruption queue
    Karpenter->>K8sAPI: Immediately cordon affected Spot node
    Karpenter->>K8sAPI: Initiate graceful pod eviction (eviction timeout: 60s)
    Karpenter->>EC2Fleet: Proactively request replacement Spot instance
    Worker->>Head: Report graceful shutdown (Ray task lineage rebuilds state)
```

---

## 06 — Ray Worker Node & Pod Internal Topology

```mermaid
flowchart TD
    subgraph Host["AWS EC2 Graviton Spot Host (e.g., m7g.xlarge / m7g.2xlarge)"]
        direction TB

        subgraph OS_Layer["Host Operating System: Ubuntu Linux (EKS Optimized LTS)"]
            KERNEL["Linux Kernel 6.1 (cgroups v2 enabled)"]
            IMDS["IMDSv2 (Enforced Hop Limit: 1)"]
            EBS_DISK["EBS Volume: 50 GiB gp3 (AWS KMS Encrypted)"]
            ENI["VPC ENI (Allocated Pod IP via AWS VPC-CNI)"]
        end

        subgraph Kubelet_Runtime["Kubernetes Node Agents"]
            KUBELET["Kubelet Daemon (Node Condition: Ready)"]
            CONTAINERD["containerd Container Runtime"]
            FLUENT_POD["AWS Fluent Bit DaemonSet Pod (Log Forwarder)"]
        end

        subgraph Worker_Pod["Ray Worker Pod (app.kubernetes.io/name: ray-worker)"]
            direction TB

            subgraph Pod_Security["Pod Security & Identity Context"]
                SA["ServiceAccount: ray-pipeline-sa (IRSA Workload Identity)"]
                TOLERATION["Toleration: workload-role=ray-worker:NoSchedule"]
                AFFINITY["nodeSelector: workload-role=ray-worker"]
            end

            subgraph Memory_Architecture["Memory Architecture & IPC Optimization"]
                direction LR
                SHM["/dev/shm tmpfs Mount (4 GiB Memory Backed)"]
                PLASMA["Apache Arrow Plasma Object Store\n(object-store-memory: 3,865,470,566 bytes ~ 3.6 GiB)\n- Zero-Copy IPC Shared Memory\n- Prevents SIGBUS & Out-Of-Memory"]
                HEAP["Container Heap & Worker Process Memory (~8.4 GiB)"]
                SHM --- PLASMA
            end

            subgraph Core_Processes["Ray Worker Processes (3 CPU Allocation)"]
                RAYLET["Raylet Daemon (Node Agent)\n- Node Manager & Scheduler\n- Heartbeat to GCS (:6379)\n- Exports Prometheus Metrics (:8080)"]
                WORKER_1["Python Worker Process 1\n- CSV Chunk Ingestion & Schema Check"]
                WORKER_2["Python Worker Process 2\n- Levenshtein & Token Sort Computation"]
                WORKER_3["Python Worker Process 3\n- Distributed ML / LightGBM Training"]
                RAYLET <-->|"Local IPC / Unix Domain Socket"| WORKER_1
                RAYLET <-->|"Local IPC / Unix Domain Socket"| WORKER_2
                RAYLET <-->|"Local IPC / Unix Domain Socket"| WORKER_3
            end

            subgraph Custom_Resources["Custom Resources Advertisement"]
                SLOT["Custom Resource: entity_resolver_slot: 1\n(Controls actor placement boundaries)"]
            end
        end
    end

    KERNEL --> CONTAINERD
    CONTAINERD --> Worker_Pod
    SHM -->|"Fast Shared Memory Access"| WORKER_1
    SHM -->|"Fast Shared Memory Access"| WORKER_2
    SHM -->|"Fast Shared Memory Access"| WORKER_3
    KUBELET <--> CONTAINERD
    FLUENT_POD -->|"Tail Container Logs: /var/log/pods"| Worker_Pod
```

---

## 07 — Zero-Trust Security, Identity & Cryptographic Architecture

```mermaid
flowchart TD
    subgraph Identity_Providers["Identity & Authentication Providers"]
        AWS_IAM["AWS Identity & Access Management (IAM)"]
        OIDC_EKS["EKS IAM OpenID Connect (OIDC) Provider\noidc.eks.us-east-1.amazonaws.com/id/..."]
        GHA_OIDC["GitHub Actions OIDC Provider\ntoken.actions.githubusercontent.com"]
    end

    subgraph EKS_Auth["EKS Modern Authentication Engine"]
        ACCESS_ENTRY["EKS Access Entries (v1.30+)\n- Zero aws-auth ConfigMap\n- Principal: karpenter-node-role\n- Type: EC2_LINUX"]
        K8S_RBAC["Kubernetes RBAC (ClusterRole / RoleBinding)\n- Principle of Least Privilege\n- Namespace Scoped: ray-system"]
    end

    subgraph ServiceAccounts["Kubernetes ServiceAccounts (IRSA Bound)"]
        SA_RAY["ServiceAccount: ray-pipeline-sa\nannotation: eks.amazonaws.com/role-arn = ray-workload-role"]
        SA_KARP["ServiceAccount: karpenter\nannotation: eks.amazonaws.com/role-arn = karpenter-controller-role"]
    end

    subgraph Cryptographic_Foundation["Cryptographic Encryption Layer (AWS KMS)"]
        KMS_CMK["AWS KMS Customer Managed Key (CMK)\nalias/ray-platform-test-key\n- Automatic 1-Year Key Rotation\n- Enforces Envelope Encryption"]
    end

    subgraph AWS_Resources["Protected AWS Resources (Encrypted at Rest & in Transit)"]
        S3_DATA[("Amazon S3 Buckets\n- Server-Side Encryption: aws:kms\n- Bucket Policy: Deny Non-TLS (aws:SecureTransport)\n- Block All Public Access: TRUE")]
        DDB[("Amazon DynamoDB: ray_processing_ledger\n- KMS Managed Encryption\n- Point-In-Time Recovery (PITR) Enabled")]
        EBS[("EC2 Host EBS Volumes (gp3)\n- KMS CMK Encrypted Blocks")]
        SQS_INT[("SQS Interruption Queue\n- KMS SQS SSE Enabled")]
        ECR_REG[("Amazon ECR: ray-data-processor\n- KMS Encryption & Image Scan On Push")]
    end

    subgraph Pod_Runtime_Security["Pod & Host Hardening (Defense-in-Depth)"]
        IMDSV2["IMDSv2 Enforced\n- HttpTokens: Required\n- HttpPutResponseHopLimit: 1\n(Blocks Pod Credential Theft)"]
        SEC_CTX["Pod SecurityContext\n- allowPrivilegeEscalation: false\n- readOnlyRootFilesystem: true (where feasible)\n- drop: ALL capabilities"]
        NET_POL["Kubernetes NetworkPolicy\n- Default Deny Ingress\n- Whitelist Intra-Ray RPC (:6379, :10001)"]
    end

    OIDC_EKS --> SA_RAY
    OIDC_EKS --> SA_KARP
    GHA_OIDC -->|"Federated CI/CD AssumeRole"| AWS_IAM
    AWS_IAM --> ACCESS_ENTRY
    SA_RAY -->|"Assumes via STS AssumeRoleWithWebIdentity"| AWS_IAM
    SA_KARP -->|"Assumes via STS AssumeRoleWithWebIdentity"| AWS_IAM
    KMS_CMK -.->|"Encrypts Data at Rest"| S3_DATA
    KMS_CMK -.->|"Encrypts Ledger at Rest"| DDB
    KMS_CMK -.->|"Encrypts Node Volumes"| EBS
    KMS_CMK -.->|"Encrypts Interruption Messages"| SQS_INT
    KMS_CMK -.->|"Encrypts Container Images"| ECR_REG
    ACCESS_ENTRY --> EBS
    IMDSV2 --- SEC_CTX
    SEC_CTX --- NET_POL
```

---

## 08 — Observability, Metrics & Centralized Logging Architecture

```mermaid
flowchart TD
    subgraph Workload_EKS["Amazon EKS Workload Pods (ray-system namespace)"]
        HEAD_METRICS["Ray Head Pod\n- Metrics Server (:8080)\n- Ray Dashboard (:8265)\n- Log Stream: stdout / stderr"]
        WORKER_METRICS["Ray Worker Pods\n- Metrics Server (:8080)\n- Plasma Store Stats\n- Log Stream: stdout / stderr"]
    end

    subgraph Prometheus_Stack["Prometheus Monitoring Stack"]
        POD_MONITOR["Prometheus PodMonitor CRD\n(ray-head-monitor & ray-worker-monitor)\n- Scrape Interval: 15s\n- Port: 8080"]
        PROM_SERVER["Prometheus Server\n- Time Series Database (TSDB)\n- Evaluates AlertRules"]
        GRAFANA["Grafana Visualizer\n- Ray Cluster Health Dashboard\n- Memory & Plasma Pressure\n- Active Actor / Task Counts"]
    end

    subgraph Logging_Stack["Centralized Logging Stack"]
        HOST_LOGS["Host Path: /var/log/pods/ray-system_*"]
        FLUENT_BIT["AWS Fluent Bit DaemonSet\n- Multiline Parser\n- Kubernetes Metadata Filter\n- Buffer & Chunking Engine"]
        CW_LOGS[("Amazon CloudWatch Logs\nLog Group: /aws/eks/ray-platform-test/workloads\n- Retention: 30 Days\n- Encrypted via KMS")]
    end

    subgraph Alerting_Events["Alerting & EventBridge Alarms"]
        CW_ALARMS["CloudWatch Metric Alarms\n- RayHeadOOM\n- SpotInterruptionSpike\n- PipelineFailureRate"]
        SNS_TOPIC["Amazon SNS Topic\n(Platform Alerts)"]
    end

    subgraph Secure_Operator_Access["Secure Operator & Data Scientist Access"]
        ADMIN["Data Scientist / SRE"]
        PORT_FWD["kubectl port-forward (:8265 / :9090 / :3000)"]
        PRIVATE_ALB["Internal ALB + TLS\n(Private Ingress)"]
    end

    HEAD_METRICS -->|"Expose /metrics"| POD_MONITOR
    WORKER_METRICS -->|"Expose /metrics"| POD_MONITOR
    POD_MONITOR -->|"Scrape Targets"| PROM_SERVER
    PROM_SERVER -->|"Query Metrics"| GRAFANA
    HEAD_METRICS -.->|"Write Pod Logs"| HOST_LOGS
    WORKER_METRICS -.->|"Write Pod Logs"| HOST_LOGS
    HOST_LOGS --> FLUENT_BIT
    FLUENT_BIT -->|"Ship via PrivateLink (Port 443)"| CW_LOGS
    PROM_SERVER -.->|"Push High Memory Alert"| CW_ALARMS
    CW_LOGS -->|"Metric Filters"| CW_ALARMS
    CW_ALARMS --> SNS_TOPIC
    ADMIN --> PORT_FWD
    ADMIN --> PRIVATE_ALB
    PORT_FWD --> HEAD_METRICS
    PORT_FWD --> PROM_SERVER
    PORT_FWD --> GRAFANA
    PRIVATE_ALB --> HEAD_METRICS
```

---

## 09 — Apache Iceberg ACID Lakehouse Storage Architecture

```mermaid
flowchart TD
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

    RAY_WORKER -->|"1. Read Current Metadata Pointer"| GLUE_CATALOG
    ATHENA -->|"1. Read Current Metadata Pointer"| GLUE_CATALOG
    GLUE_CATALOG -->|"2. Return Pointer to v2.metadata.json"| META_JSON
    META_JSON -->|"3. References Current Snapshot"| SNAP_LIST
    SNAP_LIST -->|"4. Reads Partition Summaries"| M1
    SNAP_LIST -->|"4. Reads Partition Summaries"| M2
    M1 -->|"5. Predicate Pushdown Pruning"| PARQUET_1
    M2 -->|"5. Predicate Pushdown Pruning"| PARQUET_2
    M2 -->|"5. Predicate Pushdown Pruning"| PARQUET_N
    RAY_WORKER -->|"6a. Stage New Data Files"| S3_Data_Files
    RAY_WORKER -->|"6b. Write New Manifest & Snapshot"| S3_Metadata_Tree
    RAY_WORKER -->|"6c. Atomic Compare-And-Swap (CAS) Lock"| GLUE_CATALOG
    RAY_WORKER -.->|"Divert Unmatched Ambiguities"| S3_QUARANTINE
```

---

## 10 — CI/CD Pipeline, GitOps & Infrastructure Lifecycle

```mermaid
flowchart TD
    subgraph Source_Control["Source Control & Developer Workstation"]
        DEV["Platform / ML Engineer"]
        GIT_REPO["GitHub Repository: main branch"]
        MAKEFILE["Unified Makefile (make tf-apply-all / make deploy-all)"]
    end

    subgraph GHA_Workflow["GitHub Actions CI/CD Pipeline (.github/workflows/)"]
        direction TB

        subgraph Stage_Lint["Stage 1: Static Analysis & Unit Tests"]
            TEST_UNIT["make test-unit\n(Pytest: 7/7 Passing)"]
            TF_LINT["make lint-tf\n(Canonical Formatting)"]
            REPO_VAL["./scripts/validate_repo.sh\n(Layout, Credentials, Syntax)"]
            K8S_VAL["./scripts/validate_k8s_manifests.sh\n(YAML, Resources, CRDs)"]
        end

        subgraph Stage_Auth["Stage 2: Zero-Trust Cloud Authentication"]
            GHA_STS["AWS OIDC Federation\n(aws-actions/configure-aws-credentials)\n- Role: gha-deployment-role\n- Zero Long-Lived Secrets"]
        end

        subgraph Stage_Terraform["Stage 3: Terraform Layered Provisioning"]
            TF_BOOT["01-bootstrap: S3 State Bucket & Lock Table"]
            TF_NET["02-network: VPC, 3 AZs, PrivateLink Endpoints"]
            TF_EKS["03-eks: EKS 1.30, System NodeGroup, Karpenter Module"]
            TF_DATA["04-data: S3 Buckets, DynamoDB Ledger, KMS CMK, Glue"]
            TF_PLAT["05-platform: ECR Repository & Base Platform Config"]
            TF_BOOT --> TF_NET --> TF_EKS --> TF_DATA --> TF_PLAT
        end

        subgraph Stage_Docker["Stage 4: Container Build & Push"]
            DOCKER_BUILD["Docker Build (Multi-Stage Build)\n- Base: Ray 2.40.0-py310\n- Dependencies: PyIceberg, LightGBM, AWS SDK"]
            ECR_PUSH["Docker Push to Amazon ECR\n(123456789012.dkr.ecr.us-east-1.amazonaws.com)"]
        end

        subgraph Stage_K8s["Stage 5: Kubernetes & Helm GitOps Deployment"]
            HELM_KARP["Helm Install Karpenter v1.0.8"]
            APPLY_CRDS["kubectl apply:\n- EC2NodeClass\n- NodePool (Spot & On-Demand)"]
            HELM_KUBERAY["Helm Install KubeRay Operator v1.2.2"]
            APPLY_RAYCLUSTER["kubectl apply:\n- ray-cluster.yaml\n- ray-podmonitor.yaml\n- rbac.yaml"]
        end

        subgraph Stage_Verification["Stage 6: Smoke Test & Job Execution"]
            SMOKE_TEST["make ray-smoke-test\n(Submit lightweight Ray job)"]
            JOB_SUBMIT["Submit RayJob CRD\n(Data Processing & LightGBM Training)"]
            E2E_VERIFY["make e2e-verify\n(Assert Iceberg snapshot & DDB ledger)"]
        end
    end

    DEV -->|"git push origin main"| GIT_REPO
    DEV -.->|"Local Orchestration"| MAKEFILE
    GIT_REPO --> Stage_Lint
    Stage_Lint --> Stage_Auth
    Stage_Auth --> Stage_Terraform
    Stage_Terraform --> Stage_Docker
    Stage_Docker --> Stage_K8s
    Stage_K8s --> Stage_Verification
```

---

## 11 — AWS Serverless Alternative Architecture

```mermaid
flowchart TD
    subgraph TriggerLayer["Trigger & Event Ingestion"]
        S3_EVENT["Amazon EventBridge / S3 ObjectCreated"]
        CRON["Amazon EventBridge (Scheduled Cron: cron(0 2 * * ? *))"]
        API["Amazon API Gateway / Manual Step Functions Trigger"]
        S3_RAW["Amazon S3: incoming/\n(Raw CSV Datasets: S1 & S2)"]
    end

    subgraph Orchestration["AWS Step Functions State Machine (Orchestration Engine)"]
        SF_START(["State Machine Start\n(sfn-corporate-data-pipeline)"])

        subgraph S1_Stage["Stage 1: Discovery & Idempotency Claim"]
            L_DISC["AWS Lambda: handler_discovery\n- Computes SHA256 dataset hash\n- DynamoDB Conditional Put: status=CLAIMED\n- Memory: 512MB | Timeout: 60s"]
        end

        subgraph S2_Stage["Stage 2: Dynamic Schema Validation (Distributed Map)"]
            MAP_VALIDATE["Step Functions Distributed Map\n(Parallel Ingestion over Input Files)"]
            L_VAL_S1["AWS Lambda: handler_validator (S1)\n- Supply Chain CSV Dynamic Schema Discovery\n- Normalizes to canonical Pydantic model\n- Memory: 1024MB | Timeout: 120s"]
            L_VAL_S2["AWS Lambda: handler_validator (S2)\n- Financial CSV Dynamic Schema Discovery\n- Normalizes to canonical Pydantic model\n- Memory: 1024MB | Timeout: 120s"]
        end

        subgraph S3_Stage["Stage 3: Multi-Tier Entity Resolution"]
            L_RES["AWS Lambda: handler_resolver\n- Exact Tax ID Match\n- Fuzzy Levenshtein Name Match (Similarity >= 0.88)\n- Country & Founded Year Corroboration\n- Quarantines Ambiguous Records\n- Memory: 2048MB | Timeout: 300s"]
        end

        subgraph S4_Stage["Stage 4: Apache Iceberg Lakehouse Sink"]
            L_ICE["AWS Lambda: handler_iceberg_sink\n- PyIceberg ACID Upsert\n- AWS Glue Catalog Lock / Snapshot Commit\n- Partitioned Snappy Parquet\n- Memory: 2048MB | Timeout: 300s"]
        end

        subgraph S5_Stage["Stage 5: Gradient Boosting Regressor Training"]
            L_TRAIN["AWS Lambda: handler_trainer\n- Feature Engineering: Log-Revenue, Age, Confidence\n- Scikit-Learn GradientBoostingRegressor (or XGBoost)\n- Evaluates R^2 >= 0.85, RMSE, MAE\n- Serializes model to S3 /tmp\n- Memory: 3072MB | Timeout: 600s"]
        end

        subgraph S6_Stage["Stage 6: Ledger Finalization & Telemetry"]
            L_FIN["AWS Lambda: handler_finalizer\n- DynamoDB Ledger Status Update: COMPLETED\n- Emits CloudWatch Custom Metrics\n- Emits Summary JSON Payload\n- Memory: 512MB | Timeout: 60s"]
        end

        subgraph Failure_Stage["Error Handling & Dead-Letter Routing"]
            CATCH["Step Functions Catch States.ALL\n(Retry: 3x with Exponential Backoff)"]
            SQS_DLQ["Amazon SQS Dead-Letter Queue (DLQ)\n(14-Day Message Retention)"]
            DDB_FAIL["DynamoDB Ledger Status Update: FAILED"]
        end
    end

    subgraph StateStorage["State, Catalog & Storage Layer"]
        DDB[("Amazon DynamoDB\nray_processing_ledger\n(PK: execution_id, SK: timestamp)")]
        GLUE[("AWS Glue Data Catalog\ncorporate_data_db.corporate_registry")]
        S3_WH["Amazon S3: iceberg-warehouse/\n(Apache Iceberg v2 Parquet Metadata & Data)"]
        S3_QUAR["Amazon S3: quarantine/\n(Ambiguous Entity Records)"]
        S3_MOD["Amazon S3: models/\n(Trained Regressor revenue_model.joblib)"]
    end

    subgraph Telemetry["Observability & Monitoring"]
        CW_LOGS["Amazon CloudWatch Logs\n(/aws/lambda/sfn-corporate-*)"]
        CW_METRICS["Amazon CloudWatch Metrics\n(ExecutionDuration, RecordsProcessed, ModelR2)"]
    end

    %% Trigger Wiring
    S3_EVENT --> SF_START
    CRON --> SF_START
    API --> SF_START
    S3_RAW -.-> L_DISC
    S3_RAW -.-> L_VAL_S1
    S3_RAW -.-> L_VAL_S2

    %% State Machine Sequential Flow
    SF_START --> L_DISC
    L_DISC --> MAP_VALIDATE
    MAP_VALIDATE --> L_VAL_S1
    MAP_VALIDATE --> L_VAL_S2
    L_VAL_S1 --> L_RES
    L_VAL_S2 --> L_RES
    L_RES --> L_ICE
    L_ICE --> L_TRAIN
    L_TRAIN --> L_FIN

    %% Storage Connections
    L_DISC <-->|Conditional Put| DDB
    L_RES --> S3_QUAR
    L_ICE --> S3_WH
    L_ICE <-->|Snapshot Lock| GLUE
    L_TRAIN --> S3_MOD
    L_FIN -->|Mark Completed| DDB

    %% Error Handling Connections
    L_DISC -.->|Error| CATCH
    MAP_VALIDATE -.->|Error| CATCH
    L_RES -.->|Error| CATCH
    L_ICE -.->|Error| CATCH
    L_TRAIN -.->|Error| CATCH
    CATCH --> SQS_DLQ
    CATCH --> DDB_FAIL

    %% Observability Connections
    L_DISC -.-> CW_LOGS
    L_RES -.-> CW_LOGS
    L_ICE -.-> CW_LOGS
    L_TRAIN -.-> CW_LOGS
    L_FIN -.-> CW_METRICS
```
