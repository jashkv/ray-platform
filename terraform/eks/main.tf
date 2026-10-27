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

# ==============================================================================
# Karpenter Infrastructure Integration
# Controller IRSA, Node IAM Role, SQS Interruption Queue & EventBridge Rules
# ==============================================================================
module "karpenter" {
  source = "../modules/karpenter"

  cluster_name      = module.eks.cluster_name
  oidc_provider_arn = module.eks.oidc_provider_arn
  oidc_provider_url = module.eks.oidc_provider_url
  environment       = var.environment
  tags              = var.tags
}
