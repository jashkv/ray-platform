# 05 — Two-Level Autoscaling Lifecycle & Spot Interruption

This document illustrates the **Two-Level Autoscaling Architecture** operating across the Ray AI Platform, coordinating pod-level autoscaling via the KubeRay In-Tree Autoscaler with infrastructure-level Just-In-Time (JIT) node provisioning via Karpenter `v1.0.8`.

---

## Autoscaling Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    %% Two-Level Autoscaling Lifecycle & Spot Interruption Flow

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

    %% Phase 1: Scale-Up Trigger
    Note over RayJob,K8sAPI: Phase 1: Workload Demand & Pod Autoscaling
    RayJob->>Head: Submit parallel ingestion & training tasks
    Head->>Head: Detect pending tasks > CPU slots (Backlog trigger)
    Head->>K8sAPI: Patch RayCluster replicas (0 -> 4 worker pods)
    K8sAPI->>Sched: Schedule 4 worker pods
    Sched-->>K8sAPI: Pods in "Pending" (Insufficient node capacity)

    %% Phase 2: Karpenter JIT Node Provisioning
    Note over Karpenter,SpotNode: Phase 2: Karpenter JIT Spot Provisioning (<45s)
    Karpenter->>K8sAPI: Watch unschedulable pending pods
    Karpenter->>Karpenter: Calculate binpack & select cheapest diversified Spot type
    Karpenter->>EC2Fleet: Request EC2 Spot instance (e.g., m6i.2xlarge)
    EC2Fleet-->>SpotNode: Launch EC2 instance (AL2023, IMDSv2)
    SpotNode->>K8sAPI: Register via EKS Access Entry (EC2_LINUX)
    K8sAPI-->>Sched: Node condition: Ready
    Sched->>K8sAPI: Bind 4 pending Ray worker pods to Spot Node
    K8sAPI->>Worker: Start containers (mount 4GiB /dev/shm)

    %% Phase 3: Workload Execution
    Note over Head,Worker: Phase 3: Distributed Execution
    Worker->>Head: Connect to GCS (:6379) & register Plasma store
    Head->>Worker: Dispatch data ingestion & training tasks
    Worker-->>Head: Tasks completed successfully

    %% Phase 4: Scale to Zero
    Note over Head,SpotNode: Phase 4: Scale-to-Zero & Node Consolidation
    Head->>Head: Worker idle timer > 60 seconds (idleTimeoutSeconds: 60)
    Head->>K8sAPI: Scale down replicas (4 -> 0)
    K8sAPI->>Worker: Terminate worker pods
    Karpenter->>K8sAPI: Detect node is empty (consolidationPolicy: WhenEmptyOrUnderutilized)
    Karpenter->>Karpenter: Wait 60s consolidation timer
    Karpenter->>K8sAPI: Cordon & Drain EC2 Spot Node
    Karpenter->>EC2Fleet: Terminate EC2 instance
    Note over Karpenter,SpotNode: Worker compute drops to $0.00 / hour

    %% Phase 5: Spot Interruption Resilience
    Note over EventBridge,Worker: Phase 5: Spot Interruption Handling (2-Min Notice)
    EventBridge->>SQS: Send EC2 Spot Interruption / Rebalance event
    SQS->>Karpenter: Karpenter polls SQS interruption queue
    Karpenter->>K8sAPI: Immediately cordon affected Spot node
    Karpenter->>K8sAPI: Initiate graceful pod eviction (eviction timeout: 60s)
    Karpenter->>EC2Fleet: Proactively request replacement Spot instance
    Worker->>Head: Report graceful shutdown (Ray task lineage rebuilds state)
```

---

## State Transition Matrix

```mermaid
stateDiagram-v2
    [*] --> IdleCluster: Cluster Ready (0 Workers, 0 Spot EC2s)
    
    IdleCluster --> PodScaleUp: RayJob Submits Tasks
    state PodScaleUp {
        [*] --> CheckTaskBacklog
        CheckTaskBacklog --> ScaleReplicas: Backlog > 0
        ScaleReplicas --> PodsPending: Workers in Pending State
    }

    PodsPending --> KarpenterJITProvisioning: Unschedulable Event
    state KarpenterJITProvisioning {
        [*] --> FleetEvaluation
        FleetEvaluation --> LaunchEC2: Cheapest Diversified Spot (<45s)
        LaunchEC2 --> EKSNodeJoin: Join via EKS Access Entry
        EKSNodeJoin --> PodsBound: K8s Scheduler Binds Pods
    }

    KarpenterJITProvisioning --> ActiveExecution: Workers Online
    state ActiveExecution {
        [*] --> ProcessData
        ProcessData --> TrainModel
    }

    ActiveExecution --> SpotInterrupted: AWS 2-Min Warning Event
    state SpotInterrupted {
        [*] --> EventBridgeNotice
        EventBridgeNotice --> SQSQueue
        SQSQueue --> KarpenterCordonDrain
        KarpenterCordonDrain --> LineageReconstruct: Evict & Relaunch
    }
    SpotInterrupted --> ActiveExecution: Replacement Node Ready

    ActiveExecution --> ScaleToZero: Tasks Complete (Idle > 60s)
    state ScaleToZero {
        [*] --> WorkersScaledTo0
        WorkersScaledTo0 --> NodeEmpty
        NodeEmpty --> ConsolidationTimer: 60s Delay
        ConsolidationTimer --> NodeTerminated: Terminate EC2 Instance
    }
    ScaleToZero --> IdleCluster: Compute Cost = $0.00
```

---

## Architectural Guarantees

| Metric / Parameter | Value | Technical Enforcement |
| :--- | :--- | :--- |
| **Worker Replicas Min/Max** | `0` to `8` | Defined in `RayCluster` CRD (`kubernetes/ray/ray-cluster.yaml`). |
| **Ray Idle Timeout** | `60 seconds` | Configured via `autoscalerOptions.idleTimeoutSeconds`. |
| **Karpenter Launch Time** | `<45 seconds` | Direct EC2 Fleet API invocation bypassing ASG scaling activities. |
| **Consolidation Policy** | `WhenEmptyOrUnderutilized` | NodePool spec with a `consolidateAfter: 60s` window. |
| **Spot Interruption Notice** | `120 seconds (2 mins)` | Amazon EventBridge forwards EC2 Spot preemption notices to SQS. |
| **Stateful Actor Protection** | Fixed Head placement | `EntityResolver` requires `entity_resolver_slot: 1`, pinned to Ray Head. |
