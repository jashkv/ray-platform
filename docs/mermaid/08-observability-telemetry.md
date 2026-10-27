# 08 — Observability, Metrics & Centralized Logging Architecture

This document outlines the **Observability, Metrics Collection, and Centralized Logging Pipeline** for the Ray AI Platform on AWS EKS.

---

## Observability Architecture Diagram

```mermaid
flowchart TD
    %% Observability, Metrics & Centralized Logging Architecture
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

    %% Metrics Flow
    HEAD_METRICS -->|"Expose /metrics"| POD_MONITOR
    WORKER_METRICS -->|"Expose /metrics"| POD_MONITOR
    POD_MONITOR -->|"Scrape Targets"| PROM_SERVER
    PROM_SERVER -->|"Query Metrics"| GRAFANA

    %% Log Flow
    HEAD_METRICS -.->|"Write Pod Logs"| HOST_LOGS
    WORKER_METRICS -.->|"Write Pod Logs"| HOST_LOGS
    HOST_LOGS --> FLUENT_BIT
    FLUENT_BIT -->|"Ship via PrivateLink (Port 443)"| CW_LOGS

    %% Alarms Flow
    PROM_SERVER -.->|"Push High Memory Alert"| CW_ALARMS
    CW_LOGS -->|"Metric Filters"| CW_ALARMS
    CW_ALARMS --> SNS_TOPIC

    %% Access Flow
    ADMIN --> PORT_FWD
    ADMIN --> PRIVATE_ALB
    PORT_FWD --> HEAD_METRICS
    PORT_FWD --> PROM_SERVER
    PORT_FWD --> GRAFANA
    PRIVATE_ALB --> HEAD_METRICS
```

---

## Observability Capabilities

### 1. Prometheus Metrics via `PodMonitor`
- Ray natively exposes OpenMetrics on port `:8080`.
- The Prometheus Operator discovers Head and Worker pods automatically via `PodMonitor` CRDs (`ray-podmonitor.yaml`).
- Key metrics tracked include:
  - `ray_node_cpu_utilization`: Core consumption per node.
  - `ray_object_store_memory`: Plasma shared memory occupancy in bytes.
  - `ray_tasks_state`: Real-time queue count of tasks (`RUNNING`, `PENDING_NODE_ASSIGNMENT`).
  - `ray_actors_state`: Health and restart count of the stateful `EntityResolver` actor.

### 2. High-Throughput Centralized Logging
- The AWS Fluent Bit DaemonSet mounts `/var/log/pods` from the host.
- It parses container stdout/stderr, adds Kubernetes namespace/pod metadata, and securely ships log chunks over AWS PrivateLink directly to CloudWatch Logs (`/aws/eks/ray-platform-test/workloads`).
- This eliminates container logging disk exhaustion on Spot nodes.

### 3. Secure Dashboard Access
Access to the Ray Dashboard (port `:8265`) is strictly constrained to private routes:
- Internal access via `kubectl port-forward svc/ray-cluster-kuberay-head-svc 8265:8265`.
- Or private ingress through an internal Application Load Balancer terminating TLS 1.3 within the private VPC boundary.
