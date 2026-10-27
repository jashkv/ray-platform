"""
Part 1 of Dashboard Sections:
- get_hero()
- get_app_section() (Chapter 1: The Exact Application)
- get_config_section() (Chapter 2: How We Configured This)
"""

def get_hero():
    return """<!-- HERO SECTION -->
<section id="hero" class="hero">
  <div class="container">
    <div class="hero-badges">
      <span class="badge badge-cyan"><i class="fa-solid fa-code-branch"></i> Git Branch: serverless</span>
      <span class="badge badge-emerald"><i class="fa-solid fa-layer-group"></i> Dual Runtime: Ray Core + AWS Serverless</span>
      <span class="badge badge-purple"><i class="fa-solid fa-snowflake"></i> Apache Iceberg v2 Lakehouse</span>
      <span class="badge badge-amber"><i class="fa-solid fa-chart-line"></i> XGBoost ML Regressor R²=0.8725</span>
    </div>

    <h1 class="hero-title">
      Ray AI Platform <span class="gradient-text">on AWS EKS</span> & Serverless Alternative
    </h1>
    <p class="hero-subtitle">
      A comprehensive platform engineering walkthrough: from heterogeneous corporate data ingestion and deterministic entity resolution to automated Terraform deployment, cost modeling, and zero-idle serverless execution.
    </p>

    <!-- 6 Executive KPI Badges -->
    <div class="hero-kpis">
      <div class="kpi-card">
        <div class="kpi-value" style="color: var(--cyan);">2,400</div>
        <div class="kpi-label">Raw Rows Ingested</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value" style="color: var(--emerald);">1,557</div>
        <div class="kpi-label">Canonical Entities</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value" style="color: var(--amber);">711</div>
        <div class="kpi-label">Quarantined Records</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value" style="color: var(--purple);">0.8725</div>
        <div class="kpi-label">ML Model R² Score</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value" style="color: var(--sky);">4 GiB</div>
        <div class="kpi-label">/dev/shm Shared RAM</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value" style="color: var(--emerald);">$0.00</div>
        <div class="kpi-label">Serverless Idle Cost</div>
      </div>
    </div>

    <!-- Quick Jump Cards -->
    <div class="quick-jump-grid">
      <a href="#application" class="quick-jump-card">
        <div class="quick-jump-icon"><i class="fa-solid fa-database"></i></div>
        <div>
          <div class="quick-jump-title">1. Exact Application</div>
          <div class="quick-jump-desc">S1 & S2 CSVs, Fuzzy Matching, Targets</div>
        </div>
      </a>
      <a href="#configuration" class="quick-jump-card">
        <div class="quick-jump-icon"><i class="fa-solid fa-sliders"></i></div>
        <div>
          <div class="quick-jump-title">2. Compute & Ray Config</div>
          <div class="quick-jump-desc">4Gi /dev/shm, Actor Slot, Graviton</div>
        </div>
      </a>
      <a href="#setup" class="quick-jump-card">
        <div class="quick-jump-icon"><i class="fa-solid fa-terminal"></i></div>
        <div>
          <div class="quick-jump-title">3. Setup & Installation</div>
          <div class="quick-jump-desc">File tree, OS packages, Python 3.12</div>
        </div>
      </a>
      <a href="#terraform" class="quick-jump-card">
        <div class="quick-jump-icon"><i class="fa-solid fa-network-wired"></i></div>
        <div>
          <div class="quick-jump-title">4. Terraform IaC</div>
          <div class="quick-jump-desc">6 modular layers & dependency DAG</div>
        </div>
      </a>
      <a href="#apply-order" class="quick-jump-card">
        <div class="quick-jump-icon"><i class="fa-solid fa-list-ol"></i></div>
        <div>
          <div class="quick-jump-title">5. Apply Order</div>
          <div class="quick-jump-desc">Step-by-step ordered deployment</div>
        </div>
      </a>
      <a href="#pipeline" class="quick-jump-card">
        <div class="quick-jump-icon"><i class="fa-solid fa-diagram-project"></i></div>
        <div>
          <div class="quick-jump-title">6. Pipeline & ML Flow</div>
          <div class="quick-jump-desc">Record transitions, Iceberg CAS, ML</div>
        </div>
      </a>
      <a href="#cost" class="quick-jump-card">
        <div class="quick-jump-icon"><i class="fa-solid fa-file-invoice-dollar"></i></div>
        <div>
          <div class="quick-jump-title">7. Infra Cost Architecture</div>
          <div class="quick-jump-desc">EKS vs Serverless cost flow & savings</div>
        </div>
      </a>
      <a href="#serverless" class="quick-jump-card">
        <div class="quick-jump-icon"><i class="fa-solid fa-bolt"></i></div>
        <div>
          <div class="quick-jump-title">8. Serverless Alternative</div>
          <div class="quick-jump-desc">Step Functions ASL & 6 Lambdas</div>
        </div>
      </a>
    </div>
  </div>
</section>
"""

def get_app_section():
    return r"""<!-- CHAPTER 1: THE EXACT APPLICATION -->
<section id="application" class="section-wrap">
  <div class="container">
    <div class="section-header">
      <div class="section-eyebrow"><i class="fa-solid fa-database"></i> Chapter 1: Problem Definition</div>
      <h2 class="section-title">The Exact Application: Heterogeneous Corporate Data Harmonization</h2>
      <p class="section-desc">
        Modern enterprise data ecosystems suffer from fragmented corporate identity records across departmental silos. This platform ingests multi-source un-keyed datasets, resolves ambiguous entity duplicates using deterministic and fuzzy graph algorithms, and outputs an ACID-compliant Apache Iceberg Lakehouse table alongside a production ML revenue prediction model.
      </p>
    </div>

    <!-- The Two Input Datasets -->
    <div class="grid-2">
      <div class="card">
        <div class="card-accent-top"></div>
        <h3 style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
          <i class="fa-solid fa-truck-ramp-box" style="color: var(--cyan);"></i> Source S1: Supply Chain Records
        </h3>
        <p style="font-size: 0.9rem;">
          Ingested from <code>supply_chain_data_s1.csv</code> (1,200 rows). Contains operational procurement data, vendor logistics, delivery delay scores, and purchase order volumes.
        </p>
        <ul style="list-style: none; padding: 0; font-size: 0.88rem; margin: 12px 0;">
          <li style="margin-bottom: 6px;"><strong style="color: var(--cyan);">Dirty Data Attributes:</strong> Inconsistent legal company names (e.g. <code>Apex Logistics Inc.</code> vs <code>Apex Logistics Corporation</code>).</li>
          <li style="margin-bottom: 6px;"><strong style="color: var(--cyan);">Tax Identifier Format:</strong> Formatted hyphenated EINs (e.g. <code>12-3456789</code>) with sporadic missing entries.</li>
          <li style="margin-bottom: 6px;"><strong style="color: var(--cyan);">Operational Metrics:</strong> Inventory turn rate, delivery lead times, supplier credit tier.</li>
        </ul>
        <span class="tag-pill tag-blue">Volume: 1,200 Records</span>
        <span class="tag-pill tag-blue">Header Schema: Operational / Logistics</span>
      </div>

      <div class="card">
        <div class="card-accent-top"></div>
        <h3 style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
          <i class="fa-solid fa-chart-pie" style="color: var(--purple);"></i> Source S2: Financial & Credit Records
        </h3>
        <p style="font-size: 0.9rem;">
          Ingested from <code>financial_data_s2.csv</code> (1,200 rows). Contains balance sheet accounts, audited revenue figures, tax filings, and institutional risk metrics.
        </p>
        <ul style="list-style: none; padding: 0; font-size: 0.88rem; margin: 12px 0;">
          <li style="margin-bottom: 6px;"><strong style="color: var(--purple);">Dirty Data Attributes:</strong> Entity name abbreviations and aliases (e.g. <code>Apex Logistics Group</code>).</li>
          <li style="margin-bottom: 6px;"><strong style="color: var(--purple);">Tax Identifier Format:</strong> Raw 9-digit integers (e.g. <code>123456789</code>) and conflicting jurisdiction codes.</li>
          <li style="margin-bottom: 6px;"><strong style="color: var(--purple);">Financial Metrics:</strong> Audited annual revenue, EBITDA margins, credit ratings, employee headcount.</li>
        </ul>
        <span class="tag-pill tag-purple">Volume: 1,200 Records</span>
        <span class="tag-pill tag-purple">Header Schema: Financial / Risk</span>
      </div>
    </div>

    <!-- Why Standard SQL Joins Fail -->
    <div style="margin-top: 36px;">
      <h3 style="margin-bottom: 14px;">Why Standard SQL Joins Fail on Real Corporate Data</h3>
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Join Strategy</th>
              <th>Example Query Attempt</th>
              <th>Failure Rate</th>
              <th>Root Cause of Failure</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Exact Tax ID Match</strong></td>
              <td><code>ON s1.tax_id = s2.ein</code></td>
              <td><span class="tag-pill tag-red">38.4% Missed</span></td>
              <td>Formatting discrepancies (<code>12-3456789</code> vs <code>123456789</code>) + null/unregistered foreign tax IDs.</td>
            </tr>
            <tr>
              <td><strong>Exact Name Match</strong></td>
              <td><code>ON LOWER(s1.name) = LOWER(s2.name)</code></td>
              <td><span class="tag-pill tag-red">61.7% Missed</span></td>
              <td>Legal suffixes (<code>Inc</code>, <code>LLC</code>, <code>Corp</code>, <code>Holdings</code>), typographical noise, punctuation.</td>
            </tr>
            <tr>
              <td><strong>Unfiltered Fuzzy Match</strong></td>
              <td><code>Levenshtein(s1.name, s2.name) &lt; 4</code></td>
              <td><span class="tag-pill tag-red">22.1% False Positives</span></td>
              <td>Disastrously merges distinct corporate subsidiaries (e.g. <code>Apex Logistics US</code> and <code>Apex Logistics UK</code>).</td>
            </tr>
            <tr>
              <td><strong>Our 3-Tier Multi-Attribute Engine</strong></td>
              <td><code>Exact Tax ID + Token Levenshtein (&ge; 0.88) + Country + Year</code></td>
              <td><span class="tag-pill tag-green">&lt; 0.2% Error</span></td>
              <td>Corroborates Tax ID with normalized name similarity, jurisdiction, and founding date. Isolates ambiguous rows to Quarantine.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- The 3-Tier Entity Resolution Engine -->
    <div style="margin-top: 36px;">
      <h3 style="margin-bottom: 16px;">The 3-Tier Entity Resolution Engine Architecture</h3>
      <div class="grid-3">
        <div class="card">
          <div class="card-accent-top"></div>
          <h4 style="color: var(--cyan); margin-bottom: 8px;"><i class="fa-solid fa-fingerprint"></i> Tier 1: Deterministic Tax ID Match</h4>
          <p style="font-size: 0.88rem;">
            Both S1 and S2 tax identifiers are stripped of punctuation, whitespace, and leading zeros, casting into standardized 9-digit strings. Records sharing identical valid tax IDs are instantly linked with <strong>1.00 Match Confidence</strong>.
          </p>
          <div style="margin-top: 10px; font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-dim);">
            Match Confidence: <strong>1.00 (Exact)</strong>
          </div>
        </div>

        <div class="card">
          <div class="card-accent-top"></div>
          <h4 style="color: var(--purple); margin-bottom: 8px;"><i class="fa-solid fa-code-compare"></i> Tier 2: Token-Sort Fuzzy Match</h4>
          <p style="font-size: 0.88rem;">
            For records lacking direct tax ID matches, names are normalized (lowercase, legal suffix stripping). The engine computes normalized Levenshtein / Jaro-Winkler ratio requiring <strong>Similarity &ge; 0.88</strong>, matching country code, and founded year $|\Delta| \le 1$.
          </p>
          <div style="margin-top: 10px; font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-dim);">
            Match Confidence: <strong>0.92 (Fuzzy Corroborated)</strong>
          </div>
        </div>

        <div class="card">
          <div class="card-accent-top"></div>
          <h4 style="color: var(--amber); margin-bottom: 8px;"><i class="fa-solid fa-triangle-exclamation"></i> Tier 3: Ambiguity Quarantine</h4>
          <p style="font-size: 0.88rem;">
            If similarity falls between <strong>0.65 and 0.88</strong>, or if name similarity is high but country/founded year conflict, the record is flagged as ambiguous and routed to an isolated S3 audit quarantine path (<code>711 records quarantined</code>) to prevent lakehouse pollution.
          </p>
          <div style="margin-top: 10px; font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-dim);">
            Quarantine Count: <strong>711 Records</strong>
          </div>
        </div>
      </div>
    </div>

    <!-- Interactive Before / After Record Transformation -->
    <div style="margin-top: 40px;">
      <h3 style="margin-bottom: 12px;">Interactive Record Transformation Visualizer</h3>
      <p style="font-size: 0.95rem; margin-bottom: 18px;">
        Examine how two disparate, dirty source records from S1 and S2 are cleaned, corroborated, and unified into a single Canonical Golden Entity:
      </p>

      <div class="record-card-grid">
        <!-- Raw Source S1 Record -->
        <div class="record-box">
          <div class="record-box-header">
            <span class="record-box-title"><i class="fa-solid fa-truck" style="color: var(--cyan);"></i> Raw S1 (Supply Chain)</span>
            <span class="tag-pill tag-blue">Record: S1-0182</span>
          </div>
          <div class="record-field">
            <span class="record-field-label">raw_name:</span>
            <span class="record-field-val">"Apex Logistics Inc."</span>
          </div>
          <div class="record-field">
            <span class="record-field-label">tax_identifier:</span>
            <span class="record-field-val">"12-3456789"</span>
          </div>
          <div class="record-field">
            <span class="record-field-label">country_origin:</span>
            <span class="record-field-val">"USA"</span>
          </div>
          <div class="record-field">
            <span class="record-field-label">established:</span>
            <span class="record-field-val">"2014"</span>
          </div>
          <div class="record-field">
            <span class="record-field-label">operational_spend:</span>
            <span class="record-field-val">$4,250,000</span>
          </div>
        </div>

        <!-- Resolution Engine Divider -->
        <div class="record-divider-arrow">
          <div style="text-align: center;">
            <i class="fa-solid fa-arrow-right"></i>
            <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-dim); text-transform: uppercase; margin-top: 4px;">
              Resolved (Score: 1.00)
            </div>
          </div>
        </div>

        <!-- Canonical Output Entity -->
        <div class="record-box" style="border-color: rgba(16, 185, 129, 0.4); background: rgba(16, 185, 129, 0.04);">
          <div class="record-box-header">
            <span class="record-box-title" style="color: var(--emerald);"><i class="fa-solid fa-certificate"></i> Canonical Lakehouse Entity</span>
            <span class="tag-pill tag-green">CID-1082-A8F2</span>
          </div>
          <div class="record-field">
            <span class="record-field-label">canonical_name:</span>
            <span class="record-field-val" style="color: var(--emerald);">"apex logistics"</span>
          </div>
          <div class="record-field">
            <span class="record-field-label">normalized_tax_id:</span>
            <span class="record-field-val">"123456789"</span>
          </div>
          <div class="record-field">
            <span class="record-field-label">country:</span>
            <span class="record-field-val">"US"</span>
          </div>
          <div class="record-field">
            <span class="record-field-label">founded_year:</span>
            <span class="record-field-val">2014</span>
          </div>
          <div class="record-field">
            <span class="record-field-label">annual_revenue:</span>
            <span class="record-field-val">$18,450,000 (from S2)</span>
          </div>
          <div class="record-field">
            <span class="record-field-label">provenance_sources:</span>
            <span class="record-field-val">["S1-0182", "S2-0941"]</span>
          </div>
        </div>
      </div>
    </div>

    <!-- The 2 Downstream Deliverables -->
    <div style="margin-top: 36px;">
      <h3 style="margin-bottom: 16px;">The Two Concrete Deliverables</h3>
      <div class="grid-2">
        <div class="card">
          <div class="card-accent-top"></div>
          <h4 style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <i class="fa-solid fa-layer-group" style="color: var(--cyan);"></i> Deliverable 1: Apache Iceberg Lakehouse
          </h4>
          <p style="font-size: 0.88rem;">
            Table <code>lakehouse_db.corporate_registry</code> stored in AWS S3 with AWS Glue Data Catalog. Features ACID transaction guarantees via atomic Compare-and-Swap (CAS) commits, snapshot isolation, hidden partitioning by country, and full historical time-travel auditing.
          </p>
          <div style="margin-top: 8px;">
            <span class="tag-pill tag-green">1,557 Canonical Entities</span>
            <span class="tag-pill tag-blue">Parquet + Snappy</span>
            <span class="tag-pill tag-purple">ACID Snapshot ID: 35689108348...</span>
          </div>
        </div>

        <div class="card">
          <div class="card-accent-top"></div>
          <h4 style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <i class="fa-solid fa-brain" style="color: var(--purple);"></i> Deliverable 2: Production XGBoost ML Model
          </h4>
          <p style="font-size: 0.88rem;">
            Trained Regressor (<code>revenue_model.joblib</code>) predicting corporate annual revenue based on harmonized multi-dimensional features (employee count, company age, credit tier, operational spend). Evaluated on 80/20 train/test split.
          </p>
          <div style="margin-top: 8px;">
            <span class="tag-pill tag-green">R² Score: 0.8725 (&ge; 0.85 Target)</span>
            <span class="tag-pill tag-blue">MAE: $18,420</span>
            <span class="tag-pill tag-purple">RMSE: $24,150</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
"""

def get_config_section():
    return """<!-- CHAPTER 2: HOW WE CONFIGURED THIS -->
<section id="configuration" class="section-wrap" style="background: var(--bg-surface);">
  <div class="container">
    <div class="section-header">
      <div class="section-eyebrow"><i class="fa-solid fa-sliders"></i> Chapter 2: Runtime Engineering</div>
      <h2 class="section-title">How We Configured This: Ray Cluster & Runtime Mechanics</h2>
      <p class="section-desc">
        Running distributed data engineering and machine learning workloads requires precise operating system, shared memory, and cluster scheduling configurations to prevent data corruption, out-of-memory crashes, and split-brain states.
      </p>
    </div>

    <!-- Compute Architecture Blueprint -->
    <div class="mermaid-wrapper">
      <div class="mermaid-toolbar">
        <div class="mermaid-title"><i class="fa-solid fa-network-wired" style="color: var(--cyan);"></i> Ray Cluster Architecture on AWS EKS</div>
        <div class="mermaid-actions">
          <button class="mermaid-btn" onclick="openDiagramModal('ray-arch-diag')"><i class="fa-solid fa-expand"></i> Expand</button>
        </div>
      </div>
      <div class="mermaid-container" id="ray-arch-diag">
flowchart TD
    subgraph EKS["AWS EKS 1.31 Cluster (VPC Private Subnets)"]
        subgraph HeadNode["Ray Head Node (Dedicated On-Demand c7g.large)"]
            HEAD_POD["Ray Head Pod\n- GCS (Global Control Store: 6379)\n- Ray Dashboard (8265)\n- Prometheus Metrics Exporter (8080)\n- num-cpus: '0' (Zero Task Scheduling)"]
            SHM_HEAD["Shared Memory Volume: /dev/shm\n- emptyDir: Memory (2 GiB)"]
        end

        subgraph WorkerFleet["Ray Worker Fleet (Elastic Karpenter Spot Pool)"]
            direction LR
            W1["Worker Pod 1 (c7g.xlarge)\n- CPU: 3 / RAM: 12Gi\n- Object Store: 3.6 GiB\n- Slot: entity_resolver_slot: 1"]
            W2["Worker Pod 2 (c7g.xlarge)\n- CPU: 3 / RAM: 12Gi\n- Object Store: 3.6 GiB\n- Task Execution: Ingest & Train"]
            W3["Worker Pod N (Autoscaled 0-8)\n- Spot Diversified (c7g, c6g, c7a, m5)\n- Graceful Node Draining"]
        end

        subgraph Actors["Ray Actor & Task Graph"]
            ACTOR["Stateful RayEntityResolver Actor\n(Single-Instance Enforced via Custom Resource)"]
            DATA_TASKS["Distributed Ray Data Tasks\n(Arrow Ingestion, Normalization, Feature Prep)"]
            TRAIN_TASK["Ray Train / XGBoost Task\n(Parallel Gradient Boosting)"]
        end
    end

    HEAD_POD -->|Cluster Coordination| WorkerFleet
    ACTOR -.->|Pinned via Slot| W1
    DATA_TASKS --> W2
    DATA_TASKS --> W3
    TRAIN_TASK --> W2
    TRAIN_TASK --> W3
      </div>
    </div>

    <!-- The 3 Critical Engineering Decisions -->
    <div style="margin-top: 36px;">
      <h3 style="margin-bottom: 16px;">The 3 Critical Engineering Fixes Applied</h3>
      <div class="grid-3">
        
        <!-- Fix 1: /dev/shm Shared Memory -->
        <div class="card">
          <div class="card-accent-top"></div>
          <h4 style="color: var(--cyan); margin-bottom: 8px;">
            <i class="fa-solid fa-memory"></i> 1. The 4Gi /dev/shm Shared Memory Fix
          </h4>
          <p style="font-size: 0.88rem;">
            <strong>The Problem:</strong> By default, Docker and Kubernetes allocate a tiny <strong>64 MB</strong> to <code>/dev/shm</code>. Ray's Plasma Object Store relies on POSIX shared memory for zero-copy Apache Arrow data deserialization. Without modification, large DataFrame transfers crash instantly with fatal <code>SIGBUS: Bus error</code>.
          </p>
          <div class="terminal-window" style="margin: 10px 0;">
            <div class="terminal-header">
              <span class="terminal-title">ray-cluster.yaml</span>
              <button class="btn-copy" onclick="copySnippet(this)"><i class="fa-solid fa-copy"></i></button>
            </div>
            <div class="terminal-body">
              <pre><span class="comment"># tmpfs volume backed by host RAM</span>
<span class="command">volumes</span>:
  - <span class="command">name</span>: dshm
    <span class="command">emptyDir</span>:
      <span class="command">medium</span>: Memory
      <span class="command">sizeLimit</span>: 4Gi</pre>
            </div>
          </div>
          <p style="font-size: 0.82rem; color: var(--emerald);">
            <i class="fa-solid fa-check"></i> Prevents Plasma memory mapping bus errors across all worker nodes.
          </p>
        </div>

        <!-- Fix 2: Explicit Object Store Sizing -->
        <div class="card">
          <div class="card-accent-top"></div>
          <h4 style="color: var(--purple); margin-bottom: 8px;">
            <i class="fa-solid fa-hard-drive"></i> 2. Object Store Memory Limit (3.6 GiB)
          </h4>
          <p style="font-size: 0.88rem;">
            <strong>The Problem:</strong> If Ray starts without explicit memory boundaries, it attempts to claim 30% of total host RAM for Plasma, causing Kubernetes container cgroups to trigger <code>OOMKilled (Exit Code 137)</code> when Python heap consumption spikes during XGBoost model fitting.
          </p>
          <div class="terminal-window" style="margin: 10px 0;">
            <div class="terminal-header">
              <span class="terminal-title">rayStartParams</span>
              <button class="btn-copy" onclick="copySnippet(this)"><i class="fa-solid fa-copy"></i></button>
            </div>
            <div class="terminal-body">
              <pre><span class="comment"># Exactly 3.6 GiB for Arrow objects</span>
<span class="command">rayStartParams</span>:
  <span class="command">object-store-memory</span>: "3865470566"
  <span class="command">block</span>: "true"</pre>
            </div>
          </div>
          <p style="font-size: 0.82rem; color: var(--emerald);">
            <i class="fa-solid fa-check"></i> Guarantees 8.4 GiB of remaining pod RAM for Python heap execution.
          </p>
        </div>

        <!-- Fix 3: Custom Resource Actor Placement -->
        <div class="card">
          <div class="card-accent-top"></div>
          <h4 style="color: var(--amber); margin-bottom: 8px;">
            <i class="fa-solid fa-cube"></i> 3. Stateful Actor Slot Placement
          </h4>
          <p style="font-size: 0.88rem;">
            <strong>The Problem:</strong> The <code>EntityResolver</code> actor maintains an in-memory graph index of canonical tax IDs and normalized company names. If multiple actor instances were spawned across multiple worker nodes, the entity graph would fragment, producing split-brain canonical IDs.
          </p>
          <div class="terminal-window" style="margin: 10px 0;">
            <div class="terminal-header">
              <span class="terminal-title">entity_resolver.py</span>
              <button class="btn-copy" onclick="copySnippet(this)"><i class="fa-solid fa-copy"></i></button>
            </div>
            <div class="terminal-body">
              <pre><span class="comment"># Pinned single-instance placement</span>
<span class="prompt">@ray.remote</span>(resources={
    <span class="command">"entity_resolver_slot"</span>: 1
})
<span class="command">class RayEntityResolver</span>(...):</pre>
            </div>
          </div>
          <p style="font-size: 0.82rem; color: var(--emerald);">
            <i class="fa-solid fa-check"></i> Enforces single-instance state consistency across all worker tasks.
          </p>
        </div>

      </div>
    </div>

    <!-- Compute Fleet Sizing & Graviton Optimization -->
    <div style="margin-top: 36px;">
      <h3 style="margin-bottom: 14px;">Compute Fleet Optimization: AWS Graviton3 vs Legacy x86</h3>
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Architecture Tier</th>
              <th>Legacy Baseline (x86_64)</th>
              <th>Optimized Graviton (arm64)</th>
              <th>Performance & Cost Advantage</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Head Node (On-Demand)</strong></td>
              <td><code>m6i.xlarge</code> ($0.192/hr)</td>
              <td><code>c7g.large</code> ($0.086/hr)</td>
              <td><span class="tag-pill tag-green">55% Cost Reduction</span> &bull; Dedicated GCS without compute overhead.</td>
            </tr>
            <tr>
              <td><strong>Worker Pool (Spot)</strong></td>
              <td><code>m5.xlarge</code> ($0.076/hr Spot)</td>
              <td><code>c7g.xlarge</code> ($0.058/hr Spot)</td>
              <td><span class="tag-pill tag-green">+24% Throughput</span> &bull; Graviton3 Scalable Vector Extensions (SVE).</td>
            </tr>
            <tr>
              <td><strong>Spot Diversity Pool</strong></td>
              <td>3-4 x86 instance pools</td>
              <td>24+ ARM64 Spot pools (<code>c7g</code>, <code>c6g</code>, <code>m7g</code>, <code>m6g</code>)</td>
              <td><span class="tag-pill tag-green">95% Lower Preemption Risk</span> via Karpenter dynamic diversification.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</section>
"""
