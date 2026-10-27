# ==============================================================================
# 1. Head / System Node Group (On-Demand, Dedicated)
# ==============================================================================
resource "aws_eks_node_group" "head_system" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.cluster_name}-head-system-pool"
  node_role_arn   = aws_iam_role.node_group.arn
  subnet_ids      = var.private_subnet_ids

  capacity_type  = "ON_DEMAND"
  instance_types = var.head_node_instance_types
  ami_type       = var.head_node_ami_type

  scaling_config {
    desired_size = 1
    min_size     = 1
    max_size     = 2
  }

  update_config {
    max_unavailable = 1
  }

  labels = {
    "workload-role" = "ray-head-system"
  }

  tags = merge(
    var.tags,
    {
      Name                                        = "${var.cluster_name}-head-system-node"
      "karpenter.sh/discovery"                    = var.cluster_name
      "kubernetes.io/cluster/${var.cluster_name}" = "owned"
    }
  )

  depends_on = [
    aws_iam_role_policy_attachment.node_group_AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.node_group_AmazonEKS_CNI_Policy,
    aws_iam_role_policy_attachment.node_group_AmazonEC2ContainerRegistryReadOnly,
  ]
}

# ==============================================================================
# 2. Ray Worker Node Group (Spot Diversified - ~70% Cost Reduction)
# ==============================================================================
resource "aws_eks_node_group" "worker_spot" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.cluster_name}-worker-spot-pool"
  node_role_arn   = aws_iam_role.node_group.arn
  subnet_ids      = var.private_subnet_ids

  capacity_type  = "SPOT"
  instance_types = var.worker_spot_instance_types
  ami_type       = var.head_node_ami_type

  scaling_config {
    desired_size = var.worker_desired_size
    min_size     = var.worker_min_size
    max_size     = var.worker_max_size
  }

  update_config {
    max_unavailable_percentage = 33
  }

  labels = {
    "workload-role"    = "ray-worker"
    "ray.io/node-type" = "worker"
    "lifecycle"        = "Ec2Spot"
  }

  # Isolate Ray worker nodes from generic system pods (CoreDNS, FluentBit, etc.)
  taint {
    key    = "workload-role"
    value  = "ray-worker"
    effect = "NO_SCHEDULE"
  }

  tags = merge(
    var.tags,
    {
      Name                                        = "${var.cluster_name}-worker-spot-node"
      "karpenter.sh/discovery"                    = var.cluster_name
      "kubernetes.io/cluster/${var.cluster_name}" = "owned"
    }
  )

  depends_on = [
    aws_iam_role_policy_attachment.node_group_AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.node_group_AmazonEKS_CNI_Policy,
    aws_iam_role_policy_attachment.node_group_AmazonEC2ContainerRegistryReadOnly,
  ]
}

# ==============================================================================
# 3. Ray Worker On-Demand Fallback Pool (Zero default nodes, scales only if Spot exhausted)
# ==============================================================================
resource "aws_eks_node_group" "worker_ondemand_fallback" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.cluster_name}-worker-ondemand-fallback"
  node_role_arn   = aws_iam_role.node_group.arn
  subnet_ids      = var.private_subnet_ids

  capacity_type  = "ON_DEMAND"
  instance_types = var.head_node_instance_types
  ami_type       = var.head_node_ami_type

  scaling_config {
    desired_size = 0
    min_size     = 0
    max_size     = 5
  }

  labels = {
    "workload-role"    = "ray-worker"
    "ray.io/node-type" = "worker"
    "lifecycle"        = "OnDemand"
  }

  taint {
    key    = "workload-role"
    value  = "ray-worker"
    effect = "NO_SCHEDULE"
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.cluster_name}-worker-ondemand-fallback"
    }
  )

  depends_on = [
    aws_iam_role_policy_attachment.node_group_AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.node_group_AmazonEKS_CNI_Policy,
    aws_iam_role_policy_attachment.node_group_AmazonEC2ContainerRegistryReadOnly,
  ]
}
