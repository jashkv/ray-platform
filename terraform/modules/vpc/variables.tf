variable "vpc_cidr" {
  description = "The CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones to deploy subnets into"
  type        = list(string)
}

variable "public_subnet_cidrs" {
  description = "List of CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.0.0/20", "10.0.16.0/20", "10.0.32.0/20"]
}

variable "private_subnet_cidrs" {
  description = "List of CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.64.0/20", "10.0.80.0/20", "10.0.96.0/20"]
}

variable "cluster_name" {
  description = "EKS cluster name for subnet discovery tags"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g. test)"
  type        = string
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "enable_single_nat_gateway" {
  description = "Set to true to use a single NAT gateway to minimize AWS charges in test environment"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Additional resource tags"
  type        = map(string)
  default     = {}
}
