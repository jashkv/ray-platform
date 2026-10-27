# 06 — Ray Worker Node & Pod Internal Topology

This document details the internal anatomy of a Karpenter-provisioned **Ray Worker EC2 Spot Instance** and its contained **Ray Worker Pod**, highlighting memory management, shared IPC, and process scheduling.

---

## Worker Node Anatomy Diagram

```mermaid
flowchart TD
    %% Internal Topology of a Karpenter-Provisioned Ray Worker Node
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

    %% Wiring
    KERNEL --> CONTAINERD
    CONTAINERD --> Worker_Pod
    SHM -->|"Fast Shared Memory Access"| WORKER_1
    SHM -->|"Fast Shared Memory Access"| WORKER_2
    SHM -->|"Fast Shared Memory Access"| WORKER_3
    KUBELET <--> CONTAINERD
    FLUENT_POD -->|"Tail Container Logs: /var/log/pods"| Worker_Pod
```

---

## Memory & IPC Deep-Dive

### Why Sizing `/dev/shm` at 4 GiB is Essential
Standard Kubernetes/Docker container runtimes default `/dev/shm` to a mere **64 MiB**. 

Ray utilizes Apache Arrow Plasma, an in-memory object store that maps Arrow tabular record batches directly into `/dev/shm`. Multiple worker processes on the same host can read dataset partitions simultaneously without copy operations (Zero-Copy Deserialization).

If `/dev/shm` is left at the default 64 MiB:
1. Any multi-megabyte Arrow Table allocation exceeds the tmpfs threshold.
2. The Linux kernel immediately issues a `SIGBUS` (Bus Error) signal to the worker process.
3. The process crashes immediately without a Python traceback, destabilizing the distributed pipeline.

To prevent this:
- An `emptyDir` with `medium: Memory` and `sizeLimit: 4Gi` is mounted at `/dev/shm`.
- Ray's `object-store-memory` parameter is explicitly capped at `3865470566` bytes (~3.6 GiB), leaving a 400 MiB safety buffer within tmpfs.
- The remaining container memory (~8.4 GiB out of 12 GiB) is dedicated to Python runtime heaps, data structures, and LightGBM model training buffers.

### Resource Allocation Summary

| Resource | Request | Limit | Component / Purpose |
| :--- | :--- | :--- | :--- |
| **CPU** | `3000m` (3 Cores) | `3000m` (3 Cores) | 1 core per Python worker process; prevents CPU throttling. |
| **Memory** | `12 GiB` | `12 GiB` | 3.6 GiB Plasma Object Store + 8.4 GiB Heap / OS cache. |
| **Shared Memory (`/dev/shm`)** | `4 GiB` | `4 GiB` | tmpfs mount backed by host RAM for Apache Arrow IPC. |
| **Root Volume** | `50 GiB` | `50 GiB` | gp3 encrypted with AWS KMS; container layer caching & spooling. |
| **Network** | Dedicated Pod IP | Line rate | AWS VPC-CNI assigns direct VPC IP from private subnet. |
