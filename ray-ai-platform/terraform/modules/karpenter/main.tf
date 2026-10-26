# ==============================================================================
# Karpenter AWS Integration Module
# Implements: Controller IRSA, Node IAM Role, SQS Interruption Queue & EventBridge
# Compatible with Karpenter v1.0+ (EC2NodeClass and NodePool API)
# ==============================================================================

data "aws_partition" "current" {}
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

locals {
  partition  = data.aws_partition.current.partition
  region     = data.aws_region.current.name
  account_id = data.aws_caller_identity.current.account_id

  # Strip protocol prefix if present
  clean_oidc_url = replace(var.oidc_provider_url, "https://", "")
}

# ==============================================================================
# 1. SQS Interruption Queue & EventBridge Rules
# ==============================================================================
resource "aws_sqs_queue" "interruption" {
  name                      = "${var.cluster_name}-karpenter-interruption"
  message_retention_seconds = 300
  sqs_managed_sse_enabled   = true

  tags = merge(
    var.tags,
    {
      Name        = "${var.cluster_name}-karpenter-interruption"
      Environment = var.environment
    }
  )
}

resource "aws_sqs_queue_policy" "interruption" {
  queue_url = aws_sqs_queue.interruption.id

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "EC2InterruptionPolicy"
    Statement = [
      {
        Sid    = "AllowEventsSendMessage"
        Effect = "Allow"
        Principal = {
          Service = ["events.amazonaws.com", "sqs.amazonaws.com"]
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.interruption.arn
      }
    ]
  })
}

# 1.1 Spot Instance Interruption Warning (2-minute advance notice)
resource "aws_cloudwatch_event_rule" "spot_interruption" {
  name        = "${var.cluster_name}-karpenter-spot-interruption"
  description = "Routes EC2 Spot interruption warnings to Karpenter interruption SQS queue"

  event_pattern = jsonencode({
    source      = ["aws.ec2"]
    detail-type = ["EC2 Spot Instance Interruption Warning"]
  })

  tags = var.tags
}

resource "aws_cloudwatch_event_target" "spot_interruption" {
  rule      = aws_cloudwatch_event_rule.spot_interruption.name
  target_id = "KarpenterInterruptionQueueTarget"
  arn       = aws_sqs_queue.interruption.arn
}

# 1.2 EC2 Instance Rebalance Recommendation
resource "aws_cloudwatch_event_rule" "rebalance" {
  name        = "${var.cluster_name}-karpenter-rebalance"
  description = "Routes EC2 Rebalance recommendations to Karpenter queue"

  event_pattern = jsonencode({
    source      = ["aws.ec2"]
    detail-type = ["EC2 Instance Rebalance Recommendation"]
  })

  tags = var.tags
}

resource "aws_cloudwatch_event_target" "rebalance" {
  rule      = aws_cloudwatch_event_rule.rebalance.name
  target_id = "KarpenterRebalanceQueueTarget"
  arn       = aws_sqs_queue.interruption.arn
}

# 1.3 EC2 Instance State-change Notification
resource "aws_cloudwatch_event_rule" "instance_state_change" {
  name        = "${var.cluster_name}-karpenter-state-change"
  description = "Routes EC2 instance state-change notifications to Karpenter queue"

  event_pattern = jsonencode({
    source      = ["aws.ec2"]
    detail-type = ["EC2 Instance State-change Notification"]
  })

  tags = var.tags
}

resource "aws_cloudwatch_event_target" "instance_state_change" {
  rule      = aws_cloudwatch_event_rule.instance_state_change.name
  target_id = "KarpenterInstanceStateChangeTarget"
  arn       = aws_sqs_queue.interruption.arn
}

# 1.4 AWS Health Scheduled Maintenance Events
resource "aws_cloudwatch_event_rule" "health_event" {
  name        = "${var.cluster_name}-karpenter-health-event"
  description = "Routes AWS Health scheduled maintenance events to Karpenter queue"

  event_pattern = jsonencode({
    source      = ["aws.health"]
    detail-type = ["AWS Health Event"]
  })

  tags = var.tags
}

resource "aws_cloudwatch_event_target" "health_event" {
  rule      = aws_cloudwatch_event_rule.health_event.name
  target_id = "KarpenterHealthEventTarget"
  arn       = aws_sqs_queue.interruption.arn
}

# ==============================================================================
# 2. Karpenter Controller IAM Role (IRSA)
# ==============================================================================
resource "aws_iam_role" "controller" {
  name = "${var.cluster_name}-karpenter-controller"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = var.oidc_provider_arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "${local.clean_oidc_url}:sub" = "system:serviceaccount:${var.namespace}:${var.service_account_name}"
            "${local.clean_oidc_url}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = merge(
    var.tags,
    {
      Name        = "${var.cluster_name}-karpenter-controller"
      Environment = var.environment
    }
  )
}

resource "aws_iam_policy" "controller" {
  name        = "${var.cluster_name}-karpenter-controller-policy"
  description = "Scoped permissions for Karpenter controller to provision and manage EC2 compute"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # Read-only EC2 discovery permissions
      {
        Sid    = "EC2Discovery"
        Effect = "Allow"
        Action = [
          "ec2:DescribeAvailabilityZones",
          "ec2:DescribeImages",
          "ec2:DescribeInstances",
          "ec2:DescribeInstanceTypeOfferings",
          "ec2:DescribeInstanceTypes",
          "ec2:DescribeLaunchTemplates",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeSpotPriceHistory",
          "ec2:DescribeSubnets"
        ]
        Resource = "*"
      },
      # Launch instance permissions
      {
        Sid    = "EC2LaunchInstances"
        Effect = "Allow"
        Action = [
          "ec2:CreateFleet",
          "ec2:CreateLaunchTemplate",
          "ec2:RunInstances"
        ]
        Resource = "*"
      },
      # Tagging permissions scoped to Karpenter-managed resources
      {
        Sid    = "EC2Tagging"
        Effect = "Allow"
        Action = [
          "ec2:CreateTags"
        ]
        Resource = [
          "arn:${local.partition}:ec2:${local.region}:${local.account_id}:instance/*",
          "arn:${local.partition}:ec2:${local.region}:${local.account_id}:volume/*",
          "arn:${local.partition}:ec2:${local.region}:${local.account_id}:network-interface/*",
          "arn:${local.partition}:ec2:${local.region}:${local.account_id}:launch-template/*",
          "arn:${local.partition}:ec2:${local.region}:${local.account_id}:spot-instances-request/*"
        ]
      },
      # Terminate and delete permissions strictly scoped to discovery tag
      {
        Sid    = "EC2ScopedTermination"
        Effect = "Allow"
        Action = [
          "ec2:DeleteLaunchTemplate",
          "ec2:TerminateInstances"
        ]
        Resource = [
          "arn:${local.partition}:ec2:${local.region}:${local.account_id}:instance/*",
          "arn:${local.partition}:ec2:${local.region}:${local.account_id}:launch-template/*"
        ]
        Condition = {
          StringEquals = {
            "aws:ResourceTag/karpenter.sh/discovery" = var.cluster_name
          }
        }
      },
      # PassRole permission to attach node role to launched EC2 instances
      {
        Sid    = "PassNodeRole"
        Effect = "Allow"
        Action = "iam:PassRole"
        Resource = [
          aws_iam_role.node.arn
        ]
      },
      # Pricing API permissions for cost-optimized instance selection
      {
        Sid    = "PricingAccess"
        Effect = "Allow"
        Action = [
          "pricing:GetProducts"
        ]
        Resource = "*"
      },
      # SSM Parameter store for resolving official EKS AMIs
      {
        Sid    = "SSMParameterResolution"
        Effect = "Allow"
        Action = [
          "ssm:GetParameter"
        ]
        Resource = [
          "arn:${local.partition}:ssm:${local.region}::parameter/aws/service/eks/optimized-ami/*"
        ]
      },
      # SQS message consumption from interruption queue
      {
        Sid    = "SQSInterruptionAccess"
        Effect = "Allow"
        Action = [
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:GetQueueUrl",
          "sqs:ReceiveMessage"
        ]
        Resource = [
          aws_sqs_queue.interruption.arn
        ]
      },
      # Describe cluster for version and endpoint discovery
      {
        Sid    = "EKSClusterDescribe"
        Effect = "Allow"
        Action = [
          "eks:DescribeCluster"
        ]
        Resource = [
          "arn:${local.partition}:eks:${local.region}:${local.account_id}:cluster/${var.cluster_name}"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "controller" {
  role       = aws_iam_role.controller.name
  policy_arn = aws_iam_policy.controller.arn
}

# ==============================================================================
# 3. Karpenter Node IAM Role & Instance Profile
# ==============================================================================
resource "aws_iam_role" "node" {
  name = "${var.cluster_name}-karpenter-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(
    var.tags,
    {
      Name        = "${var.cluster_name}-karpenter-node-role"
      Environment = var.environment
    }
  )
}

resource "aws_iam_role_policy_attachment" "node_AmazonEKSWorkerNodePolicy" {
  role       = aws_iam_role.node.name
  policy_arn = "arn:${local.partition}:iam::aws:policy/AmazonEKSWorkerNodePolicy"
}

resource "aws_iam_role_policy_attachment" "node_AmazonEKS_CNI_Policy" {
  role       = aws_iam_role.node.name
  policy_arn = "arn:${local.partition}:iam::aws:policy/AmazonEKS_CNI_Policy"
}

resource "aws_iam_role_policy_attachment" "node_AmazonEC2ContainerRegistryReadOnly" {
  role       = aws_iam_role.node.name
  policy_arn = "arn:${local.partition}:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "node_AmazonSSMManagedInstanceCore" {
  role       = aws_iam_role.node.name
  policy_arn = "arn:${local.partition}:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "node" {
  name = "${var.cluster_name}-karpenter-node-profile"
  role = aws_iam_role.node.name

  tags = var.tags
}

# ==============================================================================
# 4. EKS Access Entry for Karpenter Nodes (Zero-Trust Modern Auth)
# ==============================================================================
resource "aws_eks_access_entry" "karpenter_node" {
  cluster_name  = var.cluster_name
  principal_arn = aws_iam_role.node.arn
  type          = "EC2_LINUX"
}
