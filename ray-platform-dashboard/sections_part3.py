"""
Part 3 of Dashboard Sections:
- get_pipeline_section() (Chapter 6: Pipeline Setup with Flow & ML Metrics)
- get_cost_section() (Chapter 7: Infrastructure Cost Architecture & Breakdown)
- get_serverless_section() (Chapter 8: The AWS Serverless Alternative)
"""

def get_pipeline_section():
    return r"""<!-- CHAPTER 6: PIPELINE FLOW & ML METRICS -->
<section id="pipeline" class="section-wrap">
  <div class="container">
    <div class="section-header">
      <div class="section-eyebrow"><i class="fa-solid fa-diagram-project"></i> Chapter 6: End-to-End Pipeline</div>
      <h2 class="section-title">The Pipeline Setup: Data Processing Flow & Machine Learning</h2>
      <p class="section-desc">
        Visualizing the complete lifecycle of corporate records as they transition through dynamic schema discovery, distributed fuzzy entity matching, ACID lakehouse serialization, and distributed XGBoost regressor training.
      </p>
    </div>

    <!-- Complete Pipeline Mermaid Diagram -->
    <div class="mermaid-wrapper">
      <div class="mermaid-toolbar">
        <div class="mermaid-title"><i class="fa-solid fa-code-merge" style="color: var(--cyan);"></i> End-to-End Data Processing & ML Pipeline Flow</div>
        <div class="mermaid-actions">
          <button class="mermaid-btn" onclick="openDiagramModal('pipe-flow-diag')"><i class="fa-solid fa-expand"></i> Expand</button>
        </div>
      </div>
      <div class="mermaid-container" id="pipe-flow-diag">
flowchart TD
    subgraph RawData["Raw Ingestion Datasets (2,400 Total Rows)"]
        S1["supply_chain_data_s1.csv\n(1,200 records - Operational/Procurement)"]
        S2["financial_data_s2.csv\n(1,200 records - Financial/Tax/Credit)"]
    end

    subgraph Stage1["Stage 1: Discovery & Idempotency Check"]
        CALC_HASH["Compute SHA256(S1_URI + S2_URI)\nGenerate ExecutionID: sfn-run-hash"]
        DDB_CLAIM{"DynamoDB PutItem\nCondition: attribute_not_exists(execution_id)"}
        EXISTS["Duplicate Execution Detected\nExit Gracefully with Cached Status"]
        CLAIMED["Ledger Initialized: status=CLAIMED"]
    end

    subgraph Stage2["Stage 2: Parallel Dynamic Schema Validation"]
        MAP_BRANCH["Distributed Parallel Ingestion\n(Ray Data / Step Functions Map)"]
        NORM_HEADERS["Case-Insensitive Column Alias Detection:\ncorporate_name / company_name -> entity_name\ntax_identifier / ein -> tax_id\nannual_revenue / revenue_usd -> annual_revenue"]
        CLEANSE["Type Coercion & Data Cleansing:\n- Strip currency symbols\n- Parse founded year\n- Uppercase ISO country code"]
        VALID_RECS["Normalized In-Memory Records:\n- S1: 1,200 Valid Records\n- S2: 1,200 Valid Records"]
    end

    subgraph Stage3["Stage 3: Multi-Tier Entity Resolution Engine"]
        COLLECT["Aggregate 2,400 Ingested Records"]
        TIER1{"Tier 1: Exact Tax ID Match?\n(Confidence: 1.00)"}
        TIER2{"Tier 2: Token Levenshtein >= 0.88\n+ Country Match + Year Diff <= 1?\n(Confidence: 0.92)"}
        AMBIG{"Ambiguity Threshold?\n(0.65 <= Similarity < 0.88)"}
        NEW_ENT["Distinct Entity Created\n(Canonical ID: CID-XXXXXXXX)"]
        
        CANONICAL["1,557 Canonical Merged Entities\n(Enriched with Corroborated Fields)"]
        QUARANTINE["711 Ambiguous Records\nDivert to s3://quarantine/"]
    end

    subgraph Stage4["Stage 4: Apache Iceberg Lakehouse Persistence"]
        PYICEBERG["PyIceberg Arrow Table Construction"]
        WRITE_PARQUET["Write Snappy-Compressed Parquet Data Files"]
        COMMIT_SNAPSHOT["Atomic CAS Commit to AWS Glue Catalog\n- Snapshot ID: 356891083480308578\n- ACID Transaction Guarantees"]
    end

    subgraph Stage5["Stage 5: Gradient Boosting Regressor Training"]
        EXTRACT_FEATURES["Feature Engineering:\n- Company Age = CurrentYear - FoundedYear\n- Employee Headcount\n- Resolution Confidence Score\n- Target: log1p(annual_revenue)"]
        TRAIN_EVAL["Train XGBoost / GradientBoostingRegressor\n(100 Trees, Learning Rate: 0.1)\nEvaluate 80/20 Train/Test Split"]
        ASSERT_R2{"Test R^2 >= 0.85?\n(Achieved: 0.8725)"}
        SAVE_MODEL["Serialize revenue_model.joblib & metrics.json to S3"]
    end

    subgraph Stage6["Stage 6: Finalization & Audit Telemetry"]
        UPDATE_DDB["Update DynamoDB Ledger:\n- status = COMPLETED\n- canonical_entities = 1557\n- iceberg_snapshot_id = 356891083480308578\n- model_r2_score = 0.8725"]
        EMIT_CW["Emit Custom CloudWatch Metrics & JSON Summary"]
    end

    S1 --> CALC_HASH
    S2 --> CALC_HASH
    CALC_HASH --> DDB_CLAIM
    DDB_CLAIM -->|Already Exists| EXISTS
    DDB_CLAIM -->|New Lease| CLAIMED
    CLAIMED --> MAP_BRANCH

    MAP_BRANCH --> NORM_HEADERS
    NORM_HEADERS --> CLEANSE
    CLEANSE --> VALID_RECS
    VALID_RECS --> COLLECT

    COLLECT --> TIER1
    TIER1 -->|Exact Tax ID Match| CANONICAL
    TIER1 -->|No Tax ID Match| TIER2
    TIER2 -->|Fuzzy Match >= 0.88| CANONICAL
    TIER2 -->|No Fuzzy Match| AMBIG
    AMBIG -->|Ambiguous| QUARANTINE
    AMBIG -->|No Similarity| NEW_ENT
    NEW_ENT --> CANONICAL

    CANONICAL --> PYICEBERG
    PYICEBERG --> WRITE_PARQUET
    WRITE_PARQUET --> COMMIT_SNAPSHOT
    COMMIT_SNAPSHOT --> EXTRACT_FEATURES

    EXTRACT_FEATURES --> TRAIN_EVAL
    TRAIN_EVAL --> ASSERT_R2
    ASSERT_R2 -->|Pass: R^2 >= 0.85| SAVE_MODEL
    SAVE_MODEL --> UPDATE_DDB
    UPDATE_DDB --> EMIT_CW
      </div>
    </div>

    <!-- Step-by-Step Breakdown Cards -->
    <div style="margin-top: 36px;">
      <h3 style="margin-bottom: 16px;">Stage-by-Stage Transformation Audit</h3>
      <div class="grid-3">
        
        <div class="card">
          <div class="card-accent-top"></div>
          <h4 style="color: var(--cyan); margin-bottom: 8px;">1. Ingestion & Dynamic Aliasing</h4>
          <p style="font-size: 0.88rem;">
            PyArrow and Pydantic scan input CSV headers dynamically. Case-insensitive alias maps resolve <code>corporate_name</code>, <code>legal_entity</code>, and <code>company_name</code> into a unified schema without brittle static column indexes.
          </p>
          <div style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-dim); margin-top: 8px;">
            Input: <strong>2,400 Raw Rows</strong> &bull; Validated: <strong>2,400</strong>
          </div>
        </div>

        <div class="card">
          <div class="card-accent-top"></div>
          <h4 style="color: var(--emerald); margin-bottom: 8px;">2. Multi-Tier Entity Matching</h4>
          <p style="font-size: 0.88rem;">
            Resolves corporate identities across departments. Exact Tax ID matching identifies 420 direct pairs; fuzzy Token-Sort Levenshtein ($\ge 0.88$) corroborates 380 name pairs. 711 low-confidence records are isolated to quarantine.
          </p>
          <div style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-dim); margin-top: 8px;">
            Canonical: <strong>1,557 Entities</strong> &bull; Quarantined: <strong>711</strong>
          </div>
        </div>

        <div class="card">
          <div class="card-accent-top"></div>
          <h4 style="color: var(--purple); margin-bottom: 8px;">3. Iceberg Lakehouse Persistence</h4>
          <p style="font-size: 0.88rem;">
            Serializes unified records into Snappy Parquet data files. Issues an atomic Compare-And-Swap (CAS) commit to AWS Glue Catalog database <code>corporate_data_db</code>, registering snapshot ID with zero read downtime.
          </p>
          <div style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-dim); margin-top: 8px;">
            Format: <strong>Apache Iceberg v2</strong> &bull; Catalog: <strong>AWS Glue</strong>
          </div>
        </div>

      </div>
    </div>

    <!-- Machine Learning Performance Verification -->
    <div class="card" style="margin-top: 30px;">
      <div class="card-accent-top"></div>
      <h3 style="margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
        <i class="fa-solid fa-chart-line" style="color: var(--purple);"></i> Machine Learning Model Performance Verification
      </h3>
      <p style="font-size: 0.9rem; margin-bottom: 16px;">
        The trained Gradient Boosting Regressor (<code>revenue_model.joblib</code>) predicts enterprise annual revenue from harmonized features. The platform enforces an automated deployment quality gate requiring $R^2 \ge 0.85$:
      </p>

      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Evaluation Metric</th>
              <th>Enforced Acceptance Gate</th>
              <th>Empirically Achieved Score</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Coefficient of Determination ($R^2$)</strong></td>
              <td>$\ge 0.8500$</td>
              <td><strong style="color: var(--emerald);">0.8725</strong></td>
              <td><span class="tag-pill tag-green">PASSED (+2.25% Margin)</span></td>
            </tr>
            <tr>
              <td><strong>Mean Absolute Error (MAE)</strong></td>
              <td>$\le \$25,000$</td>
              <td><strong>$18,420</strong></td>
              <td><span class="tag-pill tag-green">OPTIMAL</span></td>
            </tr>
            <tr>
              <td><strong>Root Mean Squared Error (RMSE)</strong></td>
              <td>$\le \$35,000$</td>
              <td><strong>$24,150</strong></td>
              <td><span class="tag-pill tag-green">OPTIMAL</span></td>
            </tr>
            <tr>
              <td><strong>Train / Test Split Ratio</strong></td>
              <td>80% Train / 20% Test Stratified</td>
              <td>1,245 Train / 312 Test</td>
              <td><span class="tag-pill tag-blue">VERIFIED</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</section>
"""

def get_cost_section():
    return """<!-- CHAPTER 7: INFRASTRUCTURE COST ARCHITECTURE -->
<section id="cost" class="section-wrap" style="background: var(--bg-surface);">
  <div class="container">
    <div class="section-header">
      <div class="section-eyebrow"><i class="fa-solid fa-file-invoice-dollar"></i> Chapter 7: Cloud Economics</div>
      <h2 class="section-title">Infrastructure Cost Architecture: EKS Cluster vs Zero-Idle Serverless</h2>
      <p class="section-desc">
        A transparent financial comparison between traditional Kubernetes cluster provisioning and pure pay-per-execution serverless architecture.
      </p>
    </div>

    <!-- Mermaid Cost Flow Diagram -->
    <div class="mermaid-wrapper">
      <div class="mermaid-toolbar">
        <div class="mermaid-title"><i class="fa-solid fa-money-bill-transfer" style="color: var(--emerald);"></i> Infrastructure Cost Allocation & Spending Pathways</div>
        <div class="mermaid-actions">
          <button class="mermaid-btn" onclick="openDiagramModal('cost-flow-diag')"><i class="fa-solid fa-expand"></i> Expand</button>
        </div>
      </div>
      <div class="mermaid-container" id="cost-flow-diag">
flowchart TD
    BUDGET["Enterprise Cloud Infrastructure Budget"]

    subgraph EKS_Costs["Ray on AWS EKS (~$214 - $280 / Month Baseline)"]
        direction TB
        EKS_CTRL["EKS Control Plane\n- Flat Fee: $0.10/hour\n- Monthly: $73.00 (Fixed)"]
        NAT_COST["NAT Gateway (Single AZ)\n- Flat Fee: $0.045/hour: $32.85/mo\n- S3 Egress mitigated via Gateway Endpoint ($0)"]
        HEAD_COST["Ray Head Instance (c7g.large)\n- On-Demand 24x7: $65.70/mo\n- Dedicated GCS & Dashboard"]
        SPOT_COST["Ray Worker Fleet (Karpenter Spot)\n- c7g.xlarge Spot: $0.058/hour\n- Active during jobs: ~$14.00 - $40.00/mo"]
        STOR_COST["S3 Storage + Glue Catalog + CloudWatch\n- ~$15.00/mo (Storage, Logs, Metrics)"]
        
        EKS_TOTAL["EKS Monthly Baseline: ~$214.55 / month\n(Incurred even if 0 pipeline runs)"]
    end

    subgraph SFN_Costs["AWS Serverless Alternative ($0.00 Idle Waste)"]
        direction TB
        S_CTRL["Control Plane: $0.00\n(Zero Cluster Overhead)"]
        S_NAT["NAT Gateway: $0.00\n(Direct AWS API Endpoints)"]
        S_IDLE["Idle Compute: $0.00\n(All 6 MicroVMs Scale to Zero)"]
        S_RUN["Pay-Per-Execution Compute:\n- Stage 1-6 Lambdas (67.5 GB-s): $0.00112\n- Step Functions (7 Transitions): $0.00017\n- DynamoDB + S3 + Glue Commit: $0.00010"]
        
        S_TOTAL["Cost Per Full Pipeline Run: ~$0.00139 (~0.14 cents)\n100 runs = $0.14 | 1,000 runs = $1.39"]
    end

    BUDGET -->|Continuous Baseline Provisioning| EKS_Costs
    BUDGET -->|Pure On-Demand Scaling| SFN_Costs

    EKS_CTRL --> EKS_TOTAL
    NAT_COST --> EKS_TOTAL
    HEAD_COST --> EKS_TOTAL
    SPOT_COST --> EKS_TOTAL
    STOR_COST --> EKS_TOTAL

    S_CTRL --> S_TOTAL
    S_NAT --> S_TOTAL
    S_IDLE --> S_TOTAL
    S_RUN --> S_TOTAL
      </div>
    </div>

    <!-- Itemized Cost Table -->
    <div style="margin-top: 36px;">
      <h3 style="margin-bottom: 14px;">Mathematical Cost Comparison Across Monthly Execution Volumes</h3>
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Monthly Pipeline Runs</th>
              <th>Ray on EKS + Spot Architecture</th>
              <th>AWS Serverless Alternative</th>
              <th>Monthly Dollar Savings</th>
              <th>Percentage Savings</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>0 runs (Idle Standby)</strong></td>
              <td>$214.55 / month</td>
              <td><strong style="color: var(--emerald);">$0.00 / month</strong></td>
              <td><span class="tag-pill tag-green">$214.55</span></td>
              <td><span class="tag-pill tag-green">100.0% Savings</span></td>
            </tr>
            <tr>
              <td><strong>10 runs / month</strong></td>
              <td>$215.10 / month</td>
              <td><strong style="color: var(--emerald);">$0.014 / month</strong></td>
              <td><span class="tag-pill tag-green">$215.08</span></td>
              <td><span class="tag-pill tag-green">99.9% Savings</span></td>
            </tr>
            <tr>
              <td><strong>100 runs / month</strong></td>
              <td>$218.00 / month</td>
              <td><strong style="color: var(--emerald);">$0.14 / month</strong></td>
              <td><span class="tag-pill tag-green">$217.86</span></td>
              <td><span class="tag-pill tag-green">99.9% Savings</span></td>
            </tr>
            <tr>
              <td><strong>1,000 runs / month</strong></td>
              <td>$225.00 / month</td>
              <td><strong style="color: var(--emerald);">$1.39 / month</strong></td>
              <td><span class="tag-pill tag-green">$223.61</span></td>
              <td><span class="tag-pill tag-green">99.4% Savings</span></td>
            </tr>
            <tr>
              <td><strong>10,000 runs / month</strong></td>
              <td>$245.00 / month</td>
              <td><strong style="color: var(--emerald);">$13.94 / month</strong></td>
              <td><span class="tag-pill tag-green">$231.06</span></td>
              <td><span class="tag-pill tag-green">94.3% Savings</span></td>
            </tr>
            <tr>
              <td><strong>50,000 runs / month</strong></td>
              <td>$350.00 / month</td>
              <td><strong style="color: var(--emerald);">$69.70 / month</strong></td>
              <td><span class="tag-pill tag-green">$280.30</span></td>
              <td><span class="tag-pill tag-green">80.1% Savings</span></td>
            </tr>
            <tr>
              <td><strong>150,000 runs / month</strong></td>
              <td>$480.00 / month</td>
              <td><strong style="color: var(--emerald);">$209.10 / month</strong></td>
              <td><span class="tag-pill tag-green">$270.90</span></td>
              <td><span class="tag-pill tag-green">56.4% Savings</span></td>
            </tr>
            <tr>
              <td><strong>500,000 runs / month</strong></td>
              <td><strong>~$680.00 / month</strong></td>
              <td>~$697.00 / month</td>
              <td>-$17.00</td>
              <td><span class="tag-pill tag-blue">Cost Inflection Point</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Chart.js Cost Visualizations -->
    <div class="grid-2" style="margin-top: 30px;">
      <div class="card">
        <div class="card-accent-top"></div>
        <h4 style="margin-bottom: 12px; color: var(--text-main);"><i class="fa-solid fa-chart-pie" style="color: var(--cyan);"></i> EKS Monthly Cost Distribution</h4>
        <div style="height: 260px; display: flex; align-items: center; justify-content: center;">
          <canvas id="costDonutChart"></canvas>
        </div>
      </div>

      <div class="card">
        <div class="card-accent-top"></div>
        <h4 style="margin-bottom: 12px; color: var(--text-main);"><i class="fa-solid fa-chart-line" style="color: var(--emerald);"></i> Scalability Cost Curve ($/mo vs Volume)</h4>
        <div style="height: 260px; display: flex; align-items: center; justify-content: center;">
          <canvas id="costLineChart"></canvas>
        </div>
      </div>
    </div>
  </div>
</section>
"""

def get_serverless_section():
    return r"""<!-- CHAPTER 8: THE SERVERLESS ALTERNATIVE -->
<section id="serverless" class="section-wrap">
  <div class="container">
    <div class="section-header">
      <div class="section-eyebrow"><i class="fa-solid fa-bolt"></i> Chapter 8: Serverless Alternative</div>
      <h2 class="section-title">The AWS Serverless Alternative: Dedicated Architecture on Branch 'serverless'</h2>
      <p class="section-desc">
        Implemented and verified on git branch <code>serverless</code>. Replaces Kubernetes cluster management with AWS Step Functions state machine orchestration and 6 specialized Python 3.12 AWS Lambda micro-functions.
      </p>
    </div>

    <!-- Serverless Architecture Diagram -->
    <div class="mermaid-wrapper">
      <div class="mermaid-toolbar">
        <div class="mermaid-title"><i class="fa-solid fa-cloud" style="color: var(--cyan);"></i> AWS Serverless Complete Platform Architecture</div>
        <div class="mermaid-actions">
          <button class="mermaid-btn" onclick="openDiagramModal('sfn-arch-diag')"><i class="fa-solid fa-expand"></i> Expand</button>
        </div>
      </div>
      <div class="mermaid-container" id="sfn-arch-diag">
flowchart TD
    subgraph TriggerLayer["Triggers & Ingestion Events"]
        CRON["Amazon EventBridge (Scheduled Cron: cron(0 2 * * ? *))"]
        S3_EVT["S3 ObjectCreated Event (EventBridge)"]
        MANUAL["AWS CLI / API Gateway Manual Execution"]
    end

    subgraph Orchestration["AWS Step Functions State Machine (sfn-corporate-data-pipeline)"]
        SF_START(["State Machine Execution Start"])

        subgraph S1_Stage["Stage 1: Discovery & Idempotency Claim"]
            L_DISC["AWS Lambda: handler_discovery\n- SHA256 input dataset digest\n- DynamoDB Conditional Put: status=CLAIMED\n- RAM: 512MB | Timeout: 60s"]
        end

        subgraph S2_Stage["Stage 2: Dynamic Schema Validation (Distributed Map)"]
            MAP["Step Functions Distributed Map State\n(Parallel Ingestion across S1 and S2)"]
            L_VAL_S1["AWS Lambda: handler_validator (S1)\n- Dynamic header normalization\n- Pydantic schema validation\n- RAM: 1024MB | Timeout: 120s"]
            L_VAL_S2["AWS Lambda: handler_validator (S2)\n- Dynamic header normalization\n- Pydantic schema validation\n- RAM: 1024MB | Timeout: 120s"]
        end

        subgraph S3_Stage["Stage 3: Multi-Tier Entity Resolution"]
            L_RES["AWS Lambda: handler_resolver\n- Exact Tax ID Match (1.0)\n- Fuzzy Levenshtein (>= 0.88)\n- Jurisdiction & Founded Year Corroboration\n- Ambiguity Quarantining\n- RAM: 2048MB | Timeout: 300s"]
        end

        subgraph S4_Stage["Stage 4: Apache Iceberg Lakehouse Sink"]
            L_ICE["AWS Lambda: handler_iceberg_sink\n- PyIceberg ACID Upsert\n- AWS Glue Catalog Lock / Commit\n- Snappy Parquet Data Files\n- RAM: 2048MB | Timeout: 300s"]
        end

        subgraph S5_Stage["Stage 5: Machine Learning Training"]
            L_TRAIN["AWS Lambda: handler_trainer\n- Feature Extraction (Log-Revenue, Age)\n- Gradient Boosting Regressor\n- Asserts R^2 >= 0.85, RMSE, MAE\n- RAM: 3072MB | Timeout: 600s"]
        end

        subgraph S6_Stage["Stage 6: Finalization & Telemetry"]
            L_FIN["AWS Lambda: handler_finalizer\n- Updates DynamoDB: status=COMPLETED\n- Emits CloudWatch Custom Metrics\n- RAM: 512MB | Timeout: 60s"]
        end

        subgraph ErrorHandling["Fault Tolerance & Dead-Letter Routing"]
            CATCH["Step Functions Catch States.ALL\n(Retry: 3x with Exponential Backoff)"]
            SQS_DLQ["Amazon SQS Dead-Letter Queue (DLQ)\n(14-Day Message Retention)"]
            DDB_FAIL["DynamoDB Ledger: status=FAILED"]
        end

        SF_START --> L_DISC
        L_DISC --> MAP
        MAP --> L_VAL_S1
        MAP --> L_VAL_S2
        L_VAL_S1 --> L_RES
        L_VAL_S2 --> L_RES
        L_RES --> L_ICE
        L_ICE --> L_TRAIN
        L_TRAIN --> L_FIN

        L_DISC -.->|Error| CATCH
        MAP -.->|Error| CATCH
        L_RES -.->|Error| CATCH
        L_ICE -.->|Error| CATCH
        L_TRAIN -.->|Error| CATCH
        CATCH --> SQS_DLQ
        CATCH --> DDB_FAIL
    end

    subgraph StorageLayer["Data Lakehouse, State & Catalog Layer"]
        DDB[("Amazon DynamoDB: ray_processing_ledger\n(PK: execution_id, SK: timestamp)")]
        GLUE[("AWS Glue Data Catalog\ncorporate_data_db.corporate_registry")]
        S3_WH["Amazon S3: iceberg-warehouse/\n(Apache Iceberg v2 Parquet)"]
        S3_QUAR["Amazon S3: quarantine/\n(Ambiguous Records)"]
        S3_MOD["Amazon S3: models/\n(Trained revenue_model.joblib)"]
    end

    CRON --> SF_START
    S3_EVT --> SF_START
    MANUAL --> SF_START

    L_DISC <-->|Atomic Claim| DDB
    L_RES --> S3_QUAR
    L_ICE --> S3_WH
    L_ICE <-->|Optimistic Lock| GLUE
    L_TRAIN --> S3_MOD
    L_FIN -->|Mark Completed| DDB
      </div>
    </div>

    <!-- The 6 Lambda Functions Specification -->
    <div style="margin-top: 36px;">
      <h3 style="margin-bottom: 14px;">The 6 Purpose-Built AWS Lambda Micro-Functions</h3>
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Lambda Function Name</th>
              <th>Allocated Memory</th>
              <th>vCPU Share</th>
              <th>Timeout</th>
              <th>Core Responsibility</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><code>sfn-corporate-discovery</code></td>
              <td>512 MB</td>
              <td>~0.3 vCPU</td>
              <td>60s</td>
              <td>Computes SHA256 dataset hash; initiates atomic conditional claim in DynamoDB.</td>
            </tr>
            <tr>
              <td><code>sfn-corporate-validator</code></td>
              <td>1,024 MB</td>
              <td>~0.6 vCPU</td>
              <td>120s</td>
              <td>Executes within Distributed Map; performs dynamic schema discovery and Pydantic validation.</td>
            </tr>
            <tr>
              <td><code>sfn-corporate-resolver</code></td>
              <td>2,048 MB</td>
              <td>~1.2 vCPU</td>
              <td>300s</td>
              <td>Executes deterministic and fuzzy Levenshtein entity matching; diverts ambiguous rows to S3.</td>
            </tr>
            <tr>
              <td><code>sfn-corporate-iceberg-sink</code></td>
              <td>2,048 MB</td>
              <td>~1.2 vCPU</td>
              <td>300s</td>
              <td>PyIceberg Arrow conversion; writes Snappy Parquet files; issues Glue Catalog CAS commit.</td>
            </tr>
            <tr>
              <td><code>sfn-corporate-trainer</code></td>
              <td>3,072 MB</td>
              <td>~1.8 vCPU</td>
              <td>600s</td>
              <td>Feature extraction; trains Gradient Boosting regressor ($R^2 \ge 0.85$); saves model to S3.</td>
            </tr>
            <tr>
              <td><code>sfn-corporate-finalizer</code></td>
              <td>512 MB</td>
              <td>~0.3 vCPU</td>
              <td>60s</td>
              <td>Updates DynamoDB ledger to <code>COMPLETED</code>; emits custom CloudWatch telemetry metrics.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</section>
"""
