Base Platform Requirements
1. Purpose
Build an automated, production-like data-processing platform on AWS that
receives corporate data in CSV format from multiple sources, identifies
records belonging to the same company, maintains a harmonized company
registry in Apache Iceberg, and trains a machine-learning model to
predict annual company revenue.

The platform will use Ray for distributed Python execution and
Kubernetes (Amazon EKS) as its execution environment. Infrastructure
will be provisioned using Terraform, workloads will be deployed through
CI/CD, and the platform will provide monitoring, logging, security
controls, and job-status visibility.

This document defines the baseline platform and application requirements
for the take-home assignment. It distinguishes requirements stated in
the assignment from implementation decisions that still need to be
confirmed.
2. Problem Statement
Multiple data sources provide corporate information in CSV files. The
files may contain financial data, supplier or supply-chain information,
and other relevant company attributes.

The incoming records may: - Describe different companies. - Describe the
same company using different names or naming conventions. - Contain
complementary information about a company across multiple datasets. -
Contain incomplete, inconsistent, or ambiguous information that requires
validation.

The system must process these files, determine which records represent
the same company, create a consistent representation of each company,
and persist the harmonized data in an Apache Iceberg table.

The complete assignment also requires using the harmonized data to train
a machine-learning model that predicts annual company revenue.
3. Objectives
The platform must:
1. Receive or make available two or more corporate CSV datasets for
   processing.
2. Automatically initiate processing when a new input file or dataset
   is ready, using a trigger mechanism selected during implementation.
3. Validate input files and normalize relevant fields.
4. Identify records that refer to the same company, including records
   with differing company names.
5. Assign a stable canonical company identifier to resolved companies.
6. Create or update a harmonized company registry in Apache Iceberg
   using transactional table operations.
7. Train and evaluate a machine-learning model to predict annual
   company revenue.
8. Run the workload on Ray, with infrastructure managed through
   Kubernetes and KubeRay.
9. Provide repeatable deployment, monitoring, logging, and failure
   visibility.
10. Document setup, architecture, Spot-instance strategy, and a
    serverless alternative.
4. End-to-End Workflow
Stage 1 --- Data arrival
Corporate CSV files are supplied by separate data sources. Example
source categories include financial and supply-chain data.

Expected input: CSV files containing company records and relevant
attributes.

Requirement from the assignment: Create two datasets with at least
1,000 records each for the exercise.

Implementation decision still required: Select the file-arrival
location and event-trigger mechanism. For example, files could be placed
in Amazon S3 and an event-driven mechanism could initiate processing.
The assignment does not prescribe a specific trigger service.
Stage 2 --- Automatic pipeline trigger
When new data is available, the system should start the processing
workflow without requiring an engineer to manually execute the Python
script.

The trigger must identify the input to process and provide enough
context for the job to read the correct files.

The implementation must consider duplicate notifications, repeated
submissions, and failed job launches so that the same input is not
accidentally processed as unrelated new data.
Stage 3 --- Ingestion and validation
The pipeline reads the input CSV files and validates them before entity
resolution.

Validation should cover, as applicable: - Required columns and schema
compatibility. - Empty or malformed files. - Data types and required
values. - Duplicate or invalid records. - Consistent representations of
company names and relevant attributes.

Invalid records should be handled deliberately, such as by recording
validation errors and isolating rejected data rather than silently
discarding it.

The ingestion implementation must return usable data for subsequent
processing. The supplied assignment code contains an ingestion
placeholder that must be implemented.
Stage 4 --- Entity resolution and harmonization
The pipeline must determine which records refer to the same real-world
company.

The resolver should use relevant attributes available in the datasets.
Company-name similarity alone must not be treated as conclusive evidence
that two records belong to the same company.

The implementation should: - Normalize company names and relevant
fields. - Use available identifiers and attributes to support
matching. - Assign stable canonical company IDs to resolved entities. -
Handle ambiguous or low-confidence matches explicitly. - Preserve
relevant source information and provenance where practical. - Avoid
silently merging distinct companies. - Be designed for repeatable
processing of the same input.

The current assignment skeleton simulates resolution using Python's
built-in hash() and marks all records as resolved. This is placeholder
logic and must be replaced with meaningful entity-resolution logic.
Stage 5 --- Apache Iceberg registry
The harmonized data must be written to an Apache Iceberg table named
corporate_registry.

The table update must support the intended transactional behavior. The
pipeline should distinguish between: - A company not previously present
in the registry. - An existing company receiving new or updated
information. - A record that matches an existing company but contains
conflicting attributes. - An ambiguous record that requires further
handling.

The implementation must configure: - Durable storage for Iceberg data
and metadata. - An Iceberg catalog for table discovery and metadata
management. - The permissions required for the Ray workload to read and
write the relevant resources. - The actual write or upsert operation. -
Validation that the transaction completed and the expected data is
present.

Proposed AWS implementation choice: Amazon S3 for storage and AWS
Glue Data Catalog as the Iceberg catalog. These are recommended choices,
not services mandated by the assignment.

A log message claiming that a write succeeded is not sufficient; the
application must perform and verify the real Iceberg operation.
Stage 6 --- Revenue-prediction model
The complete assignment requires training a machine-learning model to
predict annual company revenue using the harmonized data.

The implementation must define: - The target revenue field and its
units. - Which features are available for training. - How missing or
invalid values are handled. - A suitable training and evaluation
approach. - Appropriate evaluation metrics. - Where the trained model
artifact is stored.

Ray Train should be addressed as required by the assignment, including
how the environment could support distributed training. Whether the
exercise's actual model training needs multiple workers should be
determined by the dataset size and selected model.

The provided Python skeleton contains only a placeholder for model
training. Actual training and evaluation must be implemented.
Stage 7 --- Completion status and evidence
The workflow must report whether execution succeeded or failed. A
successful submission of a Kubernetes resource or a successful container
build must not be treated as proof that the data pipeline completed
successfully.

Evidence should include, as applicable: - Job status and execution
logs. - Input and processed record counts. - Entity-resolution outcomes
and ambiguous-match counts. - Confirmation that the Iceberg table was
updated. - Model-training and evaluation results. - The location of the
saved model artifact.
5. Platform Requirements
5.1 Cloud and Kubernetes
- Use a managed Kubernetes cluster. This baseline selects Amazon EKS.
- Provision the environment using Terraform.
- Organize Terraform into modular, decoupled state layers.
- Use appropriate network isolation and access controls.
- Plan for resilient worker capacity across Availability Zones where
  practical.
5.2 Ray and KubeRay
- Install the KubeRay Operator to manage Ray resources in Kubernetes.
- Configure a Ray Head group and a separate Ray Worker group.
- Support CPU-bound data-processing tasks.
- Document the configuration needed for Ray Data and Ray Train,
  including relevant shared-memory and object-store considerations.
- Configure resource scheduling so that the EntityResolver actor
  runs on the intended worker group, using suitable labels,
  taints/tolerations, placement rules, or Ray custom resources.
- Ensure the application connects to the intended Ray cluster and uses
  compatible Ray and application dependencies.
5.3 Worker scaling and Spot instances
- Provide an autoscaling strategy for Ray workers and the underlying
  Kubernetes nodes.
- Evaluate Spot instances for worker capacity to reduce costs.
- Keep essential system/head capacity on a suitable stable capacity
  strategy.
- Account for Spot interruptions, retries, workload recovery, and safe
  repeated execution.
- Explain the Spot strategy and its trade-offs in the README.
Karpenter is a possible AWS node-provisioning choice, but the assignment
does not mandate it.
5.4 Storage and cloud integration
- Store input datasets and durable outputs in cloud object storage.
- Configure an Apache Iceberg catalog and storage location.
- Provide the required permissions for the Ray workload to read inputs
  and write the Iceberg table.
- Store model artifacts durably where required.
- Avoid relying on Ray's in-memory object store as permanent storage.
5.5 Identity and secrets
- Apply least-privilege access for deployment automation and
  application workloads.
- Use workload identity for access to AWS services, such as IRSA or
  EKS Pod Identity.
- Do not embed long-lived AWS credentials in source code or container
  images.
- Provide the LLM API key securely if the real resolver requires an
  external LLM.
- Restrict access to secrets and avoid logging secret values.
5.6 CI/CD
Implement a GitHub Actions or GitLab CI/CD workflow that:
1. Runs terraform plan for pull requests.
2. Validates and tests the application and infrastructure changes as
   appropriate.
3. Builds a container image containing the pipeline and its
   dependencies after an approved merge.
4. Pushes the image to a container registry.
5. Submits a RayJob custom resource to the Kubernetes cluster.
6. Checks the final job status and exposes failures to the workflow or
   operator.
For AWS, Amazon ECR and GitHub Actions OIDC are recommended
implementation choices.
5.7 Observability
- Configure Prometheus scraping for Ray cluster, node, and task-level
  metrics.
- Provide a secure way to access the Ray Dashboard, such as
  port-forwarding or an authenticated access path.
- Aggregate stdout/stderr and relevant logs from Ray Head and Worker
  pods.
- Monitor Kubernetes and node health, resource utilization, job
  failures, and pipeline execution.
- Make job outcomes and failure details available for troubleshooting.
Prometheus and Grafana are proposed monitoring components. Centralized
logging may use CloudWatch Logs or another suitable logging system.
6. Data and Identity Principles
The following principles should guide the data model and processing
logic:
- Canonical identity: Each resolved company should have a stable
  identifier that does not depend on a process-randomized hash.
- Evidence-based matching: Matching decisions should use available
  company attributes and identifiers, not name similarity alone.
- Ambiguity handling: Uncertain matches should be flagged or held
  for further processing instead of being merged automatically.
- Provenance: Preserve source identifiers and source information
  where practical so that registry records can be traced to their
  inputs.
- Repeatability: Reprocessing the same input should not create
  duplicate companies or corrupt the registry.
- Transactional updates: Registry updates should use the
  capabilities of Iceberg and the selected write approach.
- Validation: Verify actual table changes and model outputs rather
  than relying only on log messages.
The exact schema, matching thresholds, conflict-resolution rules, and
canonical-ID strategy must be finalized during application design.
7. Proposed Logical Architecture
1. Input storage: CSV files arrive in a defined input location,
   proposed as Amazon S3.
2. Trigger/orchestration: A selected event or orchestration
   mechanism initiates the job.
3. CI/CD and image registry: The application image is built,
   versioned, and stored in Amazon ECR.
4. Amazon EKS: Provides the Kubernetes execution environment.
5. KubeRay Operator: Manages Ray cluster and job resources.
6. Ray Head and Workers: Coordinate and execute the distributed
   Python pipeline.
7. Entity resolver: Performs company matching and harmonization.
8. Iceberg catalog and S3 warehouse: Maintain the durable
   corporate_registry table.
9. Model-training workflow: Trains and evaluates the
   revenue-prediction model and saves its artifact.
10. Observability: Collects metrics, logs, job status, and execution
    evidence.
This is a logical architecture. The exact trigger service, Terraform
module boundaries, network topology, node-provisioning mechanism, and
Iceberg catalog configuration remain implementation decisions.
8. Non-Functional Requirements
Reliability
- Detect and report failed jobs.
- Handle worker interruptions and transient failures appropriately.
- Make repeated processing safe where practical.
- Avoid reporting success before data and model outputs have been
  verified.
Security
- Use least-privilege identities.
- Keep worker and data access appropriately restricted.
- Protect secrets and sensitive data.
- Restrict access to operational dashboards.
Scalability
- Support distributed execution through Ray.
- Separate Ray Head/system capacity from worker capacity.
- Allow worker and node capacity to scale according to workload
  demand.
- Avoid collecting large datasets into a single process unnecessarily
  when a distributed data-processing approach is appropriate.
Maintainability
- Use modular Terraform and versioned application images.
- Keep infrastructure, platform configuration, and application logic
  clearly organized.
- Document setup, execution, troubleshooting, and operational
  assumptions.
Cost awareness
- Evaluate Spot instances for interruptible worker workloads.
- Scale down unnecessary worker capacity.
- Select compute and monitoring resources appropriate to the
  demonstrated workload.
- Document cost and reliability trade-offs.
9. Deliverables
The submission should include:
1. A working end-to-end solution.
2. A Git repository containing application code, Terraform modules, and
   Kubernetes manifests.
3. Two CSV datasets with at least 1,000 records each.
4. A working Ray execution environment managed through KubeRay.
5. A functioning entity-resolution workflow.
6. A real transactional update to the Iceberg corporate_registry
   table.
7. A working revenue-prediction training and evaluation workflow.
8. CI/CD automation that builds the image and triggers a RayJob.
9. Monitoring, logging, and secure dashboard access.
10. A README with setup instructions, architecture diagram,
    Spot-instance strategy, and a serverless alternative.
10. Serverless Alternative
The README must describe a serverless alternative to running the
workload on a continuously managed Kubernetes cluster.

The selected alternative should be evaluated against the actual
requirements for distributed Python execution, job duration,
dependencies, data access, model training, operational effort, and cost.
It should not be presented as equivalent without validating those
requirements.

A suitable alternative can be proposed during the architecture
comparison phase.
11. Open Decisions Before Implementation
The following details are not fully specified by the assignment and must
be decided before implementation:
1. Input trigger: Which service detects new CSV files and starts
   processing?
2. Input contract: What are the schemas, required columns, and
   validation rules for each source?
3. Entity resolution: Which attributes and matching method
   determine whether records refer to the same company?
4. Ambiguous matches: Should uncertain records be quarantined,
   reviewed, or processed using a defined confidence threshold?
5. Registry schema: Which source attributes are retained, and how
   are conflicting values reconciled?
6. Idempotency: How is a file or batch uniquely identified so that
   duplicate notifications or reruns do not create unintended
   duplicates?
7. Iceberg catalog: Confirm AWS Glue Data Catalog or another
   compatible catalog.
8. Training design: Define the revenue target, features, evaluation
   metrics, and artifact location.
9. Scheduling: Determine whether the job runs only on new file
   arrival, on a schedule, or through both mechanisms.
10. Capacity and cost: Select initial resource sizes, scaling
    limits, and Spot/On-Demand policy based on the demonstration and
    reliability goals.
11. Access path: Define how CI/CD reaches the EKS API and how
    operators access the Ray Dashboard.
12. Failure and recovery: Define retry limits, alerting, and
    recovery behavior for partial failures and interrupted workers.
12. Source Requirements vs. Design Recommendations
Explicitly required by the assignment
- A managed Kubernetes cluster using EKS, GKE, or AKS.
- Cloud object storage.
- KubeRay Operator.
- Separate Ray Head/system and autoscaling Worker node pools.
- A Spot/Preemptible worker cost strategy.
- Ray Data and Ray Train configuration guidance.
- Scheduling the EntityResolver actor onto the intended worker
  group.
- Workload identity and secure cloud-resource access.
- An Apache Iceberg catalog.
- CI/CD with Terraform planning, container build, and RayJob
  submission.
- Prometheus metrics, secure Ray Dashboard access, and centralized
  logs.
- Two CSV datasets containing at least 1,000 records each.
- Entity resolution, an Iceberg registry update, and annual revenue
  prediction.
- A README, architecture diagram, Spot strategy, and serverless
  alternative.
Recommended design choices that require confirmation
- Amazon S3 as the storage service and AWS Glue Data Catalog as the
  Iceberg catalog.
- S3 event-driven triggering for new input files.
- Amazon ECR for container images.
- GitHub Actions OIDC for AWS authentication.
- Karpenter for node provisioning.
- Prometheus and Grafana for monitoring, with CloudWatch Logs as a
  possible logging backend.
- The specific company-matching algorithm, canonical-ID strategy,
  retry policy, and registry conflict-resolution rules.
These recommendations are not additional requirements stated by the
assignment. They are proposed choices to be evaluated and finalized
before implementation.
13. Acceptance Principle
The platform is considered successful only when an input batch can be
processed through the intended workflow and the resulting outcomes can
be verified: the records were ingested and validated, company identities
were resolved according to defined rules, the Iceberg registry was
updated transactionally, the revenue-prediction model was trained and
evaluated, and the execution status and logs are available.

Infrastructure deployment alone is not sufficient evidence of
completion.