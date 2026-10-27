variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
}

variable "cluster_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.31"
}

variable "vpc_id" {
  description = "VPC ID where the cluster is deployed"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for worker nodes"
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs for external load balancers"
  type        = list(string)
  default     = []
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "endpoint_public_access" {
  description = "Enable Kubernetes API server public endpoint"
  type        = bool
  default     = true
}

variable "public_access_cidrs" {
  description = "List of CIDR blocks permitted to access public API server"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "head_node_instance_types" {
  description = "Instance types for On-Demand Head/System node group (Graviton3 ARM64)"
  type        = list(string)
  default     = ["m7g.xlarge"]
}

variable "head_node_ami_type" {
  description = "AMI type for On-Demand Head/System node group"
  type        = string
  default     = "AL2023_ARM_64_STANDARD"
}

variable "worker_spot_instance_types" {
  description = "Diversified Graviton instance types for Spot worker node group"
  type        = list(string)
  default     = ["m7g.xlarge", "m6g.xlarge", "m7g.2xlarge", "m6g.2xlarge"]
}

variable "worker_min_size" {
  description = "Minimum number of worker nodes"
  type        = number
  default     = 0
}

variable "worker_max_size" {
  description = "Maximum number of worker nodes"
  type        = number
  default     = 10
}

variable "worker_desired_size" {
  description = "Desired number of worker nodes (0 when managed dynamically by Karpenter)"
  type        = number
  default     = 0
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
