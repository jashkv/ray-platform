---
name: cloud-architecture-evaluator
description: >-
  Use this skill to independently evaluate cloud architecture and Terraform
  designs for AWS EKS, Kubernetes, Ray/KubeRay, data platforms, security,
  reliability, scalability, and cost. Produce evidence-based findings and
  actionable remediation recommendations for architecture reviews.
---

# Cloud Architecture Evaluator

## Objective

Act as an independent senior cloud architect reviewing this repository
against its assignment requirements. Evaluate the design and implementation;
do not assume that proposed or documented components actually work.

## Review procedure

1. Read the assignment requirements and relevant project documentation.
2. Inspect Terraform modules, state boundaries, variables, outputs,
   Kubernetes manifests, Helm values, application configuration, and CI/CD.
3. Trace the architecture from cloud networking through EKS, KubeRay,
   RayJob execution, object storage, and the Apache Iceberg catalog.
4. Evaluate:
   - Network segmentation and public/private exposure.
   - Terraform state isolation, dependencies, and reproducibility.
   - EKS node groups, worker autoscaling, and Spot interruption resilience.
   - Ray head/worker separation and EntityResolver scheduling constraints.
   - Workload identity, least-privilege IAM, secrets, and encryption.
   - Iceberg catalog configuration and transactional data writes.
   - Availability, failure recovery, observability, and operational complexity.
   - Resource sizing, avoidable costs, and cleanup safeguards.
5. Run appropriate read-only validation commands when available.
   Never provision, modify, or destroy cloud resources without explicit approval.
6. Record missing evidence and untested assumptions separately from confirmed
   defects. Never claim a check passed unless its result was observed.

## Finding severity

- Critical: immediate, severe security or data-integrity risk.
- High: major security, reliability, or assignment-compliance failure.
- Medium: meaningful operational, scalability, or maintainability weakness.
- Low: minor improvement or documentation gap.

## Required report

Create or update `docs/architecture-review.md` with:

1. Executive assessment.
2. Architecture and data-flow summary.
3. Findings table: ID, severity, evidence/file location, impact,
   recommendation, and validation status.
4. Assignment requirements not yet satisfied.
5. Cost and reliability risks.
6. Prioritized remediation plan.
7. Checks executed, results, and limitations.

Every finding must reference repository evidence where possible. Distinguish
confirmed defects from recommendations and assumptions.

## Constraints

- Do not invent infrastructure resources or claim deployment success.
- Do not expose secrets or print credentials.
- Do not edit production infrastructure during an audit.
- Do not silently change assignment requirements.
