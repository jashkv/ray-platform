"""
Part 2 of Dashboard Sections:
- get_setup_section() (Chapter 3: Software & File Setup)
- get_tf_section() (Chapter 4: Terraform Configuration & Architecture Rationale)
- get_order_section() (Chapter 5: How to Apply in Correct Order)
"""

def get_setup_section():
    return """<!-- CHAPTER 3: SOFTWARE & FILE SETUP -->
<section id="setup" class="section-wrap">
  <div class="container">
    <div class="section-header">
      <div class="section-eyebrow"><i class="fa-solid fa-terminal"></i> Chapter 3: Installation Runbook</div>
      <h2 class="section-title">How to Setup Files & Install Software: Local & Cloud Environment</h2>
      <p class="section-desc">
        Complete step-by-step developer setup guide for replicating the entire platform environment from a fresh workstation to ready-to-deploy status.
      </p>
    </div>

    <!-- Repository File Tree Layout -->
    <div class="card" style="margin-bottom: 30px;">
      <div class="card-accent-top"></div>
      <h3 style="margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
        <i class="fa-solid fa-folder-tree" style="color: var(--cyan);"></i> Repository Directory Architecture
      </h3>
      <p style="font-size: 0.9rem; margin-bottom: 14px;">
        The repository is organized cleanly with complete isolation between infrastructure, application code, container definitions, and test harnesses:
      </p>
      <div class="terminal-window">
        <div class="terminal-header">
          <span class="terminal-title">Directory Tree View</span>
          <button class="btn-copy" onclick="copySnippet(this)"><i class="fa-solid fa-copy"></i></button>
        </div>
        <div class="terminal-body">
          <pre><span class="output">ray-ai-platform/
├── Makefile                               <span class="comment"># Root automation entrypoint (test, lint, deploy)</span>
├── ray-ai-platform/
│   ├── application/
│   │   ├── Dockerfile                     <span class="comment"># Multi-arch container image (amd64 + arm64)</span>
│   │   ├── requirements.txt               <span class="comment"># Pinned Ray 2.40.0, PyIceberg, XGBoost, PyArrow</span>
│   │   ├── src/
│   │   │   ├── entity_resolver.py         <span class="comment"># Multi-tier deterministic & fuzzy matching engine</span>
│   │   │   ├── normalizer.py              <span class="comment"># Name cleaning, Jaro-Winkler & Levenshtein metrics</span>
│   │   │   ├── schema_validator.py        <span class="comment"># Pydantic schemas & dynamic header mapping</span>
│   │   │   ├── iceberg_sink.py            <span class="comment"># PyIceberg ACID commit & catalog management</span>
│   │   │   ├── train_model.py             <span class="comment"># Distributed XGBoost regressor model training</span>
│   │   │   └── serverless/
│   │   │       ├── handlers.py            <span class="comment"># 6 AWS Lambda handler functions</span>
│   │   │       └── serverless_pipeline.py <span class="comment"># Local execution harness for serverless stages</span>
│   │   └── tests/                         <span class="comment"># Unit & integration test suites (5/5 passing)</span>
│   ├── terraform/
│   │   ├── bootstrap/                     <span class="comment"># Layer 1: S3 tfstate bucket & DynamoDB lock table</span>
│   │   ├── network/                       <span class="comment"># Layer 2: 3-AZ VPC, NAT, S3 Gateway Endpoint</span>
│   │   ├── data/                          <span class="comment"># Layer 3: S3 Lakehouse, Glue Catalog, IRSA roles</span>
│   │   ├── eks/                           <span class="comment"># Layer 4: EKS 1.31 cluster, OIDC, Karpenter roles</span>
│   │   ├── platform/                      <span class="comment"># Layer 5: KubeRay, Karpenter NodePools, Prometheus</span>
│   │   └── serverless/                    <span class="comment"># Layer 6: Step Functions State Machine, 6 Lambdas</span>
│   ├── kubernetes/                        <span class="comment"># Manifests for KubeRay, Karpenter, and Observability</span>
│   └── scripts/                           <span class="comment"># Verification, health check, and build scripts</span></span></pre>
        </div>
      </div>
    </div>

    <!-- Operating System & Prerequisites Runbook -->
    <div class="card" style="margin-bottom: 30px;">
      <div class="card-accent-top"></div>
      <h3 style="margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
        <i class="fa-solid fa-download" style="color: var(--purple);"></i> Step 1: Install OS Packages & CLI Tools
      </h3>
      <p style="font-size: 0.9rem; margin-bottom: 14px;">
        Choose your host operating system tab for exact package manager commands:
      </p>

      <div class="tab-nav">
        <button class="tab-btn active" onclick="switchTab(this, 'os-macos')"><i class="fa-brands fa-apple"></i> macOS (Homebrew)</button>
        <button class="tab-btn" onclick="switchTab(this, 'os-linux')"><i class="fa-brands fa-ubuntu"></i> Ubuntu / Debian Linux</button>
      </div>

      <!-- macOS Tab -->
      <div id="os-macos" class="tab-content active">
        <div class="terminal-window">
          <div class="terminal-header">
            <span class="terminal-title">Terminal &bull; macOS</span>
            <button class="btn-copy" onclick="copySnippet(this)"><i class="fa-solid fa-copy"></i></button>
          </div>
          <div class="terminal-body">
            <pre><span class="comment"># 1. Update Homebrew package repository</span>
<span class="prompt">$</span> <span class="command">brew update</span>

<span class="comment"># 2. Install required runtime tools, compilers, and cloud CLIs</span>
<span class="prompt">$</span> <span class="command">brew install python@3.12 terraform awscli kubectl helm docker uv jq graphviz</span>

<span class="comment"># 3. Verify installed tool versions</span>
<span class="prompt">$</span> <span class="command">python3.12 --version</span>   <span class="output"># Python 3.12.x</span>
<span class="prompt">$</span> <span class="command">terraform version</span>     <span class="output"># Terraform v1.10.x</span>
<span class="prompt">$</span> <span class="command">aws --version</span>          <span class="output"># aws-cli/2.15.x</span>
<span class="prompt">$</span> <span class="command">kubectl version --client</span></pre>
          </div>
        </div>
      </div>

      <!-- Linux Tab -->
      <div id="os-linux" class="tab-content">
        <div class="terminal-window">
          <div class="terminal-header">
            <span class="terminal-title">Terminal &bull; Ubuntu/Debian Linux</span>
            <button class="btn-copy" onclick="copySnippet(this)"><i class="fa-solid fa-copy"></i></button>
          </div>
          <div class="terminal-body">
            <pre><span class="comment"># 1. Update system package index and install base utilities</span>
<span class="prompt">$</span> <span class="command">sudo apt-get update && sudo apt-get install -y ca-certificates curl gnupg unzip jq git make \
  python3.12 python3.12-venv python3-pip build-essential</span>

<span class="comment"># 2. Add HashiCorp APT repository for Terraform</span>
<span class="prompt">$</span> <span class="command">curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp.gpg</span>
<span class="prompt">$</span> <span class="command">echo "deb [signed-by=/usr/share/keyrings/hashicorp.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list</span>

<span class="comment"># 3. Add Docker official APT repository</span>
<span class="prompt">$</span> <span class="command">sudo install -m 0755 -d /etc/apt/keyrings</span>
<span class="prompt">$</span> <span class="command">curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc</span>
<span class="prompt">$</span> <span class="command">echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list</span>

<span class="comment"># 4. Install Terraform and Docker Engine</span>
<span class="prompt">$</span> <span class="command">sudo apt-get update && sudo apt-get install -y terraform docker-ce docker-ce-cli containerd.io docker-buildx-plugin</span>

<span class="comment"># 5. Install AWS CLI v2</span>
<span class="prompt">$</span> <span class="command">curl "https://awscli.amazonaws.com/awscli-exe-linux-$(uname -m).zip" -o "awscliv2.zip"</span>
<span class="prompt">$</span> <span class="command">unzip awscliv2.zip && sudo ./aws/install</span></pre>
          </div>
        </div>
      </div>
    </div>

    <!-- Step 2 & 3: Python Environment & AWS Credential Verification -->
    <div class="grid-2">
      <div class="card">
        <div class="card-accent-top"></div>
        <h4 style="color: var(--cyan); margin-bottom: 8px;">
          <i class="fa-brands fa-python"></i> Step 2: Python 3.12 Virtual Environment
        </h4>
        <p style="font-size: 0.88rem;">
          Create an isolated virtual environment and install all pinned application packages:
        </p>
        <div class="terminal-window">
          <div class="terminal-header">
            <span class="terminal-title">venv setup</span>
            <button class="btn-copy" onclick="copySnippet(this)"><i class="fa-solid fa-copy"></i></button>
          </div>
          <div class="terminal-body">
            <pre><span class="comment"># Create and activate virtual environment</span>
<span class="prompt">$</span> <span class="command">python3.12 -m venv .venv</span>
<span class="prompt">$</span> <span class="command">source .venv/bin/activate</span>

<span class="comment"># Upgrade pip and install pinned dependencies</span>
<span class="prompt">$</span> <span class="command">pip install --upgrade pip</span>
<span class="prompt">$</span> <span class="command">pip install -r ray-ai-platform/application/requirements.txt</span></pre>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-accent-top"></div>
        <h4 style="color: var(--purple); margin-bottom: 8px;">
          <i class="fa-brands fa-aws"></i> Step 3: AWS Credential & IAM Verification
        </h4>
        <p style="font-size: 0.88rem;">
          Configure local AWS credentials and verify active caller identity:
        </p>
        <div class="terminal-window">
          <div class="terminal-header">
            <span class="terminal-title">aws sts check</span>
            <button class="btn-copy" onclick="copySnippet(this)"><i class="fa-solid fa-copy"></i></button>
          </div>
          <div class="terminal-body">
            <pre><span class="comment"># Authenticate with target AWS account</span>
<span class="prompt">$</span> <span class="command">aws configure</span>
<span class="comment"># AWS Access Key ID [None]: ****************</span>
<span class="comment"># Default region name [None]: us-east-1</span>

<span class="comment"># Verify active IAM credentials</span>
<span class="prompt">$</span> <span class="command">aws sts get-caller-identity</span>
<span class="output">{
  "UserId": "AIDASAMPLEUSER12345",
  "Account": "123456789012",
  "Arn": "arn:aws:iam::123456789012:user/platform-admin"
}</span></pre>
          </div>
        </div>
      </div>
    </div>

    <!-- Step 4: Local Testing Verification Runbook -->
    <div style="margin-top: 30px;">
      <h3 style="margin-bottom: 12px;">Step 4: Execute Local Verification Targets</h3>
      <p style="font-size: 0.95rem; margin-bottom: 14px;">
        Before any infrastructure deployment, validate application code integrity via the automated Makefile gates:
      </p>

      <div class="terminal-window">
        <div class="terminal-header">
          <span class="terminal-title">Verification Commands</span>
          <button class="btn-copy" onclick="copySnippet(this)"><i class="fa-solid fa-copy"></i></button>
        </div>
        <div class="terminal-body">
          <pre><span class="comment"># 1. Run full unit and integration test suite (Entity Resolver, Schema, Iceberg Sink)</span>
<span class="prompt">$</span> <span class="command">make test</span>
<span class="success-text">======= 5 passed in 1.42s =======</span>

<span class="comment"># 2. Run the dedicated serverless pipeline test suite</span>
<span class="prompt">$</span> <span class="command">make test-serverless</span>
<span class="success-text">======= 5 passed in 95.8s =======</span>

<span class="comment"># 3. Execute the local end-to-end Ray pipeline</span>
<span class="prompt">$</span> <span class="command">make e2e-local</span>
<span class="output">Generated S1 (1,200 rows) & S2 (1,200 rows) -> Resolved 1,557 Canonical Entities -> Model R²: 0.8725</span>

<span class="comment"># 4. Verify Terraform formatting and syntax across all layers</span>
<span class="prompt">$</span> <span class="command">make lint-tf</span>
<span class="success-text">Success! The configuration is valid across all 6 modules.</span></pre>
        </div>
      </div>
    </div>
  </div>
</section>
"""

def get_tf_section():
    return """<!-- CHAPTER 4: TERRAFORM CONFIGURATION -->
<section id="terraform" class="section-wrap" style="background: var(--bg-surface);">
  <div class="container">
    <div class="section-header">
      <div class="section-eyebrow"><i class="fa-solid fa-network-wired"></i> Chapter 4: Infrastructure as Code</div>
      <h2 class="section-title">Terraform Configuration: 6-Layer Modular Architecture</h2>
      <p class="section-desc">
        Why did we decompose the infrastructure into 6 distinct Terraform modules instead of a monolithic state file? Analyzing the architectural benefits of blast radius containment, state locking isolation, and team privilege separation.
      </p>
    </div>

    <!-- Why Modular Architecture? 3 Principles -->
    <div class="grid-3" style="margin-bottom: 30px;">
      <div class="card">
        <div class="card-accent-top"></div>
        <h4 style="color: var(--cyan); margin-bottom: 8px;"><i class="fa-solid fa-shield-halved"></i> 1. Blast Radius Containment</h4>
        <p style="font-size: 0.88rem;">
          In a monolithic Terraform state, an accidental syntax error or quota failure in an EKS worker pool upgrade risks tearing down VPC subnets, NAT gateways, or dropping S3 lakehouse metadata. Modularization guarantees zero cross-layer destruction.
        </p>
      </div>

      <div class="card">
        <div class="card-accent-top"></div>
        <h4 style="color: var(--purple); margin-bottom: 8px;"><i class="fa-solid fa-lock"></i> 2. Independent State Locking</h4>
        <p style="font-size: 0.88rem;">
          Each layer maintains its own distinct S3 state file and DynamoDB state lock. Data engineers deploying new Glue tables or DynamoDB tables never block platform engineers deploying Helm charts or updating Karpenter nodepools.
        </p>
      </div>

      <div class="card">
        <div class="card-accent-top"></div>
        <h4 style="color: var(--emerald); margin-bottom: 8px;"><i class="fa-solid fa-user-lock"></i> 3. Least-Privilege IAM</h4>
        <p style="font-size: 0.88rem;">
          CI/CD pipelines assume role-specific credentials per layer: the Networking role only possesses EC2/VPC permissions; the Data role cannot touch Kubernetes clusters; and the EKS role cannot delete S3 lakehouse buckets.
        </p>
      </div>
    </div>

    <!-- Mermaid Dependency DAG -->
    <div class="mermaid-wrapper">
      <div class="mermaid-toolbar">
        <div class="mermaid-title"><i class="fa-solid fa-diagram-project" style="color: var(--cyan);"></i> Terraform Layer Dependency DAG (Data & State Flow)</div>
        <div class="mermaid-actions">
          <button class="mermaid-btn" onclick="openDiagramModal('tf-dag-diag')"><i class="fa-solid fa-expand"></i> Expand</button>
        </div>
      </div>
      <div class="mermaid-container" id="tf-dag-diag">
flowchart TD
    L1["Layer 1: bootstrap\n- S3 State Storage Bucket\n- DynamoDB State Lock Table\n- KMS Encryption Key"]
    L2["Layer 2: network\n- 3-AZ VPC (us-east-1a, 1b, 1c)\n- Public & Private Subnets\n- Single NAT Gateway ($32.85/mo)\n- S3 Gateway VPC Endpoint ($0 Egress)"]
    L3["Layer 3: data\n- S3 Lakehouse Bucket (iceberg-warehouse/)\n- AWS Glue Data Catalog (corporate_data_db)\n- DynamoDB Processing Ledger\n- IRSA IAM Roles (Ray & Lambda)"]
    L4["Layer 4: eks\n- EKS Control Plane 1.31\n- OIDC Identity Provider\n- Managed System Node Group (c7g.large)\n- Karpenter Controller IAM & SQS"]
    L5["Layer 5: platform\n- KubeRay Operator Helm Release\n- Karpenter NodePool (Spot c7g.xlarge)\n- Prometheus & Grafana Monitoring Stack\n- GitHub Actions OIDC Role"]
    L6["Layer 6: serverless\n- AWS Step Functions ASL State Machine\n- 6 Lambda Micro-Functions (Python 3.12)\n- Amazon SQS Dead-Letter Queue (DLQ)\n- EventBridge Scheduled Rule"]

    L1 -->|State Backend| L2
    L1 -->|State Backend| L3
    L1 -->|State Backend| L4
    L1 -->|State Backend| L5
    L1 -->|State Backend| L6

    L2 -->|VPC ID & Subnets| L4
    L2 -->|VPC ID & S3 Endpoint| L6
    L4 -->|OIDC Provider ARN| L3
    L4 -->|Cluster Endpoint & Auth| L5
    L3 -->|S3 & DynamoDB ARNs| L5
    L3 -->|S3 & DynamoDB ARNs| L6
      </div>
    </div>

    <!-- The 6 Modules Deep-Dive Breakdown -->
    <div style="margin-top: 36px;">
      <h3 style="margin-bottom: 16px;">The 6 Terraform Modules: Purpose & Outputs</h3>
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Layer</th>
              <th>Directory Path</th>
              <th>Core AWS Resources Provisioned</th>
              <th>Exported Outputs</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>1. Bootstrap</strong></td>
              <td><code>terraform/bootstrap/</code></td>
              <td>S3 state bucket (versioning, AES256), DynamoDB lock table, KMS CMK.</td>
              <td><code>tfstate_bucket_id</code>, <code>dynamodb_lock_table_name</code></td>
            </tr>
            <tr>
              <td><strong>2. Network</strong></td>
              <td><code>terraform/network/</code></td>
              <td>3-AZ VPC (10.0.0.0/16), 3 public subnets, 3 private subnets, NAT Gateway, S3 Gateway Endpoint.</td>
              <td><code>vpc_id</code>, <code>private_subnets</code>, <code>s3_endpoint_id</code></td>
            </tr>
            <tr>
              <td><strong>3. Data</strong></td>
              <td><code>terraform/data/</code></td>
              <td>S3 Lakehouse bucket, AWS Glue DB (<code>corporate_data_db</code>), DynamoDB ledger, IRSA IAM roles.</td>
              <td><code>s3_bucket_arn</code>, <code>glue_database_name</code>, <code>ddb_table_arn</code></td>
            </tr>
            <tr>
              <td><strong>4. EKS</strong></td>
              <td><code>terraform/eks/</code></td>
              <td>Amazon EKS 1.31 cluster, OIDC Issuer, Managed System Node Group (2x c7g.large), Karpenter IAM.</td>
              <td><code>cluster_endpoint</code>, <code>cluster_name</code>, <code>oidc_provider_arn</code></td>
            </tr>
            <tr>
              <td><strong>5. Platform</strong></td>
              <td><code>terraform/platform/</code></td>
              <td>Helm: KubeRay operator, Karpenter NodePools, Prometheus/Grafana stack, FluentBit logs.</td>
              <td><code>kuberay_version</code>, <code>grafana_url</code>, <code>nodepool_status</code></td>
            </tr>
            <tr>
              <td><strong>6. Serverless</strong></td>
              <td><code>terraform/serverless/</code></td>
              <td>Step Functions ASL state machine, 6 Lambda functions (Python 3.12), SQS DLQ, EventBridge.</td>
              <td><code>state_machine_arn</code>, <code>lambda_function_arns</code>, <code>dlq_arn</code></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</section>
"""

def get_order_section():
    return """<!-- CHAPTER 5: HOW TO APPLY IN CORRECT ORDER -->
<section id="apply-order" class="section-wrap">
  <div class="container">
    <div class="section-header">
      <div class="section-eyebrow"><i class="fa-solid fa-list-ol"></i> Chapter 5: Deployment Runbook</div>
      <h2 class="section-title">How to Apply in the Correct Order: Sequential Execution Runbook</h2>
      <p class="section-desc">
        Due to cross-layer dependencies (e.g. EKS OIDC provider needed by IRSA roles, and VPC subnets needed by EKS), Terraform must be applied in a strict deterministic sequence. Follow this exact runbook:
      </p>
    </div>

    <!-- The 6-Step Ordered Execution Table -->
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>Order</th>
            <th>Layer</th>
            <th>Required Dependencies</th>
            <th>Terminal Command</th>
            <th>Expected Provisioning Time</th>
            <th>Boundary Verification Command</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong style="color: var(--cyan);">1</strong></td>
            <td><strong>Bootstrap</strong></td>
            <td>AWS Credentials with S3 & DynamoDB admin</td>
            <td><code>cd terraform/bootstrap && terraform apply</code></td>
            <td>~30 seconds</td>
            <td><code>aws s3 ls | grep tfstate</code></td>
          </tr>
          <tr>
            <td><strong style="color: var(--cyan);">2</strong></td>
            <td><strong>Network</strong></td>
            <td>Bootstrap state backend</td>
            <td><code>cd terraform/network && terraform apply</code></td>
            <td>~2.5 minutes (NAT Gateway)</td>
            <td><code>aws ec2 describe-vpcs --filters Name=tag:Name,Values=*ray*</code></td>
          </tr>
          <tr>
            <td><strong style="color: var(--cyan);">3</strong></td>
            <td><strong>Data</strong></td>
            <td>Network VPC & S3 Gateway</td>
            <td><code>cd terraform/data && terraform apply</code></td>
            <td>~45 seconds</td>
            <td><code>aws glue get-database --name corporate_data_db</code></td>
          </tr>
          <tr>
            <td><strong style="color: var(--cyan);">4</strong></td>
            <td><strong>EKS</strong></td>
            <td>Network Private Subnets & VPC</td>
            <td><code>cd terraform/eks && terraform apply</code></td>
            <td>~12-14 minutes (Control Plane)</td>
            <td><code>aws eks describe-cluster --name ray-cluster</code></td>
          </tr>
          <tr>
            <td><strong style="color: var(--cyan);">5</strong></td>
            <td><strong>Platform</strong></td>
            <td>EKS Cluster active + OIDC</td>
            <td><code>cd terraform/platform && terraform apply</code></td>
            <td>~4 minutes (Helm releases)</td>
            <td><code>kubectl get pods -n kuberay-system</code></td>
          </tr>
          <tr>
            <td><strong style="color: var(--emerald);">6</strong></td>
            <td><strong>Serverless</strong></td>
            <td>Data layer (S3 & DynamoDB)</td>
            <td><code>cd terraform/serverless && terraform apply</code></td>
            <td>~75 seconds</td>
            <td><code>aws stepfunctions list-state-machines</code></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Interactive Layer Selector with Exact Commands -->
    <div style="margin-top: 36px;">
      <h3 style="margin-bottom: 14px;">Interactive Command Inspector: Layer-by-Layer Runbook</h3>
      
      <div class="tab-nav">
        <button class="tab-btn active" onclick="switchTab(this, 'layer-1')">Layer 1: Bootstrap</button>
        <button class="tab-btn" onclick="switchTab(this, 'layer-2')">Layer 2: Network</button>
        <button class="tab-btn" onclick="switchTab(this, 'layer-3')">Layer 3: Data</button>
        <button class="tab-btn" onclick="switchTab(this, 'layer-4')">Layer 4: EKS</button>
        <button class="tab-btn" onclick="switchTab(this, 'layer-5')">Layer 5: Platform</button>
        <button class="tab-btn" onclick="switchTab(this, 'layer-6')">Layer 6: Serverless</button>
      </div>

      <!-- Layer 1 Tab -->
      <div id="layer-1" class="tab-content active">
        <div class="terminal-window">
          <div class="terminal-header">
            <span class="terminal-title">bash &bull; terraform/bootstrap</span>
            <button class="btn-copy" onclick="copySnippet(this)"><i class="fa-solid fa-copy"></i></button>
          </div>
          <div class="terminal-body">
            <pre><span class="prompt">$</span> <span class="command">cd ray-ai-platform/terraform/bootstrap</span>
<span class="prompt">$</span> <span class="command">terraform init</span>
<span class="prompt">$</span> <span class="command">terraform plan -out=tfplan</span>
<span class="prompt">$</span> <span class="command">terraform apply tfplan</span>
<span class="success-text">Apply complete! Resources: 3 added, 0 changed, 0 destroyed.
Outputs:
tfstate_bucket = "ray-platform-tfstate-test-123456789012"
lock_table_name = "ray-platform-tflocks-test"</span></pre>
          </div>
        </div>
      </div>

      <!-- Layer 2 Tab -->
      <div id="layer-2" class="tab-content">
        <div class="terminal-window">
          <div class="terminal-header">
            <span class="terminal-title">bash &bull; terraform/network</span>
            <button class="btn-copy" onclick="copySnippet(this)"><i class="fa-solid fa-copy"></i></button>
          </div>
          <div class="terminal-body">
            <pre><span class="prompt">$</span> <span class="command">cd ../network</span>
<span class="prompt">$</span> <span class="command">terraform init</span>
<span class="prompt">$</span> <span class="command">terraform apply -auto-approve</span>
<span class="success-text">Apply complete! Resources: 14 added, 0 changed, 0 destroyed.
Outputs:
vpc_id = "vpc-0a8b7c6d5e4f3a2b1"
private_subnets = ["subnet-01", "subnet-02", "subnet-03"]
s3_gateway_endpoint_id = "vpce-0123456789abcdef0"</span></pre>
          </div>
        </div>
      </div>

      <!-- Layer 3 Tab -->
      <div id="layer-3" class="tab-content">
        <div class="terminal-window">
          <div class="terminal-header">
            <span class="terminal-title">bash &bull; terraform/data</span>
            <button class="btn-copy" onclick="copySnippet(this)"><i class="fa-solid fa-copy"></i></button>
          </div>
          <div class="terminal-body">
            <pre><span class="prompt">$</span> <span class="command">cd ../data</span>
<span class="prompt">$</span> <span class="command">terraform init</span>
<span class="prompt">$</span> <span class="command">terraform apply -auto-approve</span>
<span class="success-text">Apply complete! Resources: 8 added, 0 changed, 0 destroyed.
Outputs:
iceberg_s3_bucket = "ray-platform-iceberg-warehouse-test-123456789012"
glue_catalog_database = "corporate_data_db"
dynamodb_ledger_arn = "arn:aws:dynamodb:us-east-1:123456789012:table/ray_processing_ledger"</span></pre>
          </div>
        </div>
      </div>

      <!-- Layer 4 Tab -->
      <div id="layer-4" class="tab-content">
        <div class="terminal-window">
          <div class="terminal-header">
            <span class="terminal-title">bash &bull; terraform/eks</span>
            <button class="btn-copy" onclick="copySnippet(this)"><i class="fa-solid fa-copy"></i></button>
          </div>
          <div class="terminal-body">
            <pre><span class="prompt">$</span> <span class="command">cd ../eks</span>
<span class="prompt">$</span> <span class="command">terraform init</span>
<span class="prompt">$</span> <span class="command">terraform apply -auto-approve</span>
<span class="comment"># EKS control plane creation takes ~12 minutes</span>
<span class="success-text">Apply complete! Resources: 22 added, 0 changed, 0 destroyed.
Outputs:
cluster_endpoint = "https://ABCDEF1234567890.gr7.us-east-1.eks.amazonaws.com"
cluster_name = "ray-ai-platform-test"
oidc_provider_arn = "arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/ABCDEF"</span>

<span class="comment"># Update local kubeconfig to authenticate with new EKS cluster</span>
<span class="prompt">$</span> <span class="command">aws eks update-kubeconfig --region us-east-1 --name ray-ai-platform-test</span>
<span class="prompt">$</span> <span class="command">kubectl get nodes</span></pre>
          </div>
        </div>
      </div>

      <!-- Layer 5 Tab -->
      <div id="layer-5" class="tab-content">
        <div class="terminal-window">
          <div class="terminal-header">
            <span class="terminal-title">bash &bull; terraform/platform</span>
            <button class="btn-copy" onclick="copySnippet(this)"><i class="fa-solid fa-copy"></i></button>
          </div>
          <div class="terminal-body">
            <pre><span class="prompt">$</span> <span class="command">cd ../platform</span>
<span class="prompt">$</span> <span class="command">terraform init</span>
<span class="prompt">$</span> <span class="command">terraform apply -auto-approve</span>
<span class="success-text">Apply complete! Resources: 11 added, 0 changed, 0 destroyed.
Outputs:
kuberay_helm_release = "kuberay-operator-v1.1.0"
karpenter_nodepool = "ray-workers"</span>

<span class="comment"># Verify KubeRay operator and Karpenter controller pods</span>
<span class="prompt">$</span> <span class="command">kubectl get pods -n kuberay-system</span>
<span class="prompt">$</span> <span class="command">kubectl get pods -n karpenter</span></pre>
          </div>
        </div>
      </div>

      <!-- Layer 6 Tab -->
      <div id="layer-6" class="tab-content">
        <div class="terminal-window">
          <div class="terminal-header">
            <span class="terminal-title">bash &bull; terraform/serverless</span>
            <button class="btn-copy" onclick="copySnippet(this)"><i class="fa-solid fa-copy"></i></button>
          </div>
          <div class="terminal-body">
            <pre><span class="prompt">$</span> <span class="command">cd ../serverless</span>
<span class="prompt">$</span> <span class="command">terraform init</span>
<span class="prompt">$</span> <span class="command">terraform apply -auto-approve</span>
<span class="success-text">Apply complete! Resources: 16 added, 0 changed, 0 destroyed.
Outputs:
state_machine_arn = "arn:aws:states:us-east-1:123456789012:stateMachine:sfn-corporate-data-pipeline"
lambda_function_arns = [
  "arn:aws:lambda:us-east-1:123456789012:function:sfn-corporate-discovery",
  "arn:aws:lambda:us-east-1:123456789012:function:sfn-corporate-validator",
  "arn:aws:lambda:us-east-1:123456789012:function:sfn-corporate-resolver",
  "arn:aws:lambda:us-east-1:123456789012:function:sfn-corporate-iceberg-sink",
  "arn:aws:lambda:us-east-1:123456789012:function:sfn-corporate-trainer",
  "arn:aws:lambda:us-east-1:123456789012:function:sfn-corporate-finalizer"
]
dlq_sqs_arn = "arn:aws:sqs:us-east-1:123456789012:sfn-corporate-dlq"</span></pre>
          </div>
        </div>
      </div>

    </div>

    <!-- Health Check & Rollback Procedures -->
    <div class="alert alert-info" style="margin-top: 30px;">
      <div class="alert-icon"><i class="fa-solid fa-circle-info"></i></div>
      <div>
        <strong>Deterministic Rollback Procedure:</strong> If an apply failure occurs midway through Layer 4 or 5, execute <code>terraform destroy</code> in reverse order (Layer 6 &rarr; Layer 5 &rarr; Layer 4). Never destroy Layer 1 (bootstrap) or Layer 3 (data) unless intentionally purging the entire data lakehouse.
      </div>
    </div>
  </div>
</section>
"""
