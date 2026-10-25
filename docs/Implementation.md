Implementation Guide --- Ray AI Platform on Kubernetes
Status: Implementation plan
Cloud: AWS
Runtime: Amazon EKS + KubeRay + Ray
Related design: architecture.md
Scope: A practical deployment and execution guide. Automated tests
are intentionally deferred until the infrastructure and application
baseline are implemented.
1. Purpose and implementation principles
This document turns architecture.md into an ordered implementation
plan. It is not a claim that the infrastructure has already been
deployed or verified.

The actual input datasets have not been provided. Their row counts,
column counts, names, formats beyond CSV, and business semantics are
therefore unknown. The implementation must not depend on a guessed fixed
schema such as corporate_name or annual_revenue being present in
every file.

The design will:
1. Discover new CSV files in a configured S3 input prefix on a
   schedule.
2. Inspect each file's headers and data types before processing.
3. Support different row counts and different numbers of columns.
4. Normalize and map fields only when the mapping is configured or
   unambiguous.
5. Quarantine or reject files with missing required business fields or
   ambiguous mappings rather than silently inventing meaning.
6. Resolve records that refer to the same company using explicit,
   explainable matching rules.
7. Write harmonized records to Apache Iceberg using transactional
   operations.
8. Train a small revenue-prediction model with Ray Train when usable
   target and feature fields are available.
9. Track file processing status and make retries safe.
10. Run on Kubernetes through a KubeRay-managed RayJob.
The system can inspect arbitrary CSV structures, but it cannot reliably
infer the meaning of every unknown column from its name or values alone.
For example, amount, value, or total could mean revenue, expenses,
transaction value, or something else. A schema-mapping configuration or
a review step is needed when meaning is unclear.
Scope control
Included in the first implementation:
- AWS infrastructure using Terraform.
- S3 input and output/warehouse locations.
- EKS and KubeRay.
- Separate stable system/head capacity and autoscaling worker
  capacity.
- Workload identity and least-privilege access.
- Scheduled discovery and a processing ledger.
- CSV inspection, entity resolution, Iceberg writes, and a minimal Ray
  Train workflow.
- CI/CD that builds the image and submits a RayJob.
- Operational logs, metrics, and a verification checklist.
Deferred until the infrastructure and application baseline work:
- Automated unit and integration tests.
- A large sample-data suite based on guessed business fields.
- LLM-based entity resolution requiring an external API key.
- GPU node pools.
- Ray Serve or a real-time prediction API.
- S3 event notifications/SQS, unless low-latency arrival processing
  becomes a requirement.
- A generalized schema-inference engine that attempts to interpret
  arbitrary business meaning without configuration.
2. Requirements versus implementation assumptions
2.1 Requirements from the assignment
The assignment requires a managed Kubernetes cluster, object storage,
KubeRay, at least two node/capacity pools, a Spot/preemptible worker
strategy, modular Terraform with decoupled state layers, a working
ray_pipeline.py, Ray Data and Ray Train configuration guidance,
deliberate EntityResolver placement, workload identity, an Iceberg
catalog, CI/CD that runs Terraform plan on pull requests and submits a
RayJob after merge, Prometheus metrics, secure Dashboard access,
centralized logs, two datasets of at least 1,000 records each, a README,
a serverless alternative, and a walkthrough demonstrating end-to-end
processing and failure handling.

The assignment does not prescribe an actual CSV schema or an external
CSV source location. It asks the candidate to create two datasets for
the exercise. Because the actual source data is currently unknown, this
guide does not assume that every future file will use the same schema.
2.2 Explicit implementation assumptions
  Area                    Initial decision        Why
  Cloud                   AWS                     Matches the proposed
                                                  architecture

  Kubernetes              EKS                     Managed Kubernetes
                                                  option

  Input                   S3 input prefix         Simple, durable file
                                                  landing zone

  Discovery               EventBridge Scheduler   Meets scheduled-job
                          invokes Lambda          intent without adding
                                                  event infrastructure

  File tracking           DynamoDB ledger         Coordinates claims,
                                                  retries, and completion
                                                  state

  Iceberg catalog         AWS Glue Data Catalog   Managed catalog option
                                                  for Iceberg

  Compute                 Stable On-Demand        Separates system
                          system/head capacity;   reliability from
                          worker autoscaling with elastic compute
                          Spot strategy           

  Job submission          Kubernetes RayJob CRD Required by the
                                                  assignment's CI/CD flow

  Model                   Small CPU-based         Demonstrates training
                          regression workflow     without GPU complexity
                          using Ray Train         

  Schema handling         Inspect first; use      Avoids assuming unknown
                          explicit mapping for    input columns
                          semantic fields         

  Tests                   Add after baseline      Matches the agreed work
                          infrastructure and      order
                          application are
                      implemented             
These are design choices, not facts supplied by the assignment. Pin
compatible dependency versions during implementation and record the
selected versions in the repository.
3. Repository structure
Use this as the target structure. Create files as each phase is
implemented; do not create placeholder code merely to make the tree look
complete.
ray-ai-platform/
├── README.md
├── architecture.md
├── IMPLEMENTATION.md
├── ray_pipeline.py
├── Dockerfile
├── pyproject.toml
├── config/
│   ├── schema-mappings/
│   └── pipeline.yaml
├── terraform/
│   ├── bootstrap/
│   ├── foundation/
│   ├── eks-platform/
│   ├── ray-platform/
│   └── modules/
│       ├── networking/
│       ├── storage-and-ledger/
│       ├── eks/
│       ├── workload-identity/
│       └── observability/
├── lambda/
│   └── discover_and_submit/
├── kubernetes/
│   ├── raycluster.yaml
│   ├── rayjob.yaml
│   └── monitoring/
├── sample-data/
│   └── README.md
├── tests/
│   ├── unit/
│   └── integration/
└── .github/
    └── workflows/
        └── deploy.yml
sample-data/README.md should explain the expected test-data contract
until the final synthetic datasets are generated. Do not invent a fixed
schema and then present it as the expected schema of real incoming data.
4. Implementation sequence
Implement in the following order. Each phase should produce a reviewable
result before the next phase begins.

Phase 1 --- Repository and configuration baseline
1. Create the repository structure.
2. Add this guide and architecture.md.
3. Define environment-specific values in Terraform variables and
   non-secret configuration.
4. Decide the AWS region, naming prefix, account/environment naming,
   and Terraform state backend.
5. Pin Terraform provider versions and application dependency versions.
6. Add .gitignore entries for Terraform state, plans, local
   environment files, credentials, and Python caches.
7. Document all required configuration keys without committing secret
   values.
Exit condition: the repository has a clear structure, configuration
conventions, and no secrets or Terraform state tracked in Git.

Phase 2 --- Terraform state bootstrap
Create the remote state backend before deploying the rest of the
infrastructure. A typical S3 backend uses a dedicated state bucket with
versioning, encryption, and tightly scoped access. If using a lock
mechanism supported by the selected Terraform version/backend, configure
it according to that version's official documentation.

The bootstrap layer is special: it may need to be applied using local
state once to create the remote state bucket, then migrated to the
remote backend. Document this one-time process. Do not store application
data and Terraform state in the same S3 prefix.

Exit condition: Terraform state is remote, encrypted, versioned, and
accessible only to the intended deployment identity.

Phase 3 --- AWS foundation
Provision the networking and shared cloud resources required by EKS and
the application:
- VPC and subnets across multiple Availability Zones.
- Private subnets for EKS worker nodes.
- Public subnets only where required by the selected network design.
- Appropriate routing and outbound access.
- S3 input and Iceberg warehouse locations, with public access
  blocked.
- DynamoDB processing ledger.
- ECR repository for the application image.
- Encryption and IAM policies.
- CloudWatch log groups or the selected centralized logging
  destination.
Use VPC endpoints where they are operationally justified and
cost-effective. Do not assume that endpoints eliminate every outbound
connectivity requirement: image pulls, package downloads, external APIs,
and AWS service access must be reviewed separately.

Exit condition: the foundation layer creates the required resources
and outputs their IDs/ARNs for later layers without embedding
environment-specific values in application code.

Phase 4 --- EKS platform
Provision EKS using a supported module or well-maintained Terraform
resources. Pin module/provider versions and inspect the plan before
applying.

Configure:
- Cluster endpoint access according to the environment's security
  requirements.
- Worker nodes in private subnets where practical.
- Kubernetes authentication and RBAC.
- Cluster logging appropriate to the assignment.
- Separate node groups or capacity configurations for stable
  system/head workloads and worker workloads.
- Cluster autoscaling capacity provisioning compatible with the chosen
  worker strategy.
- Workload identity using EKS Pod Identity or IRSA, chosen once and
  documented.
Do not give the application broad cluster-admin permissions. The Ray job
needs data permissions; only the submission component needs the narrowly
scoped permissions required to create or inspect the relevant RayJob
resources.

Exit condition: a deployment operator can authenticate to the
cluster, inspect nodes and namespaces, and verify that system and worker
capacity are separated.

Phase 5 --- KubeRay and Ray capacity
Install the KubeRay Operator using a pinned chart/version. Create a
dedicated namespace for Ray workloads.

Deploy a RayCluster with:
- A stable Ray Head group.
- An autoscaling worker group.
- Explicit CPU/memory requests and limits.
- A deliberate /dev/shm configuration.
- Ray object-store memory settings appropriate to pod memory.
- Pod labels, node selectors, affinity, tolerations, and security
  context.
- Worker capacity compatible with the cluster autoscaler or chosen
  node provisioner.
Ray autoscaling and Kubernetes node autoscaling solve different
problems. Ray decides how many worker pods are needed; the Kubernetes
node provisioning layer supplies EC2 capacity to schedule those pods.
EntityResolver placement
Use two scheduling controls:
1. Kubernetes scheduling controls place the designated Ray worker pods
   onto the intended node pool.
2. A Ray custom resource is advertised only by that Ray worker group,
   and the EntityResolver actor requests that resource.
For example, a worker group may advertise a custom resource such as
entity_resolver_slot: 1, and the actor may request
resources={"entity_resolver_slot": 1}. The resource name and
quantities must match exactly. This is a scheduling signal, not a
guarantee that a specific physical machine or GPU exists.

The initial resolver can be CPU-only. Do not create a GPU pool merely
because the starter comments mention GPU as a possibility. If a later
implementation uses an external LLM API, its credentials should be
supplied through the approved secret mechanism and only to the actor
that needs them.

Verify placement from Ray's runtime state/logs during the walkthrough;
YAML configuration alone is not sufficient evidence.
Spot worker strategy
- Keep the Ray Head and essential system components on stable
  On-Demand capacity.
- Use Spot for interruptible, retryable worker tasks.
- Use multiple compatible instance types/AZs where feasible.
- Configure pod disruption handling and application retries.
- Keep durable state in S3, DynamoDB, and Iceberg, not only in worker
  memory.
- Provide a capacity recovery path, such as an On-Demand fallback or a
  documented reduced-capacity mode.
- Confirm that a Spot interruption causes a task/job retry or a clear
  failed status rather than silent data loss.
Do not claim Spot resilience merely because the node group uses Spot.
Demonstrate how interrupted work is recovered and how the pipeline
avoids duplicate committed output.

Exit condition: a sample Ray job can execute on the cluster, the
worker group can scale, and the resolver actor is observed on the
intended Ray worker group.

Phase 6 --- Data storage, catalog, and workload identity
Create separate S3 prefixes or buckets for:
- Incoming CSV files.
- Iceberg warehouse/table data.
- Model artifacts and run outputs.
- Optional manifests and diagnostics.
Configure the selected Iceberg catalog, initially AWS Glue Data Catalog.
Configure the Ray job with the catalog name, warehouse location, region,
and required Iceberg/PyIceberg settings. Keep configuration separate
from source code.

Grant the Ray workload only the required access to read input objects,
read/write the warehouse, and write model artifacts. Grant the
discovery/submission component only the permissions required to list
candidate objects, update ledger records, and submit/inspect RayJobs. Do
not share one broad role across all components.

Use workload identity instead of long-lived access keys in Kubernetes
Secrets or environment variables. Ensure the actual Kubernetes service
account is mapped to the intended cloud role and verify access from a
running pod.

Exit condition: the Ray workload can read an approved input object
and access the configured Iceberg catalog and warehouse using its
workload identity, without static AWS credentials in the image or
repository.

Phase 7 --- Generic CSV inspection and schema handling
Because incoming data shape is unknown, the application should separate
structural inspection from business interpretation.
Structural inspection
For every file, record:
- S3 bucket, key, and version ID if available.
- File size, modification time, and content checksum/ETag where
  useful.
- Header names and duplicate/empty column names.
- Inferred data types and null rates from a bounded sample.
- Row count when it can be obtained safely and economically.
- Parsing errors, malformed rows, encoding issues, and delimiter
  issues.
Do not assume all files fit in memory. Use Ray Data or chunked readers
for larger files; use pandas only for bounded samples or small batches.
A full-file row count can require a complete scan and should not be
treated as free metadata.
Business field mapping
Use a versioned mapping configuration to map source-specific columns to
canonical fields. The canonical model should be deliberately small and
should only include fields the pipeline actually needs, for example:
- A company name or legal name candidate.
- One or more identifiers, if available (registration number, tax ID,
  domain, or another stable identifier).
- Country or jurisdiction, if available.
- Annual revenue target, if present and valid.
- Additional source attributes retained as provenance or in a flexible
  payload.
These are candidate canonical concepts, not a required input CSV schema.
A file may have different column names and extra columns. A source
mapping could map legal_entity, org_name, or supplier to the
canonical company-name field---but only when configured or confirmed by
a defensible rule.

For every mapping, store the source file and original column name.
Preserve unrecognized columns rather than silently dropping them; a raw
JSON payload or source-specific staging table can preserve them. Do not
automatically merge unrelated columns simply because they share a data
type.
Missing or ambiguous fields
- If no company-identifying field can be mapped, quarantine the file
  or fail it with a clear schema error.
- If revenue prediction is required but no valid revenue target
  exists, the ingestion and entity-resolution steps may still be
  meaningful, but model training must be marked as skipped or failed
  according to the agreed run policy. Do not fabricate a target.
- If two columns could plausibly represent revenue, require an
  explicit mapping.
- Keep a schema report with the reason for acceptance, warning, or
  rejection.
Exit condition: the pipeline can explain what it found in a file,
what fields it mapped, what it could not infer, and why it accepted or
rejected the file.

Phase 8 --- Entity resolution
The starter code's hash-based canonical ID is only a placeholder and
should not be treated as production entity resolution. Python's built-in
hash() is not a stable cross-process identifier and can change between
interpreter runs.

Implement matching in increasing order of confidence:
1. Strong identifiers: exact match on a trusted company
   registration/tax identifier, scoped by jurisdiction where relevant.
2. Normalized names: Unicode normalization, whitespace/punctuation
   cleanup, case folding, and conservative legal-suffix normalization.
3. Supporting attributes: compare country, domain, address, or
   other fields only if present and mapped.
4. Fuzzy candidates: use a thresholded similarity score to propose
   matches, not to merge every vaguely similar name automatically.
5. Ambiguous cases: retain an unresolved status or send to a
   review/quarantine output instead of forcing a merge.
Create a deterministic canonical identifier from a stable source
identifier or a persistent entity registry. Do not generate IDs using
Python's built-in hash. Preserve match evidence, match method,
confidence/score, and source provenance so decisions can be explained.

A record-level match and a file-level duplicate are different problems.
File-level idempotency prevents the same file from being processed
repeatedly; entity resolution merges records about the same company
across different files.

Exit condition: repeated runs produce stable canonical IDs, and
ambiguous matches are visible rather than silently merged.

Phase 9 --- Transactional Iceberg writes
Use Apache Iceberg as the durable harmonized table. Configure the
catalog and warehouse explicitly and test the selected PyIceberg/Iceberg
integration with the chosen AWS Glue catalog version.

Recommended flow:
1. Read and validate the claimed input manifest.
2. Normalize and resolve records.
3. Add run ID, source file identity, ingestion timestamp, mapping
   version, and resolution evidence.
4. Write to a staging/batch representation if needed.
5. Apply an idempotent merge/upsert strategy keyed by stable
   canonical/source identifiers.
6. Commit using Iceberg's transactional table operation.
7. Verify the commit and expected row/run metadata.
8. Only then report the data-write phase as successful.
Do not assume that a simple append is idempotent. If a retry appends the
same rows again, duplicates may result. The chosen merge strategy must
be compatible with the Iceberg library and catalog configuration
actually deployed.

The processing ledger and Iceberg transaction are separate systems; they
do not participate in one shared atomic transaction. Design for safe
retries: the ledger must not mark a run complete before the Iceberg
commit is confirmed, and the Iceberg write must tolerate a job retry
after a commit whose acknowledgement was lost.

Exit condition: a successful run produces a visible Iceberg commit,
and retrying the same input does not create duplicate logical records.

Phase 10 --- Revenue model with Ray Train
The assignment explicitly requires training a model to predict annual
company revenue using harmonized data. Keep this first version small and
CPU-based.

Implementation outline:
1. Select the canonical revenue target only when a valid target mapping
   exists.
2. Exclude IDs, raw labels, and leakage-prone fields from the feature
   set.
3. Handle missing values and categorical fields using a documented
   preprocessing pipeline.
4. Split data into training and validation sets.
5. Train a basic regression model through Ray Train. A compatible
   CPU-based XGBoost integration is one possible choice; pin versions
   and follow that integration's current API.
6. Record metrics such as MAE and RMSE on a held-out validation set.
7. Save the model artifact, preprocessing metadata, feature list,
   training data/run reference, and metrics to S3.
8. Mark model training as skipped/failed if the dataset does not
   contain a reliable revenue target or sufficient usable examples.
Do not claim that the model has meaningful predictive accuracy merely
because training completes. With synthetic data, metrics only validate
the workflow and may not represent real-world performance. The output
should say whether the model was trained, what data/target was used, and
what evaluation metrics were measured.

The first implementation does not need a model-serving endpoint. The
assignment asks for training, not an online prediction API.

Exit condition: the job either saves a model and evaluation results
or emits an explicit, explainable training-skipped/failure status.

Phase 11 --- Scheduled discovery and duplicate prevention
The scheduled discovery component is an implementation choice to support
new-file processing; the assignment itself does not mandate a particular
trigger.
File identity
Prefer a stable identity based on:
- S3 bucket.
- Object key.
- Version ID when bucket versioning is enabled.
If versioning is not enabled, document how overwrites are handled. An
ETag is useful metadata but should not universally be treated as a
cryptographic content hash or as a complete identity in every upload
mode.
Ledger lifecycle
Use conditional writes in DynamoDB to prevent two scheduler invocations
from claiming the same input simultaneously. A minimal lifecycle is:

DISCOVERED -> PROCESSING -> COMPLETED

A failed run may transition to FAILED and later be retried through an
explicit claim/retry rule. Store a lease/claim expiry so a crashed
submitter or worker does not leave a file locked forever.

Store at least:
- File identity and S3 location.
- Processing status.
- Run ID and RayJob name/namespace.
- Attempt count.
- Claim/lease expiry.
- Start and completion timestamps.
- Output commit identifier or equivalent success evidence.
- Concise error category and message.
The discovery Lambda should submit the exact input manifest to the
RayJob. It must not merely tell the job to "process everything in the
bucket," because new files could arrive after the claim and make the
run's scope ambiguous.

The job should communicate its actual terminal result to the
orchestrator or ledger-update path. Submission success is not processing
success. A periodic reconciliation mechanism can be added if needed to
recover jobs whose final status callback was lost.

Exit condition: overlapping discovery runs do not claim the same
file concurrently, abandoned claims can be recovered, and completed
files are not reprocessed unless a new version or an explicit replay is
requested.

Phase 12 --- CI/CD
Implement GitHub Actions with separate pull-request and merge behavior.
Pull request
- Run formatting and static validation for Terraform.
- Run terraform fmt -check and terraform validate for the relevant
  layers.
- Build the application image or at minimum verify the Docker build.
- Run available lightweight code checks as the application is
  implemented.
- Generate a Terraform plan for review; do not automatically apply
  production changes from untrusted pull requests.
- Use least-privilege credentials and avoid exposing secrets to forked
  PR workflows.
Merge to the deployment branch
1. Authenticate to AWS using GitHub OIDC federation, not a long-lived
   access key.
2. Build the application image.
3. Tag it with an immutable commit SHA or equivalent immutable
   identifier.
4. Push the image to ECR.
5. Update the RayJob image reference.
6. Submit the RayJob CRD using an authenticated deployment identity.
7. Wait for the job to reach a terminal state or publish a clear job
   reference for operators.
8. Fail the workflow if the job fails; do not report deployment success
   based only on successful CRD creation.
Terraform apply should be a controlled deployment step with environment
protection and state locking. A pull request runs a plan; merge does not
automatically imply that every infrastructure change should be applied
without review.

Exit condition: the workflow builds and pushes the image, submits
the RayJob, and reports the actual execution outcome.

Phase 13 --- Observability and operational access
Implement the minimum required observability:
- Prometheus scraping for Ray metrics and Kubernetes/node metrics.
- Dashboard panels for Ray worker availability, pending/running/failed
  tasks, job duration, resource use, and node capacity.
- Centralized Head and Worker stdout/stderr logs.
- Ray Dashboard reachable only through an approved secure path, such
  as authenticated port-forwarding or private access.
- Alerts or clear operational queries for failed jobs, repeated
  retries, worker shortages, and stuck PROCESSING ledger entries.
Do not expose the Ray Dashboard publicly without authentication and
network restrictions. Do not log credentials, access tokens, or
sensitive raw data.

Exit condition: an operator can identify a failed RayJob, inspect
its logs, understand the failure category, and verify whether the
Iceberg commit and model artifact were produced.
5. Terraform implementation guidance
Use decoupled state layers so that foundational resources do not need to
be recreated when application-level configuration changes.
5.1 Suggested state layers
  Layer                   Responsibility          Example outputs
  bootstrap             Terraform remote state  state bucket name
                          bucket and state access 

  foundation            VPC, S3, DynamoDB, ECR, VPC/subnet IDs, bucket
                          shared IAM              names, table name,
                                                  repository URL

  eks-platform          EKS, node capacity,     cluster name/endpoint,
                          cluster access,         node groups, OIDC/Pod
                          workload identity base  Identity references

  ray-platform          KubeRay installation,   namespace, RayCluster
                          namespace, RayCluster,  name
                      monitoring integration  
A layer should consume stable outputs from the previous layer. Avoid
copying resource IDs into multiple .tf files manually. Use
remote-state outputs or a controlled environment configuration
mechanism.
5.2 Example: S3 data bucket module
This is a representative starting snippet, not a complete foundation
module. Add naming, lifecycle, logging, and IAM policies to match the
final environment.

resource "aws_s3_bucket" "data" {
  bucket = var.bucket_name

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
Use separate buckets or separate restricted prefixes for input, Iceberg
warehouse, and model artifacts. Versioning helps distinguish a new
object version from a previously processed version, but it does not
replace the DynamoDB processing ledger.
5.3 Example: DynamoDB ledger module

resource "aws_dynamodb_table" "processing_ledger" {
  name         = var.ledger_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "file_id"

  attribute {
    name = "file_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
The application should use conditional writes such as "create only if
this file_id does not exist" when claiming a new file. If retries and
leases need conditional updates, implement those conditions in the
application code. Do not rely on Terraform to enforce runtime state
transitions.
5.4 Example: EKS cluster module call
This is an illustrative module call. Confirm the selected module version
and its input schema before use; the exact inputs can change between
versions.

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = var.eks_module_version

  cluster_name    = "${var.project_name}-${var.environment}"
  cluster_version = var.kubernetes_version

  vpc_id     = var.vpc_id
  subnet_ids = var.private_subnet_ids

  cluster_endpoint_public_access = false

  eks_managed_node_groups = {
    system = {
      instance_types = var.system_instance_types
      capacity_type  = "ON_DEMAND"
      min_size       = 1
      desired_size   = 2
      max_size       = 3

      labels = {
        workload = "system"
      }
    }

    ray_workers = {
      instance_types = var.worker_instance_types
      capacity_type  = "SPOT"
      min_size       = 0
      desired_size   = 0
      max_size       = var.worker_max_size

      labels = {
        workload = "ray-worker"
      }
    }
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}
This sample illustrates separation of capacity only. It is not a
complete production EKS configuration. The final module must also define
access entries/roles, required add-ons, node security settings, and the
selected node autoscaling mechanism. If using Karpenter or a different
autoscaler, design the node provisioning and Spot fallback consistently
rather than layering multiple autoscalers without a clear ownership
model.

Do not assume a worker node group with desired_size = 0 will scale by
itself. Configure and verify the cluster autoscaling mechanism and its
permissions.
5.5 Example: workload IAM policy shape
Use separate IAM roles for the Ray workload and the discovery/submission
component. The following illustrates the principle only; scope resources
to the actual buckets, prefixes, table, catalog, and ledger.

data "aws_iam_policy_document" "ray_data_access" {
  statement {
    sid       = "ReadInputObjects"
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:GetObjectVersion"]
    resources = ["${var.input_bucket_arn}/${var.input_prefix}/*"]
  }

  statement {
    sid       = "ListInputPrefix"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [var.input_bucket_arn]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["${var.input_prefix}/*"]
    }
  }

  statement {
    sid    = "WriteIcebergWarehouse"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket"
    ]
    resources = [
      var.warehouse_bucket_arn,
      "${var.warehouse_bucket_arn}/${var.warehouse_prefix}/*"
    ]
  }
}
The actual Iceberg workflow may require additional S3 and Glue actions
depending on catalog/table operations. Derive the final policy from the
tested calls and narrow it to the minimum required. If using a
customer-managed KMS key, add only the necessary KMS permissions. The
example is not a drop-in complete policy.
5.6 Terraform operating rules
- Pin provider and module versions.
- Keep state separate by layer and environment.
- Never commit .tfstate, plan files, credentials, or generated
  secrets.
- Use variables for account-specific values and output stable
  identifiers.
- Review every plan before applying.
- Use CI for fmt, validate, and plan; gate apply with the intended
  approval process.
- Do not put application data transformations into Terraform.
- Avoid creating a second infrastructure mechanism for the same
  responsibility.
6. Application configuration contract
Keep runtime settings in environment variables or a non-secret
configuration file, and secrets in the cloud/Kubernetes secret mechanism
selected for the deployment.

Suggested non-secret settings:
  Setting                             Purpose
  AWS_REGION                        Region for AWS APIs and the Iceberg
                                      catalog

  INPUT_BUCKET                      S3 bucket containing incoming files

  INPUT_PREFIX                      Prefix used by scheduled discovery

  ICEBERG_CATALOG                   Catalog identifier/configuration

  ICEBERG_DATABASE                  Namespace/database for the target
                                      table

  ICEBERG_TABLE                     Target table name,
                                      e.g. corporate_registry

  ICEBERG_WAREHOUSE                 Warehouse URI

  MODEL_OUTPUT_URI                  S3 destination for model artifacts

  LEDGER_TABLE                      DynamoDB ledger name

  RUN_ID                            Unique pipeline execution
                                      identifier

  INPUT_MANIFEST_URI or manifest    Exact files claimed for this run
  payload                             

  SCHEMA_MAPPING_URI                Optional versioned
                                      source-to-canonical mapping
  LOG_LEVEL                         Logging verbosity
Do not require LLM_API_KEY for the baseline unless the implementation
actually calls an external LLM. A deterministic rules-based resolver is
simpler to deploy, test, and explain. If an external model is later
added, use a secret manager and restrict secret access to the component
that needs it.
7. RayJob lifecycle
The CI/CD workflow and scheduled discovery may both submit a RayJob,
but they should use explicit run inputs and a clear purpose.

A RayJob should define:
- A unique job name or run ID.
- The immutable application image tag.
- The target Ray cluster or the RayJob's configured cluster lifecycle.
- The Python entrypoint.
- CPU/memory resources and runtime configuration.
- The exact input manifest.
- The schema-mapping configuration version.
- The output table/catalog settings.
- Appropriate service account/workload identity.
- Retry and shutdown behavior consistent with the idempotency design.
Keep secrets out of the image and Git. Do not put a whole-bucket
wildcard as the job input when the scheduler has already claimed
specific files.

The RayJob controller's status should be observed after creation. The
orchestration layer should distinguish at least: - CRD
accepted/submitted. - Job running. - Job succeeded. - Job failed. - Job
status unknown or controller unavailable.

A successful kubectl apply only proves that the resource was accepted
by the Kubernetes API; it does not prove that the pipeline ran
successfully.
8. Failure handling and recovery
  Failure                             Expected handling
  CSV parse error                     Record file-level failure and a
                                      clear parse/schema reason; do not
                                      mark complete

  Unknown/ambiguous field mapping     Quarantine or fail validation; do
                                      not guess silently

  Missing revenue target              Complete data processing only if
                                      policy allows; mark model step
                                      skipped/failed explicitly

  Resolver actor unavailable          Ray retries or fails the task;
                                      retain run status and avoid
                                      committing partial unresolved
                                      results as complete

  Spot interruption                   Retry eligible work on replacement
                                      capacity; keep durable state
                                      outside worker memory

  Ray worker/pod crash                Let Ray/Kubernetes recover
                                      according to configured policies;
                                      record terminal job status

  Iceberg commit failure              Do not mark the file complete;
                                      retry with an idempotent write
                                      strategy

  Commit succeeds but acknowledgement On retry, inspect stable run/source
  is lost                             keys and make the operation safe to
                                      repeat

  Lambda submission failure           Record a recoverable failure and
                                      retry with conditional ledger rules

  Scheduler overlaps                  Conditional ledger claim prevents
                                      simultaneous claims for the same
                                      file

  Job remains PROCESSING            Lease expiry/reconciliation
                                      identifies abandoned work and
                                      permits controlled recovery

  Model training failure              Preserve ingestion/Iceberg outcome
                                      separately from model status;
                                      follow the documented overall run
                                      policy

  Metrics/logging unavailable         Do not log secrets; preserve
                                      application/ledger status and alert
                                  on observability degradation
Define whether a run is considered overall successful if the Iceberg
commit succeeds but model training is skipped because no valid target
exists. The initial recommendation is to represent the data and model
stages separately, with an overall result that explicitly reports both
rather than hiding a skipped model behind a generic success message.
9. Deployment walkthrough
Run the deployment in a disposable development environment first. The
exact commands depend on the final module versions, region, naming
choices, and authentication method; replace placeholders with actual
outputs rather than copying guessed IDs.
Step 1 --- Local prerequisites
Install and verify:
- AWS CLI.
- Terraform version pinned by the repository.
- kubectl.
- Helm.
- Docker or a compatible image builder.
- Python version supported by the pinned Ray release.
- GitHub repository and an AWS OIDC role for CI/CD if using GitHub
  Actions.
Authenticate using an approved AWS identity. Confirm the account and
region before provisioning resources.
Step 2 --- Bootstrap Terraform state
1. Initialize the bootstrap Terraform layer.
2. Review the plan.
3. Apply it to create the remote state backend.
4. Configure the remaining layers to use the remote backend.
5. Verify state locking/access and ensure state files are not tracked
   in Git.
Step 3 --- Provision foundation resources
1. Configure environment variables and Terraform variable files.
2. Run terraform fmt -check.
3. Run terraform init.
4. Run terraform validate.
5. Run terraform plan and inspect the changes.
6. Apply the foundation layer.
7. Record the output bucket names, ledger table, ECR repository, VPC,
   and subnet identifiers.
Do not paste secrets into terminal history or commit local variable
files containing secrets.
Step 4 --- Provision EKS
1. Initialize and validate the EKS platform layer.
2. Review the cluster endpoint, subnets, node capacity, IAM access, and
   workload identity configuration in the plan.
3. Apply the layer.
4. Configure kubectl for the created cluster.
5. Verify that the cluster and expected nodes are available.
6. Confirm that the Kubernetes identity has only the intended
   permissions.
Step 5 --- Install KubeRay and deploy RayCluster
1. Install the pinned KubeRay Operator chart.
2. Create the Ray namespace.
3. Apply the RayCluster manifest.
4. Wait for Head and worker pods to become ready.
5. Verify node selectors, tolerations, custom resources, shared memory,
   and resource limits.
6. Access the Ray Dashboard through the approved private method.
7. Submit a minimal Ray smoke job before running the full pipeline.
Step 6 --- Configure S3, DynamoDB, and Iceberg access
1. Verify the workload identity mapping for the Ray service account.
2. From a temporary diagnostic pod using the same identity, verify only
   the intended S3 and catalog operations.
3. Confirm that no static AWS keys are required.
4. Confirm that the Glue catalog and warehouse location are consistent
   across the job and configuration.
5. Confirm that the application role cannot access unrelated buckets or
   tables.
Step 7 --- Build and publish the application image
1. Pin Python dependencies.
2. Build the Docker image locally or in CI.
3. Run a basic import/startup check.
4. Tag the image with a commit SHA.
5. Push it to ECR using the deployment identity.
6. Confirm that the Ray worker nodes can pull the image.
Step 8 --- Prepare the input data contract
1. Upload a CSV to the configured input prefix.
2. Inspect the header and a bounded sample without assuming the field
   names.
3. Create or select the versioned schema mapping for the source.
4. Confirm that the mapping identifies the company fields needed for
   entity resolution.
5. Confirm that a revenue target is available and correctly mapped if
   training is expected for this run.
6. Record how the file's identity/version will be represented in the
   ledger.
If the actual data schema is not yet available, validate the inspection
and rejection paths with controlled temporary files, but do not treat
those files as the final assignment datasets.
Step 9 --- Submit a RayJob
Submit the RayJob using the approved identity and the immutable image
tag. Include the exact input manifest, run ID, catalog/table
configuration, and schema mapping version.

Observe the Kubernetes RayJob status and Ray logs. Wait for the actual
terminal result. If it fails, diagnose the recorded failure before
retrying; do not simply resubmit the same workload without checking the
ledger and Iceberg output.
Step 10 --- Verify end-to-end output
For a successful data-processing run, verify:
- The intended input file appears in the ledger with the correct
  identity.
- The job processed only the manifest claimed for that run.
- The schema report lists detected columns, mappings, warnings, and
  rejected/unknown fields.
- Entity-resolution output contains stable canonical identifiers and
  match evidence.
- The Iceberg table has a confirmed committed update.
- Re-running the same input does not create duplicate logical records.
- The model step either saves an artifact and evaluation metrics or
  reports an explicit skip/failure reason.
- The ledger reaches its terminal state only after the required output
  checks complete.
- Logs and metrics make the run traceable by run ID and file identity.
Step 11 --- Validate the scheduled discovery flow
After manual RayJob execution works:
1. Enable the EventBridge schedule.
2. Upload a new file under the input prefix.
3. Wait for the next scheduled discovery.
4. Verify the file is claimed once and a RayJob is submitted.
5. Upload no new files and confirm that completed files are not
   resubmitted.
6. Test overlapping discovery invocations in a controlled environment.
7. Test a failed run and confirm that the retry path is explicit and
   safe.
Step 12 --- Configure CI/CD
1. Configure GitHub OIDC federation to AWS.
2. Set repository/environment variables and permissions.
3. Open a pull request and verify Terraform plan and validation
   behavior.
4. Merge a controlled change to the deployment branch.
5. Verify image build/push and RayJob submission.
6. Confirm that CI reports the actual RayJob result, not just resource
   creation.
7. Apply infrastructure changes only through the reviewed environment
   process.
Step 13 --- Review cost and remove resources
Before running expensive or long-lived resources, review the expected
EKS, EC2, NAT/data transfer, storage, logging, and monitoring costs.

When the exercise is complete, remove resources in reverse dependency
order. Preserve any artifacts needed for the walkthrough. Do not destroy
the Terraform state backend until all managed resources and state
dependencies have been intentionally retired.
10. Verification checklist
This checklist is intentionally open. Check an item only after
observing the result in the target environment. Test implementation is
deferred until the infrastructure and application baseline is complete.
Repository and configuration
- [ ] Repository structure and setup documentation are present.
- [ ] Terraform/provider/module versions are pinned.
- [ ] No secrets, access keys, state files, or plan files are
  committed.
- [ ] Environment-specific configuration is externalized.
- [ ] Source requirements and implementation assumptions are
  documented separately.
Infrastructure
- [ ] Terraform state is remote, encrypted, versioned, and
  access-controlled.
- [ ] Terraform layers are separated and have clear inputs/outputs.
- [ ] EKS is deployed with the intended endpoint/network access.
- [ ] System/head capacity is separated from autoscaling worker
  capacity.
- [ ] Worker capacity can scale from zero or its configured minimum.
- [ ] Kubernetes node autoscaling/provisioning is configured and
  verified.
- [ ] Spot interruption behavior and fallback/recovery are documented
  and exercised.
- [ ] S3 public access is blocked and encryption is enabled.
- [ ] DynamoDB ledger and ECR repository exist.
- [ ] Resource tags and cost controls are applied.
Ray and scheduling
- [ ] KubeRay Operator is installed at the pinned version.
- [ ] RayCluster Head and worker pods become ready.
- [ ] Ray shared memory and object-store settings are appropriate for
  pod memory.
- [ ] A Ray smoke job completes.
- [ ] EntityResolver is observed running on the intended Ray worker
  group.
- [ ] Worker autoscaling and node provisioning work together.
- [ ] Ray Dashboard is available only through the approved secure
  access path.
Data and application
- [ ] The application inspects CSV structure without assuming fixed
  column names.
- [ ] Ambiguous or missing semantic mappings produce a clear
  warning/rejection.
- [ ] Source provenance and unrecognized fields are preserved
  according to policy.
- [ ] Entity resolution uses stable identifiers and explainable match
  evidence.
- [ ] The same input file cannot be concurrently claimed by two runs.
- [ ] Iceberg writes use a verified transactional, idempotent
  strategy.
- [ ] A committed Iceberg result is confirmed before the ledger marks
  the file complete.
- [ ] Revenue model training uses an explicitly mapped target and
  reports evaluation metrics.
- [ ] Missing/invalid revenue targets result in an explicit model-step
  status, not fabricated data.
- [ ] Model artifacts and metadata are written to the intended S3
  location.
- [ ] Retrying a run after a failure does not create duplicate logical
  records.
CI/CD and operations
- [ ] Pull requests run Terraform validation and produce a reviewable
  plan.
- [ ] GitHub Actions authenticates using OIDC or another approved
  short-lived identity.
- [ ] Merge builds and pushes an immutable image tag.
- [ ] CI submits a RayJob and checks its actual terminal status.
- [ ] Prometheus collects relevant Ray and Kubernetes/node metrics.
- [ ] Head and worker logs are centralized and searchable by run ID.
- [ ] A failed job can be diagnosed from status, logs, and metrics.
- [ ] Scheduled discovery submits only newly eligible inputs.
- [ ] Abandoned claims and failed jobs can be recovered safely.
- [ ] A serverless alternative and its trade-offs are documented.
End-to-end demonstration
- [ ] A newly discovered CSV is processed through the complete
  pipeline.
- [ ] The schema inspection/mapping decision is visible.
- [ ] Entity resolution output is inspected.
- [ ] An Iceberg commit is verified.
- [ ] Model training succeeds or reports a justified skip/failure.
- [ ] Reprocessing the same file does not create duplicate logical
  output.
- [ ] A controlled failure is demonstrated and its recovery behavior
  is explained.
- [ ] The walkthrough distinguishes observed results from design
  intentions.
11. Serverless alternative
The serverless alternative should be documented, not implemented as a
second platform for this assignment.

A possible alternative is scheduled orchestration with EventBridge,
Lambda for lightweight coordination, object storage, and a
managed/serverless data-processing or ML service for the heavier
processing stages. The exact services depend on the required Iceberg
compatibility, workload size, and supported runtime.

Trade-offs to explain:
- Less Kubernetes and cluster lifecycle management.
- Potentially simpler operations for intermittent workloads.
- Different execution and dependency constraints from Ray on EKS.
- Possible limits or additional integration work for the selected
  Iceberg catalog and distributed training workflow.
- Different cost characteristics for always-on versus bursty
  workloads.
The serverless alternative does not replace the required KubeRay
implementation; it is a design comparison for the README and
walkthrough.
12. Test plan --- deliberately deferred
Automated tests will be added after the infrastructure and application
baseline is complete. At that point, derive test cases from the actual
implemented interfaces rather than writing tests against guessed
schemas.

The later test phase should cover:
- Schema inspection and explicit field mapping.
- Unknown, ambiguous, malformed, and empty CSV inputs.
- Deterministic entity identifiers and ambiguous matches.
- File identity, conditional ledger claims, leases, and retries.
- Iceberg commit and repeat-run idempotency.
- Ray custom-resource placement.
- RayJob success/failure propagation.
- Revenue training with a valid target and explicit handling when the
  target is absent.
- End-to-end processing in a disposable environment.
Do not mark these tests as passed until they have actually run against
the implemented code and target environment.
13. Decisions to finalize during implementation
The following values are intentionally not invented in this document:
- AWS account and region.
- Terraform/provider/module versions.
- EKS/Kubernetes version and instance types.
- Exact schedule frequency.
- S3 bucket names and prefixes.
- Ledger key and lease policy details.
- Canonical company fields and source-specific mapping rules.
- Iceberg table schema and merge key.
- Revenue target and valid model features.
- Ray, KubeRay, PyIceberg, Glue catalog, and training framework
  versions.
- CI deployment branch and approval policy.
- Cost budget and resource cleanup policy.
Resolve each item when its implementation phase begins. Keep the
selected value in configuration or versioned documentation and avoid
scattering it through source code.
14. Definition of implementation-ready
This guide is ready to drive implementation when the team can follow the
phases in order and knows which choices remain environment-specific. The
overall solution is ready for the assignment walkthrough only after the
relevant checklist items have been observed in a working environment.

The main acceptance principle is simple: provisioning infrastructure
is not the same as delivering a working pipeline. The final
demonstration must show a claimed input file moving through inspection,
entity resolution, a confirmed Iceberg transaction, and a real
model-training attempt, with an explicit result for every stage.