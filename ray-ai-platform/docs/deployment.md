# Deployment Guide — Ray AI Platform on AWS

This guide details the step-by-step deployment procedure for the **Distributed AI Foundation** platform on AWS.

---

## 1. Prerequisites & Tooling
Ensure the following tools are installed on the deployment workstation or CI runner:
- Terraform $\ge 1.5.0$ (`v1.15.8` tested)
- AWS CLI v2 (`v2.35.9` tested)
- Python $\ge 3.11$ (`3.12` tested via `uv`)
- Docker (or GitHub Actions runner for container builds)
- `kubectl` $\ge 1.30$

---

## 2. Step-by-Step Deployment Procedure

### Step 1: Terraform Remote State Bootstrap (`01-bootstrap`)
```bash
cd terraform/bootstrap
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan -out=bootstrap.tfplan
terraform apply bootstrap.tfplan
```
*Outputs: Capture `state_bucket_name` and `dynamodb_table_name`.*

---

### Step 2: Network Infrastructure (`02-network`)
```bash
cd ../network
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan -out=network.tfplan
terraform apply network.tfplan
```
*Outputs: Capture `vpc_id` and `private_subnet_ids`.*

---

### Step 3: EKS Cluster & Node Pools (`03-eks`)
```bash
cd ../eks
cp terraform.tfvars.example terraform.tfvars
# Update vpc_id and private_subnet_ids from Step 2
terraform init
terraform plan -out=eks.tfplan
terraform apply eks.tfplan

# Configure local kubectl context
aws eks update-kubeconfig --region us-east-1 --name ray-platform-dev-eks
```

---

### Step 4: S3 Lakehouse & IRSA Data Layer (`04-data`)
```bash
cd ../data
cp terraform.tfvars.example terraform.tfvars
# Update oidc_provider_arn from Step 3
terraform init
terraform plan -out=data.tfplan
terraform apply data.tfplan
```
*Outputs: Capture `data_bucket_id` and `ray_pipeline_role_arn`.*

---

### Step 5: Platform & Container Registry (`05-platform`)
```bash
cd ../platform
terraform init
terraform plan -out=platform.tfplan
terraform apply platform.tfplan
```

---

### Step 6: Deploy KubeRay Operator & Namespaces
```bash
cd ../../
kubectl apply -f kubernetes/namespaces/namespaces.yaml
kubectl apply -f kubernetes/security/rbac.yaml
kubectl apply -f kubernetes/security/secrets.yaml

# Deploy KubeRay Operator
kubectl apply -f kubernetes/ray/kuberay-operator.yaml
kubectl rollout status deployment -n ray-system kuberay-operator
```

---

### Step 7: Launch RayCluster & Submit RayJob
```bash
# Launch RayCluster
kubectl apply -f kubernetes/ray/ray-cluster.yaml
kubectl wait --for=condition=ready pod -l ray.io/node-type=head -n ray-workloads --timeout=300s

# Submit RayJob pipeline execution
kubectl apply -f kubernetes/jobs/ray-job.yaml

# Monitor Job status
kubectl get rayjobs.ray.io -n ray-workloads -w
```

---

## 3. Teardown & Resource Cleanup

To avoid unnecessary AWS charges after testing, destroy resources in reverse order:

```bash
# 1. Delete Kubernetes workloads
kubectl delete -f kubernetes/jobs/ray-job.yaml --ignore-not-found
kubectl delete -f kubernetes/ray/ray-cluster.yaml --ignore-not-found
kubectl delete -f kubernetes/ray/kuberay-operator.yaml --ignore-not-found

# 2. Destroy Terraform layers in reverse order
cd terraform/platform && terraform destroy -auto-approve
cd ../data && terraform destroy -auto-approve
cd ../eks && terraform destroy -auto-approve
cd ../network && terraform destroy -auto-approve
cd ../bootstrap && terraform destroy -auto-approve
```
