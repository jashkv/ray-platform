# 06 — Lambda Execution Environment & MicroVM Topology (Serverless Alternative)

This document details the internal architecture, hardware isolation, memory allocation, and runtime topology of an **AWS Lambda Micro-Function Execution Environment**.

---

## 1. Architectural Diagram

```mermaid
flowchart TD
    %% AWS Lambda Execution Environment & MicroVM Topology
    subgraph Host["AWS Bare-Metal Server (Nitro System)"]
        KVM["Linux Kernel-Based Virtual Machine (KVM)"]

        subgraph FirecrackerVM["Isolated AWS Firecracker MicroVM"]
            direction TB

            subgraph MicroVMKernel["MicroVM Dedicated Linux Kernel (v6.x)"]
                CGROUPS["Linux cgroups v2 (CPU Quotas & Memory Enforcers)"]
                SECCOMP["seccomp Filter (Restricted Syscall Boundary)"]
            end

            subgraph StorageBoundaries["Ephemeral Storage & Memory Boundaries"]
                TMP_DISK["Ephemeral Disk: /tmp (512 MB to 2,048 MB)\n- Inode space for PyIceberg local cache\n- Scratch storage for serialized joblib model artifacts"]
                HEAP_MEM["Hardware-Enforced RAM: 512 MB to 3,072 MB\n- In-Memory PyArrow Table Buffer\n- Python 3.12 Process Heap"]
            end

            subgraph RuntimeEnvironment["Language Runtime & Worker Process"]
                INIT_SYS["AWS Lambda Runtime Bootstrap Engine (Rapid)"]
                PY_RUNTIME["Python 3.12 Managed Execution Engine"]

                subgraph LoadedLibraries["Pre-Warmed In-Memory Data Science Engines"]
                    LIB_PYICEBERG["PyIceberg (ACID Lakehouse Client)"]
                    LIB_SKLEARN["Scikit-Learn (GradientBoostingRegressor)"]
                    LIB_ARROW["Apache Arrow (PyArrow Columnar Memory)"]
                    LIB_PANDAS["Pandas DataFrames"]
                    LIB_BOTO3["AWS SDK (boto3 - S3/DynamoDB/Glue/SQS)"]
                end

                subgraph HandlerSlot["Invoked Handler Execution Slot"]
                    HANDLER["handlers.py Entry Point:\n- handler_discovery\n- handler_validator\n- handler_resolver\n- handler_iceberg_sink\n- handler_trainer\n- handler_finalizer"]
                end
            end

            subgraph TelemetryAgent["Telemetry & Log Forwarding"]
                LOG_AGENT["CloudWatch Logs Streaming Daemon\n(Structured JSON Log Buffer)"]
            end
        end
    end

    KVM --> FirecrackerVM
    CGROUPS --> HEAP_MEM
    SECCOMP --> RuntimeEnvironment
    INIT_SYS --> PY_RUNTIME
    PY_RUNTIME --> LoadedLibraries
    LoadedLibraries --> HANDLER
    HANDLER --> TMP_DISK
    HANDLER --> HEAP_MEM
    HANDLER --> LOG_AGENT
```

---

## 2. Technical Topology Breakdown

1. **Firecracker MicroVM Virtualization:**
   Unlike Docker containers that share the host Linux kernel, each AWS Lambda function executes inside an isolated microVM powered by the open-source **Firecracker** hypervisor.
2. **Ephemeral Disk (`/tmp`):**
   Configured with up to 2,048 MB of fast NVMe scratch storage, providing local caching for PyIceberg table metadata and model serialization.
3. **Hardware Memory Limits:**
   Linux `cgroups v2` strictly enforce memory ceilings (up to 3,072 MB in `handler_trainer`).
4. **Structured Telemetry Streaming:**
   The AWS Lambda Rapid initialization engine pipes logs directly to CloudWatch without requiring background DaemonSets like Fluent Bit.
