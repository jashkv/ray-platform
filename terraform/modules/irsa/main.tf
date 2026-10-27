# ==============================================================================
# IRSA Role for Ray Pod ServiceAccount
# ==============================================================================
resource "aws_iam_role" "ray_workload" {
  name = var.role_name

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
            "${var.oidc_provider_url}:sub" = "system:serviceaccount:${var.namespace}:${var.service_account_name}"
            "${var.oidc_provider_url}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = var.tags
}

# ==============================================================================
# Least-Privilege S3, Glue, DynamoDB & KMS Policies
# ==============================================================================
resource "aws_iam_policy" "ray_data_access" {
  name        = "${var.role_name}-data-policy"
  description = "Least-privilege policy allowing Ray pipeline pods to access S3 lakehouse, Glue catalog, and DynamoDB ledger"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # S3 Access
      {
        Sid    = "S3LakehouseBucketAccess"
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [var.data_bucket_arn]
      },
      {
        Sid    = "S3LakehouseObjectAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = ["${var.data_bucket_arn}/*"]
      },
      # AWS Glue Catalog Access (for PyIceberg)
      {
        Sid    = "GlueCatalogAccess"
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetDatabases",
          "glue:GetTable",
          "glue:GetTables",
          "glue:CreateTable",
          "glue:UpdateTable",
          "glue:GetPartitions",
          "glue:BatchCreatePartition"
        ]
        Resource = [
          "arn:aws:glue:*:*:catalog",
          var.glue_database_arn,
          "arn:aws:glue:*:*:table/${split("/", var.glue_database_arn)[1]}/*"
        ]
      },
      # DynamoDB Processing Ledger Access
      {
        Sid    = "DynamoDBLedgerAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query"
        ]
        Resource = [
          var.ledger_table_arn,
          "${var.ledger_table_arn}/index/*"
        ]
      },
      # KMS Decryption & Encryption
      {
        Sid    = "KMSKeyAccess"
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:Encrypt",
          "kms:GenerateDataKey*"
        ]
        Resource = [var.kms_key_arn]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ray_workload_attach" {
  role       = aws_iam_role.ray_workload.name
  policy_arn = aws_iam_policy.ray_data_access.arn
}
