# ==============================================================================
# GitHub Actions AWS OIDC Federation (Zero Static Credentials)
# ==============================================================================
data "tls_certificate" "github" {
  url = "https://token.actions.githubusercontent.com"
}

resource "aws_iam_openid_connect_provider" "github_actions" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.github.certificates[0].sha1_fingerprint]

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-github-oidc"
    }
  )
}

resource "aws_iam_role" "github_actions_deployer" {
  name = "${var.project_name}-${var.environment}-gha-deployer"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github_actions.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            # Bounded strictly to main branch pushes on the repository
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_repository}:*"
          }
        }
      }
    ]
  })

  tags = var.tags
}

# Least-privilege policy for ECR push and EKS job submission
resource "aws_iam_policy" "gha_deploy_policy" {
  name = "${var.project_name}-${var.environment}-gha-deploy-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # ECR Authentication & Image Push
      {
        Sid    = "ECRAuth"
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload"
        ]
        Resource = "*"
      },
      # EKS Describe to update-kubeconfig
      {
        Sid    = "EKSDescribe"
        Effect = "Allow"
        Action = [
          "eks:DescribeCluster"
        ]
        Resource = [var.eks_cluster_arn]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "gha_deploy_attach" {
  role       = aws_iam_role.github_actions_deployer.name
  policy_arn = aws_iam_policy.gha_deploy_policy.arn
}
