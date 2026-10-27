Prerequisites --- Ray AI Platform on Kubernetes
Status: Preparation checklist
Cloud: AWS
Target platform: Amazon EKS + KubeRay + Ray
Related documents: architecture.md, IMPLEMENTATION.md
Purpose: Identify the accounts, tools, permissions, configuration,
and decisions required before implementing the platform.
This document lists prerequisites and preparation steps. It does not
mean that AWS resources have been created, credentials have been
configured, or any deployment has been verified.

1. Scope and preparation principles
The solution is intended to run a distributed CSV processing pipeline on
Ray over Kubernetes. It will inspect incoming CSV files, resolve company
entities, update an Apache Iceberg table transactionally, and train a
small annual-revenue regression model when the incoming data contains an
explicitly identified and usable target.

The actual datasets have not been provided. Therefore, these
prerequisites do not require a fixed CSV schema, fixed row count,
fixed column count, or specific column names. The pipeline must inspect
the data and use an explicit or validated mapping for business meaning.

Prepare the prerequisites in this order:
1. Confirm access to the AWS account and the repository.
2. Install and verify local tools.
3. Establish secure identity and permissions.
4. Decide the initial region, naming, and environment configuration.
5. Prepare Terraform state and deployment workflow requirements.
6. Prepare the application/runtime configuration contract.
7. Confirm cost controls and cleanup ownership.
8. Begin implementation only after the blocking prerequisites are
   satisfied.
Do not create every cloud resource manually before Terraform is ready.
Manual setup should be limited to the bootstrap tasks that are
explicitly documented.
2. Required accounts and access
2.1 AWS account
You need an AWS account where the project resources can be created.

Before starting, confirm:
- The AWS account ID and the account owner/administrator.
- Which AWS region will host the initial development environment.
- Whether the account is a personal sandbox, a dedicated assignment
  account, or a shared organization account.
- Whether service control policies, permission boundaries, or
  organizational policies restrict EKS, EC2, IAM, S3, ECR, DynamoDB,
  Glue, CloudWatch, or EventBridge.
- Whether budget alerts and billing visibility are enabled.
- Whether there are existing resources or naming conventions that must
  be respected.
Use a dedicated development environment or account if possible. Do not
deploy experimental EKS resources into a production account without
approval.

The region is a configuration decision; do not hard-code it into the
application. Confirm regional availability and quota support for EKS,
the intended EC2 instance families, Spot capacity, and any selected
managed services.
2.2 Source repository
You need a Git repository with permission to create branches, pull
requests, and the CI workflow.

For GitHub Actions, confirm:
- Repository owner and repository name.
- Deployment branch name.
- Whether GitHub Actions is enabled.
- Whether repository or organization policy permits OIDC federation to
  AWS.
- Whether environment protection/approval rules are available and
  required.
- Whether workflow permissions can be restricted to the minimum
  needed.
- Whether pull requests can originate from forks, which affects secret
  exposure and deployment permissions.
Do not store AWS access keys, secret tokens, Terraform state, plan
files, or application secrets in Git.
2.3 Container registry
The proposed design uses Amazon ECR. The repository should be created by
Terraform or an explicitly documented bootstrap step. The build identity
needs permission to push images; the EKS worker identity needs
permission to pull the image.

Use immutable image tags based on a commit SHA or another unique build
identifier. Avoid relying only on a mutable latest tag for the
deployed RayJob.
3. Local software prerequisites
Install the tools on the machine or development environment from which
you will build, validate, and deploy the project. Use official
installation instructions for the operating system in use. Pin the
versions used by the project once the compatible toolchain is selected.
  Tool                    Required for            Verification
  Git                     Version control and     git --version
                          branches                

  AWS CLI v2              AWS identity checks and aws --version
                          cluster access setup    

  Terraform CLI           Infrastructure          terraform version
                          provisioning and state
                          management              

  kubectl               Kubernetes inspection   kubectl version --client
                          and RayJob submission   

  Helm                    Installing the KubeRay  helm version
                          Operator chart          

  Docker or compatible    Building the Ray        docker --version when
  image builder           pipeline image          using Docker

  Python                  Pipeline development    python --version or
                          and local validation    python3 --version

  pip or project        Installing application  python -m pip --version
  package manager         dependencies            

  Text editor/IDE         Editing Python, YAML,   Open the repository
                          and Terraform           successfully

  Browser access          AWS Console, GitHub,    Confirm sign-in and access
                          documentation, and
                      monitoring              
Some environments use Podman, BuildKit, or another OCI-compatible
builder instead of Docker. Use one supported image-building method and
document it; do not require multiple builders without a reason.
3.1 Version policy
Do not choose versions independently for Terraform, the AWS provider,
the EKS module, Kubernetes, KubeRay, Ray, Python, PyIceberg, or the
training framework.

Before implementation:
1. Select a compatible Kubernetes/EKS version supported by the selected
   KubeRay release.
2. Select a KubeRay Operator version compatible with that
   Kubernetes/Ray version.
3. Pin the Ray image and Python runtime.
4. Pin PyIceberg and the Glue catalog integration dependencies.
5. Pin the chosen Ray Train integration and ML library.
6. Pin Terraform provider and module versions.
7. Record all selected versions in the repository and verify them in
   CI.
Use version constraints and a committed lock file where supported. Do
not write "latest" as a version policy for a reproducible assignment.
3.2 Optional local tools
These may help, but they are not blockers for the initial cloud
implementation:
- jq for inspecting JSON output.
- yq for inspecting YAML.
- make for repeatable developer commands.
- A Python virtual environment tool.
- A Kubernetes manifest linter.
- A Terraform linter/security scanner.
- An image vulnerability scanner.
- A diagram viewer for Mermaid.
- aws-vault or another approved local credential helper, if
  permitted by the environment.
Use optional tools only if they reduce friction and are documented. Do
not make the project dependent on a large local toolchain unnecessarily.
4. AWS identity and permission prerequisites
4.1 Human/developer identity
Use an approved IAM Identity Center/SSO role or another
organization-approved short-lived credential mechanism where available.
Avoid using the AWS account root user for routine work.

The developer/deployment identity must have enough permission to perform
the tasks for the relevant environment, including the ability to:
- Read account/region identity and relevant service quotas.
- Create and manage the resources in the Terraform plan.
- Manage or pass only the intended IAM roles.
- Provision EKS and its supporting resources.
- Read EKS cluster metadata and configure Kubernetes access.
- Push application images to the intended ECR repository.
- Review deployment logs and resource state.
- Run Terraform state operations against the dedicated backend.
The exact IAM policy depends on the final Terraform resources and the
organization's governance model. Do not grant AdministratorAccess as
the default solution merely to avoid understanding permissions. If an
administrator must perform the initial bootstrap, separate that one-time
action from the ongoing deployment role and document the handoff.

Verify the identity before provisioning:
aws sts get-caller-identity
aws configure list
The output should identify the intended account and credential source.
Do not paste credential values into documentation or chat.
4.2 Separate identities by responsibility
The architecture should not use one all-powerful role for every
component. Prepare distinct roles or equivalent scoped identities for:
1. Terraform/deployment role: provisions infrastructure and
   performs approved deployments.
2. GitHub Actions role: assumes access through OIDC for approved
   workflows.
3. Ray workload role: reads claimed input files, accesses the
   configured Iceberg catalog/warehouse, and writes model artifacts.
4. Discovery/submission role: lists eligible input objects,
   claims/updates ledger items, and creates or inspects the relevant
   RayJob resources.
5. Kubernetes operator/admin identity: administers the cluster when
   necessary, separately from application runtime.
Not every identity must be created before the first Terraform file is
written, but the trust boundaries and permissions must be designed
before deployment.
4.3 Workload identity
The Ray pods must use EKS Pod Identity or IAM Roles for Service Accounts
(IRSA), selected and documented during implementation.

Prerequisites:
- EKS has the required identity integration configured.
- The intended Kubernetes service account is associated with the
  correct cloud role.
- The role trust policy is restricted to the intended cluster/service
  account or identity association.
- The Ray workload image does not contain static AWS credentials.
- The workload can access only the required S3 prefixes, Glue
  catalog/table operations, and model-output destination.
- KMS permissions are added only if a customer-managed key is used and
  the workload requires it.
A successful test from the developer laptop does not prove that the pod
identity works. Verify identity from a pod using the actual service
account.
4.4 GitHub OIDC
If using GitHub Actions, prepare OIDC federation rather than storing
long-lived AWS keys as repository secrets.

Confirm:
- The AWS OIDC provider is configured according to AWS/GitHub
  guidance.
- The trust policy restricts the allowed repository and
  branch/environment subject.
- The workflow has only the required token permissions.
- Pull-request workflows cannot assume the deployment role from
  untrusted code.
- Production applies or other sensitive operations require the
  intended approval gate.
Use the actual repository/branch/environment identifiers in the trust
policy; do not copy placeholder values into a live role.
5. AWS service readiness
The initial design expects these services. Confirm availability and
policy constraints before implementation.
  Service                 Why it is needed        Prerequisite to verify
  Amazon VPC              Network isolation for   CIDR ranges and subnet
                          EKS and workloads       design approved

  Amazon EKS              Managed Kubernetes      EKS quota, supported
                          control plane           Kubernetes version,
                                                  cluster access policy

  Amazon EC2              Kubernetes nodes        Instance-family
                                                  availability, On-Demand
                                                  quota, Spot
                                                  quota/capacity

  Amazon S3               CSV input, Iceberg      Bucket naming,
                          warehouse, model        encryption, public
                          artifacts, Terraform    access blocking,
                          state                   lifecycle/retention

  Amazon ECR              Pipeline container      Repository access and
                          images                  image retention policy

  Amazon DynamoDB         File processing ledger  Table naming, access
                                                  permissions,
                                                  backup/recovery
                                                  expectations

  AWS Glue Data Catalog   Proposed Iceberg        Catalog permissions and
                          catalog                 selected Iceberg
                                                  integration
                                                  compatibility

  Amazon CloudWatch       Logs and selected AWS   Log retention and cost
                          operational signals     policy

  Amazon EventBridge      Scheduled input         Scheduler permissions
  Scheduler               discovery               and chosen
                                                  schedule/time zone

  AWS Lambda              Lightweight scheduled   Runtime support, IAM
                          discovery and RayJob    role, timeout and
                          submission              memory expectations

  IAM                     Deployment and workload Role trust, least
                          permissions             privilege, permission
                                                  boundaries

  KMS, if applicable      Customer-managed        Key policy and required
                      encryption keys         service/workload access
This list reflects the proposed architecture. If the implementation
changes a service choice, update this document and architecture.md
rather than silently introducing a second architecture.
5.1 Quotas and capacity
Before creating EKS, check relevant service quotas and capacity
constraints, including:
- EKS clusters per region/account.
- EC2 On-Demand vCPU quota for the selected instance families.
- EC2 Spot vCPU quota and regional/AZ availability.
- ENI/IP address capacity for the VPC/subnets and expected pod
  density.
- EBS volume limits if worker nodes use EBS.
- ECR and CloudWatch limits relevant to the workload.
- Lambda concurrency/timeout constraints if the discovery component
  needs them.
A Spot quota does not guarantee that Spot capacity will be available.
Use multiple compatible instance types where feasible and define a
fallback/reduced-capacity behavior. Keep essential Ray Head/system
capacity on stable On-Demand capacity as specified in the architecture.
6. Network and access prerequisites
Before applying Terraform, agree on the network boundaries.
- Choose a VPC CIDR that does not overlap with connected networks.
- Choose private subnet CIDRs across multiple Availability Zones.
- Decide how private worker nodes reach required AWS services and
  image registries.
- Determine whether NAT gateways, VPC endpoints, or a combination are
  appropriate.
- Decide how operators reach the EKS API endpoint.
- Decide how the Ray Dashboard is accessed securely.
- Decide whether CI runners are hosted by GitHub or inside a private
  network.
Do not assume that private subnets automatically have the outbound
access needed for image pulls, Python package downloads, or external
APIs. Confirm the actual route and endpoint design.

For cost control, evaluate VPC endpoints versus NAT gateways based on
expected data volume and service access. Do not add an endpoint for
every service by default; also do not remove NAT or other egress without
checking the required traffic paths.

The Ray Dashboard must not be exposed publicly without appropriate
authentication and network restrictions. A private endpoint,
authenticated port-forward, or another approved access path should be
documented.
7. Terraform prerequisites
7.1 Remote state backend
Prepare a dedicated Terraform state backend. The bootstrap layer may
initially use local state to create the backend, after which state
should be migrated according to the documented procedure.

The backend should have:
- Restricted access.
- Encryption at rest.
- Versioning or an equivalent recovery strategy.
- A documented locking/concurrency strategy supported by the selected
  Terraform backend/version.
- Separate state keys for the layers and environments.
- No public access.
- A recovery procedure for accidental state changes.
Do not put Terraform state into the application input bucket/prefix.
State may contain sensitive infrastructure metadata and should be
treated as confidential.
7.2 State layer plan
The proposed state layers are:
1. bootstrap --- remote state resources.
2. foundation --- networking, storage, ledger, registry, shared IAM.
3. eks-platform --- EKS, node capacity, cluster access, identity
   integration.
4. ray-platform --- KubeRay, Ray resources, monitoring integration.
Confirm where each shared resource belongs and how outputs flow between
layers. Do not have multiple states manage the same Terraform resource.
7.3 Terraform workflow
Ensure the team can run and review:
terraform fmt -check
terraform init
terraform validate
terraform plan
Run these commands in the correct layer directory. terraform plan must
be reviewed before apply. A pull request should produce a reviewable
plan; applying changes should follow the intended approval process.
7.4 Naming and tags
Choose a consistent naming convention before creating resources. At
minimum, define:
- Project identifier.
- Environment (standardized as 'test').
- Region.
- Resource role/purpose.
- Required ownership and cost tags.
Check AWS naming constraints and global uniqueness requirements for S3
bucket names. Do not commit real account IDs or environment-specific
secrets into generic examples.
8. Application and data prerequisites
8.1 Data format assumptions
The initial pipeline accepts CSV files. The actual files are not yet
available, so do not assume:
- A fixed number of rows or columns.
- Fixed column names.
- A fixed column order.
- Every field is populated.
- All numeric-looking values are numeric.
- Every source contains a company identifier.
- Every source contains annual revenue.
- Similar company names always refer to the same legal entity.
CSV files may contain different headers, types, delimiters, encodings,
null representations, malformed rows, or very different sizes. The
application must inspect and report these conditions.

If the assignment later supplies files that differ from the initial CSV
assumptions, revisit the input contract before coding a parser. Do not
silently expand supported formats without a decision.
8.2 Canonical field mapping
The pipeline needs a small internal representation for the business
concepts required by entity resolution and training. Source fields must
be mapped to these concepts through explicit configuration or a
defensible validated rule.

Prepare a way to version and store mappings. A mapping should identify:
- Source identity or source schema/version.
- Original column name.
- Canonical field.
- Conversion/normalization rule, if any.
- Required/optional status.
- Validation rule.
- Mapping version and approval/source.
The canonical concepts may include a company-name candidate, stable
company identifiers when available, supporting attributes, and annual
revenue when the source actually provides a valid target. These are
concepts, not mandatory source column names.

Unknown columns should be retained in source provenance or a flexible
payload according to the chosen data model. Ambiguous business fields
should not be mapped silently.
8.3 Revenue training readiness
Ray Train is required by the assignment, but successful training depends
on the data.

Before a model-training run, confirm:
- A valid annual-revenue target has been identified and mapped.
- The target's currency, time period, units, and meaning are
  understood.
- The available features are appropriate and do not leak the target.
- There are enough usable examples for the selected split and training
  method.
- Missing values and categorical values have a documented handling
  strategy.
- Training/validation metrics and model artifacts will be recorded.
If no valid target is present, the pipeline must report that model
training was skipped or failed according to the run policy. It must not
fabricate revenue labels to make training appear successful. Synthetic
data may be used later to validate the mechanics, but results from
synthetic data must not be represented as real predictive performance.
8.4 Entity resolution readiness
Prepare the matching strategy before implementing the actor:
- Prefer trusted stable identifiers when present.
- Normalize text conservatively.
- Use supporting attributes only when their meaning is mapped.
- Treat fuzzy matching as candidate generation or a thresholded
  decision, not proof of identity.
- Record the evidence and confidence for a match.
- Keep ambiguous matches unresolved or route them for review.
- Use deterministic, persistent canonical IDs; do not use Python's
  built-in hash() as a durable ID.
File-level duplicate prevention and company-level entity resolution are
separate controls and both are required.
8.5 Iceberg readiness
Confirm the intended Glue catalog, database/namespace, table name,
warehouse location, partitioning decision (if any), and merge/upsert
strategy.

The chosen implementation must support the catalog and transactional
operation actually used. Pin and verify the compatible PyIceberg/Iceberg
dependencies. The ledger and Iceberg table are separate systems, so
design for retries and uncertain acknowledgements rather than assuming
one atomic transaction spans both.
9. Ray and Kubernetes runtime prerequisites
Before deploying the pipeline, prepare:
- A dedicated namespace for Ray workloads.
- A KubeRay Operator version compatible with the selected
  Kubernetes/Ray versions.
- A Ray Head group on stable capacity.
- A worker group that can scale and use the chosen Spot strategy.
- CPU and memory requests/limits appropriate for the workload.
- /dev/shm and Ray object-store settings appropriate to the pod
  memory limit.
- A service account with the intended workload identity.
- Labels, node selectors, taints/tolerations, and Ray custom resources
  for EntityResolver placement.
- A secure Dashboard access method.
- Log and metric collection.
- A policy for RayJob names, run IDs, input manifests, retries, and
  terminal status.
Kubernetes scheduling and Ray scheduling are distinct. Kubernetes node
selectors and tolerations choose where worker pods can run; Ray custom
resources guide placement of the actor within the Ray cluster. Both
layers must be configured and runtime placement verified.

The Ray Head should not be treated as a durable data store. Durable
processing state belongs in S3, DynamoDB, and Iceberg.
10. CI/CD prerequisites
For GitHub Actions:
- A repository with Actions enabled.
- A defined deployment branch.
- An AWS OIDC trust configuration restricted to the intended
  repository/branch/environment.
- Workflow token permissions limited to what the workflow needs.
- A role that can push to the intended ECR repository.
- A role that can submit and inspect the intended RayJob resources.
- Terraform validation and plan steps for pull requests.
- An approved process for applying infrastructure changes.
- An immutable image-tagging convention.
- A mechanism to check the actual RayJob terminal status after
  submission.
CI should not report success merely because the RayJob resource was
created. It should wait for or otherwise reliably report the actual job
result. Avoid exposing AWS credentials or secrets to untrusted
pull-request code.

If the scheduled discovery component also submits RayJobs, keep its
permissions separate from the GitHub deployment identity.
11. Observability prerequisites
Choose the minimum viable observability stack before deploying
workloads.

Required by the proposed design:
- Prometheus metrics for Ray and relevant Kubernetes/node behavior.
- Centralized Head and Worker logs.
- Secure access to the Ray Dashboard.
- A way to find logs and metrics by run ID/job name.
- Visibility into RayJob status, worker scaling, retries, and
  failures.
- Visibility into stale ledger records that remain in PROCESSING.
- Log retention and monitoring cost settings.
Grafana may be used to visualize Prometheus metrics. The exact
monitoring installation and versions should be pinned during
implementation. Do not deploy a second overlapping monitoring stack
without a specific requirement.
12. Cost, budget, and cleanup prerequisites
EKS and associated infrastructure can incur charges even when no
pipeline is actively running. Before provisioning, establish a budget
and a cleanup owner.

Review likely cost areas:
- EKS cluster/control-plane charges.
- EC2 On-Demand and Spot worker capacity.
- EBS volumes and snapshots.
- NAT gateways and data transfer.
- VPC endpoints.
- S3 storage, requests, and data transfer.
- ECR image storage.
- DynamoDB usage and backup features.
- CloudWatch logs and metrics.
- Prometheus/Grafana hosting or managed service charges.
- Lambda and EventBridge usage.
Required preparation:
1. Define an initial monthly or exercise budget.
2. Set billing alerts or an AWS Budget appropriate to the account.
3. Keep worker minimum/desired capacity as low as the implementation
   allows for a smoke-test environment.
4. Set log retention and image lifecycle policies.
5. Define which resources can be destroyed after the walkthrough.
6. Document how state and any required evidence/artifacts will be
   preserved.
7. Review actual costs after the first deployment.
Spot can reduce compute costs but is not a guarantee of capacity or
savings for every workload. Do not assume the overall environment is
inexpensive solely because workers use Spot.
13. Security preparation checklist
Before a live deployment, confirm:
- [ ] Root account is not used for routine deployment.
- [ ] Developer and CI identities use approved short-lived credentials
  where possible.
- [ ] IAM roles are separated by responsibility.
- [ ] Workload identity is configured; no static AWS keys are baked
  into images.
- [ ] S3 buckets block public access and enforce the selected
  encryption policy.
- [ ] Terraform state access is restricted.
- [ ] EKS API and Dashboard access are appropriately restricted.
- [ ] Ray pods use least-privilege service accounts and RBAC.
- [ ] Secrets are kept out of Git, container layers, logs, and command
  history.
- [ ] Container images use immutable tags and are scanned if the
  chosen tooling supports it.
- [ ] CI pull-request permissions cannot trigger privileged
  deployments from untrusted code.
- [ ] Logs avoid secrets and unnecessary sensitive raw data.
- [ ] Resource cleanup and access revocation are documented.
14. Readiness checklist
Mark an item complete only after verifying it.
Accounts and access
- [ ] AWS account and region are confirmed.
- [ ] Account policies and service quotas have been reviewed.
- [ ] Git repository and deployment branch are available.
- [ ] AWS developer identity is working and verified.
- [ ] CI/CD identity approach is selected.
- [ ] Budget alerts and cost ownership are defined.
Local tooling
- [ ] Git is installed.
- [ ] AWS CLI is installed and identifies the intended account.
- [ ] Terraform is installed.
- [ ] kubectl is installed.
- [ ] Helm is installed.
- [ ] Docker or another approved image builder is available.
- [ ] Python and the selected package manager are installed.
- [ ] Tool versions will be pinned/documented in the repository.
Infrastructure design
- [ ] Region, VPC CIDR, and subnet strategy are selected.
- [ ] Terraform state backend/locking strategy is documented.
- [ ] State layers and outputs are agreed.
- [ ] EKS access and endpoint strategy are agreed.
- [ ] On-Demand and Spot capacity strategy is agreed.
- [ ] Kubernetes node autoscaling mechanism is selected.
- [ ] Workload identity mechanism is selected.
- [ ] S3, ECR, DynamoDB, and Glue resources are assigned to a state
  layer.
- [ ] Logging/metrics and Dashboard access methods are selected.
Application readiness
- [ ] Unknown CSV schemas are treated as a supported input condition.
- [ ] Schema inspection and mapping behavior are documented.
- [ ] Ambiguous/missing business fields have a defined outcome.
- [ ] Entity resolution strategy and stable ID approach are defined.
- [ ] Iceberg catalog and retry-safe merge strategy are defined.
- [ ] Revenue target requirements and model-skip behavior are defined.
- [ ] Run ID and exact input-manifest contract are defined.
- [ ] Ledger claim, lease, retry, and terminal-state behavior is
  defined.
Deployment and operations
- [ ] CI PR validation/plan behavior is defined.
- [ ] CI merge image build/push behavior is defined.
- [ ] CI submits RayJob and checks actual terminal status.
- [ ] Prometheus and centralized logging approach is selected.
- [ ] Failure recovery expectations are documented.
- [ ] Cleanup procedure and owner are documented.
15. Blocking prerequisites versus items that can wait
Blocking before cloud deployment
- Working AWS identity and correct account/region.
- A reviewed Terraform state strategy.
- A reviewed VPC/EKS and node capacity design.
- Agreed workload identity and least-privilege access model.
- Selected compatible versions for Terraform, Kubernetes, KubeRay,
  Ray, and the data libraries.
- A defined image build/push and RayJob submission path.
- A budget and cleanup plan.
Can be finalized during implementation
- Exact source CSV column names and mapping rules, because source
  files are not yet available.
- Final canonical table schema, after the data contract is reviewed.
- Exact model feature list and training configuration, after target
  availability is confirmed.
- Final Prometheus dashboards and alert thresholds, after baseline
  metrics are observed.
- Automated unit/integration tests, as agreed, after the
  infrastructure and application baseline exists.
- Optional enhancements that are not required for the first working
  pipeline.
The absence of the actual CSV files does not block provisioning the
general platform, but it does block claiming that the schema mapping and
revenue model work against the eventual real dataset