# ==============================================================================
# EKS Access Entries (Replacing legacy aws-auth ConfigMap)
# ==============================================================================
data "aws_caller_identity" "current" {}

locals {
  # Default to current IAM caller if no additional principals are specified
  effective_admin_arns = length(var.admin_principal_arns) > 0 ? var.admin_principal_arns : [data.aws_caller_identity.current.arn]
}

resource "aws_eks_access_entry" "cluster_admins" {
  count         = length(local.effective_admin_arns)
  cluster_name  = module.eks.cluster_name
  principal_arn = local.effective_admin_arns[count.index]
  type          = "STANDARD"
}

resource "aws_eks_access_policy_association" "cluster_admins_policy" {
  count         = length(local.effective_admin_arns)
  cluster_name  = module.eks.cluster_name
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
  principal_arn = local.effective_admin_arns[count.index]

  access_scope {
    type = "cluster"
  }

  depends_on = [aws_eks_access_entry.cluster_admins]
}
