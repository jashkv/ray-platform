locals {
  cluster_name = "${var.project_name}-${var.environment}-eks"
}

module "eks" {
  source = "../modules/eks"

  cluster_name           = local.cluster_name
  cluster_version        = var.cluster_version
  vpc_id                 = var.vpc_id
  private_subnet_ids     = var.private_subnet_ids
  environment            = var.environment
  project_name           = var.project_name
  endpoint_public_access = true
  tags                   = var.tags
}
