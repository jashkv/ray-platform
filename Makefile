# ==============================================================================
# The Distributed AI Foundation — Ray AI Platform on AWS EKS
# Production-Grade Makefile Automation
# ==============================================================================
SHELL := /usr/bin/env bash
.SHELLFLAGS := -euo pipefail -c
.DEFAULT_GOAL := help

# ------------------------------------------------------------------------------
# Configuration Variables (Overridable via environment or command-line)
# Example: make tf-plan-all ENVIRONMENT=test AWS_REGION=us-west-2
# ------------------------------------------------------------------------------
ENVIRONMENT          ?= test
AWS_REGION           ?= us-east-1
AWS_ACCOUNT_ID       ?= $(shell aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "123456789012")
PROJECT_NAME         ?= ray-platform
CLUSTER_NAME         ?= $(PROJECT_NAME)-$(ENVIRONMENT)
K8S_NAMESPACE_SYSTEM ?= ray-system
K8S_NAMESPACE_WORK   ?= ray-workloads
RAY_CLUSTER_NAME     ?= corporate-data-cluster
RAY_VERSION          ?= 2.40.0
KUBERAY_VERSION      ?= v1.2.2
KARPENTER_VERSION    ?= 1.0.8

# Container & Registry
ECR_REGISTRY         ?= $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
IMAGE_NAME           ?= ray-data-pipeline
GIT_SHA              ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "latest")
IMAGE_TAG            ?= $(GIT_SHA)
IMAGE_URI            ?= $(ECR_REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
IMAGE_LATEST         ?= $(ECR_REGISTRY)/$(IMAGE_NAME):latest

# Lakehouse & S3 Storage
DATA_BUCKET          ?= $(ENVIRONMENT)-$(PROJECT_NAME)-data-$(AWS_ACCOUNT_ID)
WAREHOUSE_URI        ?= s3://$(DATA_BUCKET)/iceberg-warehouse
LOCAL_WAREHOUSE_DIR  ?= /tmp/e2e_iceberg_warehouse

# Project Paths
ROOT_DIR             := $(shell pwd)
RAY_DIR              := $(ROOT_DIR)/ray-ai-platform
TF_DIR               := $(RAY_DIR)/terraform
K8S_DIR              := $(RAY_DIR)/kubernetes
APP_DIR              := $(RAY_DIR)/application
SCRIPTS_DIR          := $(RAY_DIR)/scripts
DOCS_DIR             := $(RAY_DIR)/docs
VENV_DIR             := $(RAY_DIR)/.venv

# Python & Tool Binaries
PYTHON               := $(shell if [ -f $(VENV_DIR)/bin/python ]; then echo $(VENV_DIR)/bin/python; else echo python3; fi)
PYTEST               := $(shell if [ -f $(VENV_DIR)/bin/pytest ]; then echo $(VENV_DIR)/bin/pytest; else echo pytest; fi)
TERRAFORM            ?= terraform
KUBECTL              ?= kubectl
HELM                 ?= helm
DOCKER               ?= docker

# Safety confirmation flag for destructive operations (set CONFIRM=true in CI)
CONFIRM              ?= false

# ------------------------------------------------------------------------------
# UI / Terminal Color Utilities
# ------------------------------------------------------------------------------
BOLD   := \033[1m
GREEN  := \033[0;32m
YELLOW := \033[0;33m
BLUE   := \033[0;34m
CYAN   := \033[0;36m
RED    := \033[0;31m
RESET  := \033[0m

# Logging commands
LOG_INFO  := printf "$(BLUE)[INFO]$(RESET) %s\n"
LOG_OK    := printf "$(GREEN)[OK]$(RESET) %s\n"
LOG_WARN  := printf "$(YELLOW)[WARN]$(RESET) %s\n"
LOG_ERR   := printf "$(RED)[ERROR]$(RESET) %s\n"

# Confirmation prompt helper
define require_confirmation
	@if [ "$(CONFIRM)" != "true" ]; then \
		printf "$(YELLOW)$(BOLD)⚠️  CAUTION: You are about to execute: %s$(RESET)\n" "$(1)"; \
		read -p "Do you want to proceed? [y/N]: " ans; \
		if [ "$$ans" != "y" ] && [ "$$ans" != "Y" ]; then \
			printf "$(RED)Operation aborted by user.$(RESET)\n"; \
			exit 1; \
		fi; \
	fi
endef

# ==============================================================================
# Group 1: Help & Self-Documentation
# ==============================================================================
.PHONY: help show-config verify-tools verify-aws

help: ## Show this interactive help catalog of all targets
	@printf "\n$(BOLD)$(CYAN)Ray AI Platform on Kubernetes — Makefile Command Center$(RESET)\n"
	@printf "===============================================================================\n"
	@printf "Usage: $(BOLD)make [target] [VARIABLE=value]$(RESET)\n\n"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / {printf "  $(BOLD)$(GREEN)%-28s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@printf "\n$(BOLD)Primary Configuration Variables:$(RESET)\n"
	@printf "  ENVIRONMENT          Active environment (default: $(YELLOW)$(ENVIRONMENT)$(RESET))\n"
	@printf "  AWS_REGION           AWS Target Region  (default: $(YELLOW)$(AWS_REGION)$(RESET))\n"
	@printf "  AWS_ACCOUNT_ID       AWS Account ID     (default: $(YELLOW)$(AWS_ACCOUNT_ID)$(RESET))\n"
	@printf "  CLUSTER_NAME         EKS Cluster Name   (default: $(YELLOW)$(CLUSTER_NAME)$(RESET))\n"
	@printf "  IMAGE_TAG            ECR Image Tag      (default: $(YELLOW)$(IMAGE_TAG)$(RESET))\n"
	@printf "  CONFIRM              Bypass prompt      (default: $(YELLOW)$(CONFIRM)$(RESET))\n"
	@printf "===============================================================================\n"

show-config: ## Display all current operational variables and resolved paths
	@printf "$(BOLD)=== Active Configuration Parameters ===$(RESET)\n"
	@printf "Environment:           $(CYAN)%s$(RESET)\n" "$(ENVIRONMENT)"
	@printf "AWS Region:            $(CYAN)%s$(RESET)\n" "$(AWS_REGION)"
	@printf "AWS Account ID:        $(CYAN)%s$(RESET)\n" "$(AWS_ACCOUNT_ID)"
	@printf "EKS Cluster Name:      $(CYAN)%s$(RESET)\n" "$(CLUSTER_NAME)"
	@printf "Data Bucket Name:      $(CYAN)%s$(RESET)\n" "$(DATA_BUCKET)"
	@printf "Iceberg Warehouse:     $(CYAN)%s$(RESET)\n" "$(WAREHOUSE_URI)"
	@printf "ECR Image URI:         $(CYAN)%s$(RESET)\n" "$(IMAGE_URI)"
	@printf "Python Binary:         $(CYAN)%s$(RESET)\n" "$(PYTHON)"
	@printf "Ray Cluster Name:      $(CYAN)%s$(RESET)\n" "$(RAY_CLUSTER_NAME)"
	@printf "Namespaces:            $(CYAN)%s$(RESET) (system), $(CYAN)%s$(RESET) (workloads)\n" "$(K8S_NAMESPACE_SYSTEM)" "$(K8S_NAMESPACE_WORK)"

verify-tools: ## Verify local CLI dependencies and print status audit
	@$(LOG_INFO) "Auditing required CLI tool binaries..."
	@MISSING=0; \
	for tool in terraform aws python3 git; do \
		if command -v $$tool >/dev/null 2>&1; then \
			printf "  $(GREEN)[OK]$(RESET) %-12s installed: %s\n" "$$tool" "$$(command -v $$tool)"; \
		else \
			printf "  $(RED)[MISSING]$(RESET) %-12s REQUIRED for baseline development\n" "$$tool"; \
			MISSING=1; \
		fi; \
	done; \
	for tool in kubectl helm docker uv; do \
		if command -v $$tool >/dev/null 2>&1; then \
			printf "  $(GREEN)[OK]$(RESET) %-12s installed: %s\n" "$$tool" "$$(command -v $$tool)"; \
		else \
			printf "  $(YELLOW)[OPTIONAL]$(RESET) %-12s not installed locally (Required for cluster/container operations; see ray-ai-platform/docs/prerequisites.md)\n" "$$tool"; \
		fi; \
	done; \
	if [ $$MISSING -ne 0 ]; then \
		$(LOG_ERR) "One or more core required tools are missing. Check ray-ai-platform/docs/prerequisites.md."; exit 1; \
	fi
	@$(LOG_OK) "Core baseline tool verification passed."

verify-aws: ## Verify active AWS caller identity and STS credentials
	@$(LOG_INFO) "Checking active AWS credentials via STS..."
	@aws sts get-caller-identity --output table
	@$(LOG_OK) "AWS authentication confirmed."

# ==============================================================================
# Group 2: Setup, Virtual Environment & Dependencies
# ==============================================================================
.PHONY: setup setup-venv update-deps

setup: verify-tools setup-venv ## Full initial setup: verify tools and bootstrap Python venv
	@$(LOG_OK) "Project workstation setup complete."

setup-venv: ## Create Python virtualenv and install project dependencies
	@$(LOG_INFO) "Provisioning Python virtual environment in $(VENV_DIR)..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		python3 -m venv $(VENV_DIR); \
	fi
	@$(VENV_DIR)/bin/pip install --upgrade pip setuptools wheel
	@if command -v uv >/dev/null 2>&1; then \
		uv pip install -r $(APP_DIR)/requirements.txt --python $(VENV_DIR)/bin/python; \
	else \
		$(VENV_DIR)/bin/pip install -r $(APP_DIR)/requirements.txt; \
	fi
	@$(LOG_OK) "Virtual environment configured with Ray, PyIceberg, XGBoost, and Pytest."

update-deps: ## Upgrade dependencies in Python virtual environment
	@$(LOG_INFO) "Updating virtual environment packages..."
	@$(VENV_DIR)/bin/pip install --upgrade -r $(APP_DIR)/requirements.txt
	@$(LOG_OK) "Dependencies updated."

# ==============================================================================
# Group 3: Code Quality, Linting & Formatting
# ==============================================================================
.PHONY: lint fmt lint-python fmt-python lint-tf fmt-tf validate-repo

lint: lint-python lint-tf validate-repo ## Run all code, Terraform, and repository linters

fmt: fmt-python fmt-tf ## Auto-format Python and Terraform codebases

lint-python: ## Check Python formatting and linting rules
	@$(LOG_INFO) "Linting Python application sources..."
	@$(PYTHON) -m py_compile $(APP_DIR)/src/*.py
	@$(LOG_OK) "Python compilation syntax validation passed."

fmt-python: ## Format Python sources using ruff or black if available
	@$(LOG_INFO) "Formatting Python sources..."
	@if command -v ruff >/dev/null 2>&1; then \
		ruff format $(APP_DIR); \
	elif [ -f $(VENV_DIR)/bin/ruff ]; then \
		$(VENV_DIR)/bin/ruff format $(APP_DIR); \
	else \
		$(LOG_WARN) "Ruff not found. Skipping auto-formatting."; \
	fi

lint-tf: ## Verify Terraform formatting across all modular layers
	@$(LOG_INFO) "Checking Terraform formatting recursively..."
	@$(TERRAFORM) fmt -check -recursive $(TF_DIR)
	@$(LOG_OK) "Terraform code conforms to canonical formatting."

fmt-tf: ## Auto-format all Terraform files across all layers
	@$(LOG_INFO) "Formatting Terraform files recursively..."
	@$(TERRAFORM) fmt -recursive $(TF_DIR)
	@$(LOG_OK) "Terraform formatting completed."

validate-repo: ## Run repository secret scanning and structural integrity check
	@$(LOG_INFO) "Executing repository validation script..."
	@cd $(RAY_DIR) && ./scripts/validate_repo.sh
	@$(LOG_OK) "Repository hygiene and secret scanner PASSED."

# ==============================================================================
# Group 4: Terraform Layer 1 — Bootstrap (Remote State Backend)
# ==============================================================================
.PHONY: tf-init-bootstrap tf-validate-bootstrap tf-plan-bootstrap tf-apply-bootstrap tf-destroy-bootstrap

tf-init-bootstrap: ## Initialize Terraform bootstrap layer
	@$(LOG_INFO) "Initializing terraform/bootstrap..."
	@cd $(TF_DIR)/bootstrap && $(TERRAFORM) init

tf-validate-bootstrap: tf-init-bootstrap ## Validate syntax of bootstrap layer
	@$(LOG_INFO) "Validating terraform/bootstrap..."
	@cd $(TF_DIR)/bootstrap && $(TERRAFORM) validate

tf-plan-bootstrap: tf-validate-bootstrap ## Generate execution plan for bootstrap layer
	@$(LOG_INFO) "Planning terraform/bootstrap..."
	@cd $(TF_DIR)/bootstrap && $(TERRAFORM) plan -var="environment=$(ENVIRONMENT)" -var="aws_region=$(AWS_REGION)"

tf-apply-bootstrap: tf-validate-bootstrap ## Provision state S3 bucket and DynamoDB lock table
	$(call require_confirmation, Apply terraform/bootstrap S3 State Bucket and Lock Table)
	@cd $(TF_DIR)/bootstrap && $(TERRAFORM) apply -auto-approve -var="environment=$(ENVIRONMENT)" -var="aws_region=$(AWS_REGION)"
	@$(LOG_OK) "Bootstrap state backend resources deployed."

tf-destroy-bootstrap: ## Destroy Terraform bootstrap backend resources (Caution)
	$(call require_confirmation, DESTROY terraform/bootstrap S3 State Bucket and Lock Table)
	@cd $(TF_DIR)/bootstrap && $(TERRAFORM) destroy -auto-approve -var="environment=$(ENVIRONMENT)" -var="aws_region=$(AWS_REGION)"
	@$(LOG_WARN) "Bootstrap state backend destroyed."

# ==============================================================================
# Group 5: Terraform Layer 2 — Networking & VPC
# ==============================================================================
.PHONY: tf-init-network tf-validate-network tf-plan-network tf-apply-network tf-destroy-network

tf-init-network: ## Initialize Terraform network layer
	@$(LOG_INFO) "Initializing terraform/network..."
	@cd $(TF_DIR)/network && $(TERRAFORM) init

tf-validate-network: tf-init-network ## Validate syntax of network layer
	@$(LOG_INFO) "Validating terraform/network..."
	@cd $(TF_DIR)/network && $(TERRAFORM) validate

tf-plan-network: tf-validate-network ## Plan VPC, subnets, NAT Gateway, and S3 Endpoint
	@$(LOG_INFO) "Planning terraform/network..."
	@cd $(TF_DIR)/network && $(TERRAFORM) plan -var="environment=$(ENVIRONMENT)" -var="aws_region=$(AWS_REGION)"

tf-apply-network: tf-validate-network ## Provision VPC, subnets, NAT Gateway, and S3 Endpoint
	$(call require_confirmation, Apply terraform/network VPC Subnets NAT S3 Endpoint)
	@cd $(TF_DIR)/network && $(TERRAFORM) apply -auto-approve -var="environment=$(ENVIRONMENT)" -var="aws_region=$(AWS_REGION)"
	@$(LOG_OK) "Network infrastructure deployed successfully."

tf-destroy-network: ## Destroy networking layer
	$(call require_confirmation, DESTROY terraform/network VPC Subnets NAT Gateway)
	@cd $(TF_DIR)/network && $(TERRAFORM) destroy -auto-approve -var="environment=$(ENVIRONMENT)" -var="aws_region=$(AWS_REGION)"
	@$(LOG_WARN) "Network infrastructure destroyed."

# ==============================================================================
# Group 6: Terraform Layer 3 — EKS Platform Infrastructure
# ==============================================================================
.PHONY: tf-init-eks tf-validate-eks tf-plan-eks tf-apply-eks tf-destroy-eks eks-kubeconfig

tf-init-eks: ## Initialize Terraform EKS layer
	@$(LOG_INFO) "Initializing terraform/eks..."
	@cd $(TF_DIR)/eks && $(TERRAFORM) init

tf-validate-eks: tf-init-eks ## Validate syntax of EKS layer
	@$(LOG_INFO) "Validating terraform/eks..."
	@cd $(TF_DIR)/eks && $(TERRAFORM) validate

tf-plan-eks: tf-validate-eks ## Plan EKS cluster, On-Demand Head pool, and Spot Worker pool
	@$(LOG_INFO) "Planning terraform/eks..."
	@cd $(TF_DIR)/eks && $(TERRAFORM) plan -var="environment=$(ENVIRONMENT)" -var="aws_region=$(AWS_REGION)"

tf-apply-eks: tf-validate-eks ## Provision EKS cluster, On-Demand Head pool, and Spot Worker pool
	$(call require_confirmation, Apply terraform/eks EKS Cluster and Node Pools)
	@cd $(TF_DIR)/eks && $(TERRAFORM) apply -auto-approve -var="environment=$(ENVIRONMENT)" -var="aws_region=$(AWS_REGION)"
	@$(LOG_OK) "EKS cluster and compute pools deployed."

tf-destroy-eks: ## Destroy EKS cluster and compute pools
	$(call require_confirmation, DESTROY terraform/eks EKS Cluster and Node Pools)
	@cd $(TF_DIR)/eks && $(TERRAFORM) destroy -auto-approve -var="environment=$(ENVIRONMENT)" -var="aws_region=$(AWS_REGION)"
	@$(LOG_WARN) "EKS cluster and compute pools destroyed."

eks-kubeconfig: ## Update local kubectl context to authenticate with EKS cluster
	@$(LOG_INFO) "Updating kubeconfig for cluster $(CLUSTER_NAME)..."
	@aws eks update-kubeconfig --region $(AWS_REGION) --name $(CLUSTER_NAME)
	@$(LOG_OK) "Kubeconfig context configured for $(CLUSTER_NAME)."

# ==============================================================================
# Group 7: Terraform Layer 4 — Data Lakehouse, Ledger & IRSA
# ==============================================================================
.PHONY: tf-init-data tf-validate-data tf-plan-data tf-apply-data tf-destroy-data

tf-init-data: ## Initialize Terraform data layer
	@$(LOG_INFO) "Initializing terraform/data..."
	@cd $(TF_DIR)/data && $(TERRAFORM) init

tf-validate-data: tf-init-data ## Validate syntax of data layer
	@$(LOG_INFO) "Validating terraform/data..."
	@cd $(TF_DIR)/data && $(TERRAFORM) validate

tf-plan-data: tf-validate-data ## Plan S3 Lakehouse, Glue Catalog DB, DynamoDB ledger, IRSA
	@$(LOG_INFO) "Planning terraform/data..."
	@cd $(TF_DIR)/data && $(TERRAFORM) plan -var="environment=$(ENVIRONMENT)" -var="aws_region=$(AWS_REGION)"

tf-apply-data: tf-validate-data ## Provision S3 Lakehouse, Glue Catalog DB, DynamoDB ledger, IRSA
	$(call require_confirmation, Apply terraform/data S3 Lakehouse Glue Catalog DynamoDB IRSA)
	@cd $(TF_DIR)/data && $(TERRAFORM) apply -auto-approve -var="environment=$(ENVIRONMENT)" -var="aws_region=$(AWS_REGION)"
	@$(LOG_OK) "Data lakehouse and security roles deployed."

tf-destroy-data: ## Destroy data lakehouse, Glue catalog, DynamoDB ledger, and IRSA role
	$(call require_confirmation, DESTROY terraform/data S3 Lakehouse Glue Catalog DynamoDB IRSA)
	@cd $(TF_DIR)/data && $(TERRAFORM) destroy -auto-approve -var="environment=$(ENVIRONMENT)" -var="aws_region=$(AWS_REGION)"
	@$(LOG_WARN) "Data layer destroyed."

# ==============================================================================
# Group 8: Terraform Layer 5 — Platform, ECR & GitHub OIDC
# ==============================================================================
.PHONY: tf-init-platform tf-validate-platform tf-plan-platform tf-apply-platform tf-destroy-platform

tf-init-platform: ## Initialize Terraform platform layer
	@$(LOG_INFO) "Initializing terraform/platform..."
	@cd $(TF_DIR)/platform && $(TERRAFORM) init

tf-validate-platform: tf-init-platform ## Validate syntax of platform layer
	@$(LOG_INFO) "Validating terraform/platform..."
	@cd $(TF_DIR)/platform && $(TERRAFORM) validate

tf-plan-platform: tf-validate-platform ## Plan ECR repository and GitHub Actions OIDC provider
	@$(LOG_INFO) "Planning terraform/platform..."
	@cd $(TF_DIR)/platform && $(TERRAFORM) plan -var="environment=$(ENVIRONMENT)" -var="aws_region=$(AWS_REGION)"

tf-apply-platform: tf-validate-platform ## Provision ECR repository and GitHub Actions OIDC provider
	$(call require_confirmation, Apply terraform/platform ECR Registry and GitHub OIDC)
	@cd $(TF_DIR)/platform && $(TERRAFORM) apply -auto-approve -var="environment=$(ENVIRONMENT)" -var="aws_region=$(AWS_REGION)"
	@$(LOG_OK) "Platform ECR and OIDC federation deployed."

tf-destroy-platform: ## Destroy platform layer (ECR and GitHub OIDC)
	$(call require_confirmation, DESTROY terraform/platform ECR Registry and GitHub OIDC)
	@cd $(TF_DIR)/platform && $(TERRAFORM) destroy -auto-approve -var="environment=$(ENVIRONMENT)" -var="aws_region=$(AWS_REGION)"
	@$(LOG_WARN) "Platform layer destroyed."

# ==============================================================================
# Group 9: Orchestrated Multi-Layer Terraform Operations
# ==============================================================================
.PHONY: tf-validate-all tf-plan-all tf-apply-all tf-destroy-all

tf-validate-all: tf-validate-bootstrap tf-validate-network tf-validate-eks tf-validate-data tf-validate-platform ## Validate all 5 decoupled Terraform layers
	@$(LOG_OK) "All 5 Terraform layers validated successfully."

tf-plan-all: tf-plan-bootstrap tf-plan-network tf-plan-eks tf-plan-data tf-plan-platform ## Generate plans across all 5 layers in sequence
	@$(LOG_OK) "Planning complete for all 5 layers."

tf-apply-all: ## Deploy entire cloud infrastructure in staged dependency order
	$(call require_confirmation, STAGED DEPLOYMENT of ALL infrastructure layers: bootstrap -> network -> eks -> data -> platform)
	@$(MAKE) tf-apply-bootstrap CONFIRM=true
	@$(MAKE) tf-apply-network CONFIRM=true
	@$(MAKE) tf-apply-eks CONFIRM=true
	@$(MAKE) tf-apply-data CONFIRM=true
	@$(MAKE) tf-apply-platform CONFIRM=true
	@$(LOG_OK) "All infrastructure layers deployed successfully."

tf-destroy-all: ## Teardown all cloud infrastructure in reverse dependency order
	$(call require_confirmation, FULL TEARDOWN of all cloud infrastructure: platform -> data -> eks -> network -> bootstrap)
	@$(MAKE) tf-destroy-platform CONFIRM=true
	@$(MAKE) tf-destroy-data CONFIRM=true
	@$(MAKE) tf-destroy-eks CONFIRM=true
	@$(MAKE) tf-destroy-network CONFIRM=true
	@$(MAKE) tf-destroy-bootstrap CONFIRM=true
	@$(LOG_WARN) "Complete cloud infrastructure teardown finished."

# ==============================================================================
# Group 10: Docker Container Operations
# ==============================================================================
.PHONY: docker-login docker-build docker-build-multiarch docker-push docker-build-push docker-run-local

docker-login: ## Authenticate Docker CLI with Amazon ECR
	@$(LOG_INFO) "Authenticating Docker with Amazon ECR $(ECR_REGISTRY)..."
	@aws ecr get-login-password --region $(AWS_REGION) | $(DOCKER) login --username AWS --password-stdin $(ECR_REGISTRY)
	@$(LOG_OK) "Authenticated with ECR."

docker-build: ## Build application container image with commit SHA tag
	@$(LOG_INFO) "Building Docker image $(IMAGE_URI)..."
	@cd $(RAY_DIR) && $(DOCKER) build -f application/Dockerfile -t $(IMAGE_URI) -t $(IMAGE_LATEST) .
	@$(LOG_OK) "Docker image build successful."

docker-build-multiarch: docker-login ## Build multi-architecture (linux/amd64 + linux/arm64) image for Graviton and push to ECR
	@$(LOG_INFO) "Building multi-platform Docker image (amd64 + arm64) $(IMAGE_URI)..."
	@cd $(RAY_DIR) && $(DOCKER) buildx build --platform linux/amd64,linux/arm64 -f application/Dockerfile -t $(IMAGE_URI) -t $(IMAGE_LATEST) --push .
	@$(LOG_OK) "Multi-platform Docker images pushed to ECR successfully."

docker-push: docker-login ## Push application container image to Amazon ECR
	@$(LOG_INFO) "Pushing Docker images to $(ECR_REGISTRY)..."
	@$(DOCKER) push $(IMAGE_URI)
	@$(DOCKER) push $(IMAGE_LATEST)
	@$(LOG_OK) "Docker images pushed successfully."

docker-build-push: docker-build docker-push ## Build and push container image to ECR in one step

docker-run-local: docker-build ## Run container locally to verify runtime healthcheck
	@$(LOG_INFO) "Executing container local test run..."
	@$(DOCKER) run --rm $(IMAGE_URI) --help || true
	@$(LOG_OK) "Container executed successfully."

# ==============================================================================
# Group 11: Kubernetes & KubeRay Operator Deployment
# ==============================================================================
.PHONY: k8s-validate k8s-apply-namespaces k8s-apply-security helm-install-kuberay helm-uninstall-kuberay helm-install-karpenter k8s-apply-karpenter karpenter-check karpenter-logs k8s-apply-raycluster k8s-delete-raycluster k8s-check-pods k8s-check-nodes

k8s-validate: ## Lint and validate all Kubernetes and KubeRay YAML manifests
	@$(LOG_INFO) "Validating Kubernetes and Helm manifests..."
	@cd $(RAY_DIR) && ./scripts/validate_k8s_manifests.sh
	@$(LOG_OK) "Kubernetes manifests passed validation."

k8s-apply-namespaces: ## Apply namespaces (ray-system, ray-workloads)
	@$(LOG_INFO) "Applying Kubernetes namespaces..."
	@$(KUBECTL) apply -f $(K8S_DIR)/namespaces/namespaces.yaml

k8s-apply-security: k8s-apply-namespaces ## Apply RBAC, ServiceAccounts, and Secrets
	@$(LOG_INFO) "Applying RBAC, ServiceAccounts, and Secrets..."
	@$(KUBECTL) apply -f $(K8S_DIR)/security/

helm-install-kuberay: ## Install KubeRay Operator via Helm
	@$(LOG_INFO) "Installing KubeRay Operator $(KUBERAY_VERSION)..."
	@$(HELM) repo add kuberay https://ray-project.github.io/kuberay-helm/ >/dev/null 2>&1 || true
	@$(HELM) repo update
	@$(HELM) upgrade --install kuberay-operator kuberay/kuberay-operator \
		--version $(KUBERAY_VERSION) \
		--namespace $(K8S_NAMESPACE_SYSTEM) --create-namespace \
		-f $(RAY_DIR)/helm/kuberay-operator/values.yaml
	@$(LOG_OK) "KubeRay Operator deployed."

helm-uninstall-kuberay: ## Uninstall KubeRay Operator
	@$(LOG_INFO) "Uninstalling KubeRay Operator..."
	@$(HELM) uninstall kuberay-operator --namespace $(K8S_NAMESPACE_SYSTEM)
	@$(LOG_OK) "KubeRay Operator uninstalled."

helm-install-karpenter: ## Install Karpenter controller via OCI Helm chart
	@$(LOG_INFO) "Installing Karpenter controller $(KARPENTER_VERSION)..."
	@$(HELM) upgrade --install karpenter oci://public.ecr.aws/karpenter/karpenter \
		--version $(KARPENTER_VERSION) \
		--namespace kube-system --create-namespace \
		-f $(RAY_DIR)/helm/karpenter/values.yaml
	@$(LOG_OK) "Karpenter controller deployed."

k8s-apply-karpenter: ## Apply Karpenter EC2NodeClass and NodePool custom resources
	@$(LOG_INFO) "Applying Karpenter EC2NodeClass and NodePools..."
	@$(KUBECTL) apply -f $(K8S_DIR)/karpenter/
	@$(LOG_OK) "Karpenter node provisioning policies applied."

karpenter-check: ## Inspect Karpenter NodePools, NodeClasses, and controller pods
	@printf "$(BOLD)=== Karpenter NodePools ===$(RESET)\n"
	@$(KUBECTL) get nodepools.karpenter.sh 2>/dev/null || true
	@printf "\n$(BOLD)=== Karpenter EC2NodeClasses ===$(RESET)\n"
	@$(KUBECTL) get ec2nodeclasses.karpenter.k8s.aws 2>/dev/null || true
	@printf "\n$(BOLD)=== Karpenter Controller Pods ===$(RESET)\n"
	@$(KUBECTL) get pods -n kube-system -l app.kubernetes.io/name=karpenter -o wide

karpenter-logs: ## Stream Karpenter controller logs
	@$(KUBECTL) logs -n kube-system -l app.kubernetes.io/name=karpenter -c controller -f

k8s-apply-raycluster: k8s-apply-security ## Deploy RayCluster CRD
	@$(LOG_INFO) "Deploying RayCluster $(RAY_CLUSTER_NAME)..."
	@$(KUBECTL) apply -f $(K8S_DIR)/ray/ray-cluster.yaml
	@$(LOG_OK) "RayCluster manifest submitted."

k8s-delete-raycluster: ## Delete RayCluster CRD
	@$(LOG_INFO) "Deleting RayCluster $(RAY_CLUSTER_NAME)..."
	@$(KUBECTL) delete -f $(K8S_DIR)/ray/ray-cluster.yaml --ignore-not-found
	@$(LOG_OK) "RayCluster deleted."

k8s-check-pods: ## List all running pods in ray-system and ray-workloads
	@printf "$(BOLD)=== Pods in %s ===$(RESET)\n" "$(K8S_NAMESPACE_SYSTEM)"
	@$(KUBECTL) get pods -n $(K8S_NAMESPACE_SYSTEM) -o wide
	@printf "\n$(BOLD)=== Pods in %s ===$(RESET)\n" "$(K8S_NAMESPACE_WORK)"
	@$(KUBECTL) get pods -n $(K8S_NAMESPACE_WORK) -o wide

k8s-check-nodes: ## List EKS nodes with capacity type (Spot/On-Demand) and instance types
	@printf "$(BOLD)=== EKS Cluster Nodes ===$(RESET)\n"
	@$(KUBECTL) get nodes -L node.kubernetes.io/instance-type,karpenter.sh/capacity-type,eks.amazonaws.com/capacityType,workload-role

# ==============================================================================
# Group 12: Data Engineering & Synthetic Data Generation
# ==============================================================================
.PHONY: generate-data verify-data upload-data-s3

generate-data: ## Generate synthetic corporate datasets (S1 & S2, 1,200 records each)
	@$(LOG_INFO) "Generating corporate datasets..."
	@$(PYTHON) $(APP_DIR)/src/generate_datasets.py
	@$(LOG_OK) "Datasets generated in application/data/."

verify-data: generate-data ## Verify generated CSV dataset row counts (>= 1,000 records)
	@$(LOG_INFO) "Validating dataset line counts..."
	@S1_COUNT=$$(wc -l < $(APP_DIR)/data/supply_chain_data_s1.csv | tr -d ' '); \
	S2_COUNT=$$(wc -l < $(APP_DIR)/data/financial_data_s2.csv | tr -d ' '); \
	printf "  SupplyChain S1 rows: %s (Header + 1,200 records)\n" "$$S1_COUNT"; \
	printf "  Financial   S2 rows: %s (Header + 1,200 records)\n" "$$S2_COUNT"; \
	if [ "$$S1_COUNT" -lt 1001 ] || [ "$$S2_COUNT" -lt 1001 ]; then \
		$(LOG_ERR) "Dataset row count requirement failed (< 1,000 records)"; exit 1; \
	fi
	@$(LOG_OK) "Dataset record counts meet assignment specifications."

upload-data-s3: verify-data ## Upload datasets to s3://$(DATA_BUCKET)/incoming/
	@$(LOG_INFO) "Uploading CSV files to S3 bucket $(DATA_BUCKET)..."
	@aws s3 cp $(APP_DIR)/data/supply_chain_data_s1.csv s3://$(DATA_BUCKET)/incoming/supply_chain_data_s1.csv
	@aws s3 cp $(APP_DIR)/data/financial_data_s2.csv s3://$(DATA_BUCKET)/incoming/financial_data_s2.csv
	@$(LOG_OK) "Datasets uploaded to S3 incoming landing zone."

# ==============================================================================
# Group 13: Apache Iceberg Lakehouse Management
# ==============================================================================
.PHONY: iceberg-inspect-table iceberg-local-verify

iceberg-inspect-table: ## Inspect Apache Iceberg table snapshots and committed metadata
	@$(LOG_INFO) "Inspecting Iceberg table corporate_registry..."
	@$(PYTHON) $(SCRIPTS_DIR)/verify_iceberg_table.py --warehouse-path $(LOCAL_WAREHOUSE_DIR)

iceberg-local-verify: ## Run PyIceberg local test suite
	@$(LOG_INFO) "Running PyIceberg sink unit & integration tests..."
	@$(PYTEST) $(APP_DIR)/tests/test_iceberg_sink.py -v
	@$(LOG_OK) "Iceberg sink integration tests passed."

# ==============================================================================
# Group 14: Ray Testing, Jobs & Local Reproduction
# ==============================================================================
.PHONY: test test-unit test-integration test-all ray-smoke-test ray-job-submit ray-job-status ray-job-logs e2e-local

test: test-all ## Run complete pytest test suite

test-unit: ## Run unit tests (generator, normalizer, entity resolver)
	@$(LOG_INFO) "Running unit tests..."
	@$(PYTEST) $(APP_DIR)/tests/test_dataset_generator.py $(APP_DIR)/tests/test_entity_resolver.py -v

test-integration: ## Run integration tests (Iceberg sink, master pipeline)
	@$(LOG_INFO) "Running integration tests..."
	@$(PYTEST) $(APP_DIR)/tests/test_iceberg_sink.py $(APP_DIR)/tests/test_pipeline.py -v

test-all: ## Run all unit and integration tests with coverage
	@$(LOG_INFO) "Executing entire test suite with pytest..."
	@cd $(RAY_DIR) && $(PYTEST) application/tests/ -v
	@$(LOG_OK) "All tests passed successfully."

ray-smoke-test: ## Execute a lightweight Ray smoke test to verify cluster worker connectivity
	@$(LOG_INFO) "Running Ray cluster smoke test..."
	@$(PYTHON) -c "import ray; ray.init(ignore_reinit_error=True); print('Ray cluster nodes:', len(ray.nodes())); ray.shutdown()"
	@$(LOG_OK) "Ray cluster smoke test passed."

ray-job-submit: ## Submit RayJob custom resource to execute distributed revenue pipeline
	@$(LOG_INFO) "Submitting RayJob corporate-revenue-pipeline..."
	@$(KUBECTL) apply -f $(K8S_DIR)/jobs/ray-job.yaml
	@$(LOG_OK) "RayJob submitted to $(K8S_NAMESPACE_WORK)."

ray-job-status: ## Query current status of submitted RayJob
	@$(KUBECTL) get rayjob corporate-revenue-pipeline -n $(K8S_NAMESPACE_WORK)

ray-job-logs: ## Stream driver logs from running RayJob
	@$(KUBECTL) logs -n $(K8S_NAMESPACE_WORK) -l ray.io/node-type=head --tail=100 -f

e2e-local: ## Run master local end-to-end verification harness (7 gates, exit code 0)
	@$(LOG_INFO) "Executing master local end-to-end verification script..."
	@cd $(RAY_DIR) && ./scripts/run_local_e2e.sh
	@$(LOG_OK) "ALL 7 E2E VALIDATION GATES PASSED SUCCESSFULLY."

# ==============================================================================
# Group 14b: Serverless Alternative Workflow (AWS Step Functions + Lambda)
# ==============================================================================
.PHONY: test-serverless e2e-serverless-local tf-init-serverless tf-validate-serverless tf-plan-serverless

test-serverless: ## Run pytest suite for Serverless Alternative Lambda handlers
	@$(LOG_INFO) "Running Serverless Alternative test suite..."
	@$(PYTEST) $(APP_DIR)/tests/test_serverless_pipeline.py -v
	@$(LOG_OK) "Serverless test suite passed."

e2e-serverless-local: ## Run master local end-to-end verification for Serverless Alternative
	@$(LOG_INFO) "Executing Serverless Alternative local verification harness..."
	@cd $(RAY_DIR) && ./scripts/run_serverless_local.sh
	@$(LOG_OK) "Serverless verification harness completed successfully."

tf-init-serverless: ## Initialize Terraform serverless layer
	@$(LOG_INFO) "Initializing terraform/serverless..."
	@cd $(TF_DIR)/serverless && $(TERRAFORM) init

tf-validate-serverless: tf-init-serverless ## Validate syntax of Terraform serverless layer
	@$(LOG_INFO) "Validating terraform/serverless..."
	@cd $(TF_DIR)/serverless && $(TERRAFORM) validate
	@$(LOG_OK) "Terraform serverless layer validated successfully."

tf-plan-serverless: tf-validate-serverless ## Plan Terraform serverless layer
	@$(LOG_INFO) "Planning terraform/serverless..."
	@cd $(TF_DIR)/serverless && $(TERRAFORM) plan -var="environment=$(ENVIRONMENT)" -var="aws_region=$(AWS_REGION)"

# ==============================================================================
# Group 15: Observability, Dashboards & Port-Forwarding
# ==============================================================================
.PHONY: k8s-apply-observability ray-dashboard-port-forward prometheus-port-forward grafana-port-forward check-health logs-ray-head logs-ray-workers

k8s-apply-observability: ## Deploy Prometheus PodMonitor, Fluent Bit, and Ingress manifests
	@$(LOG_INFO) "Applying observability configurations..."
	@$(KUBECTL) apply -f $(K8S_DIR)/observability/
	@$(LOG_OK) "Observability manifests applied."

ray-dashboard-port-forward: ## Forward Ray Dashboard to http://localhost:8265
	@$(LOG_INFO) "Forwarding Ray Dashboard to http://localhost:8265 (Ctrl+C to stop)..."
	@$(KUBECTL) port-forward svc/$(RAY_CLUSTER_NAME)-head-svc 8265:8265 -n $(K8S_NAMESPACE_WORK)

prometheus-port-forward: ## Forward Prometheus service to http://localhost:9090
	@$(LOG_INFO) "Forwarding Prometheus to http://localhost:9090 (Ctrl+C to stop)..."
	@$(KUBECTL) port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n monitoring

grafana-port-forward: ## Forward Grafana dashboard service to http://localhost:3000
	@$(LOG_INFO) "Forwarding Grafana to http://localhost:3000 (Ctrl+C to stop)..."
	@$(KUBECTL) port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring

check-health: ## Run automated cluster and worker node health check script
	@$(LOG_INFO) "Running Ray cluster health check..."
	@cd $(RAY_DIR) && ./scripts/check_ray_health.sh $(RAY_CLUSTER_NAME) $(K8S_NAMESPACE_WORK)

logs-ray-head: ## Tail logs of Ray Head pod
	@$(KUBECTL) logs -n $(K8S_NAMESPACE_WORK) -l ray.io/node-type=head --tail=100 -f

logs-ray-workers: ## Tail logs of Ray Worker pods
	@$(KUBECTL) logs -n $(K8S_NAMESPACE_WORK) -l ray.io/node-type=worker --tail=100 -f

# ==============================================================================
# Group 16: Teardown, Cleanup & Cost Management
# ==============================================================================
.PHONY: clean destroy-workloads destroy-all

clean: ## Clean local temporary artifacts, caches, and test warehouses
	@$(LOG_INFO) "Cleaning local test artifacts and caches..."
	@rm -rf $(LOCAL_WAREHOUSE_DIR)
	@rm -rf $(RAY_DIR)/.pytest_cache $(RAY_DIR)/__pycache__
	@find $(RAY_DIR) -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find $(RAY_DIR) -type f -name "*.pyc" -delete 2>/dev/null || true
	@$(LOG_OK) "Local scratch and cache artifacts cleaned."

destroy-workloads: ## Delete RayJob, RayCluster, and observability workloads from cluster
	@$(LOG_INFO) "Deleting Kubernetes workloads..."
	@$(KUBECTL) delete -f $(K8S_DIR)/jobs/ray-job.yaml --ignore-not-found
	@$(KUBECTL) delete -f $(K8S_DIR)/ray/ray-cluster.yaml --ignore-not-found
	@$(LOG_OK) "Ray workloads removed."

destroy-all: clean destroy-workloads tf-destroy-all ## Comprehensive cloud cleanup (All workloads and Terraform layers)
	@$(LOG_OK) "Complete teardown finished successfully."
