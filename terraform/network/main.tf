locals {
  cluster_name = "${var.project_name}-${var.environment}-eks"
}

module "vpc" {
  source = "../modules/vpc"

  vpc_cidr                  = var.vpc_cidr
  availability_zones        = var.availability_zones
  cluster_name              = local.cluster_name
  environment               = var.environment
  project_name              = var.project_name
  enable_single_nat_gateway = var.enable_single_nat_gateway
  tags                      = var.tags
}

# ==============================================================================
# Security Group for Internal Ray Workload Communication
# ==============================================================================
resource "aws_security_group" "ray_internal" {
  name_prefix = "${var.project_name}-${var.environment}-ray-internal-"
  description = "Allows high-throughput private communication between Ray Head and Worker pods"
  vpc_id      = module.vpc.vpc_id

  # Self-referencing ingress: All Ray worker and head pods can communicate freely
  ingress {
    description = "Intra-cluster Ray GCS, Raylet, Object Store, and RPC communication"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    self        = true
  }

  egress {
    description = "Allow all outbound traffic to VPC endpoints and NAT"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-ray-internal-sg"
    }
  )

  lifecycle {
    create_before_destroy = true
  }
}
