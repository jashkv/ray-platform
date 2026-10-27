# ==============================================================================
# SQS Dead-Letter Queue for Failed State Machine Executions
# ==============================================================================
resource "aws_sqs_queue" "dlq" {
  name                      = "${var.project_name}-${var.environment}-pipeline-dlq"
  message_retention_seconds = 1209600 # 14 days
  sqs_managed_sse_enabled   = true

  tags = var.tags
}

# ==============================================================================
# Packaging Lambda Deployment Artifact
# ==============================================================================
data "archive_file" "lambda_dummy" {
  type        = "zip"
  output_path = "${path.module}/lambda_payload.zip"

  source {
    content  = "# Placeholder for serverless handler\ndef handler(event, context):\n    return {'statusCode': 200}"
    filename = "handler.py"
  }
}

# ==============================================================================
# Lambda Functions for Each Stage of Serverless Pipeline
# ==============================================================================
resource "aws_lambda_function" "discovery" {
  function_name = "${var.project_name}-${var.environment}-discovery"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "application.src.serverless.handlers.handler_discovery"
  runtime       = "python3.11"
  timeout       = 60
  memory_size   = 512

  filename         = data.archive_file.lambda_dummy.output_path
  source_code_hash = data.archive_file.lambda_dummy.output_base64sha256

  environment {
    variables = {
      LEDGER_TABLE_NAME = var.ledger_table_name
      DATA_BUCKET_NAME  = var.data_bucket_name
    }
  }

  tags = var.tags
}

resource "aws_lambda_function" "validator" {
  function_name = "${var.project_name}-${var.environment}-validator"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "application.src.serverless.handlers.handler_validator"
  runtime       = "python3.11"
  timeout       = 300
  memory_size   = 1024

  filename         = data.archive_file.lambda_dummy.output_path
  source_code_hash = data.archive_file.lambda_dummy.output_base64sha256

  environment {
    variables = {
      DATA_BUCKET_NAME = var.data_bucket_name
    }
  }

  tags = var.tags
}

resource "aws_lambda_function" "resolver" {
  function_name = "${var.project_name}-${var.environment}-resolver"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "application.src.serverless.handlers.handler_resolver"
  runtime       = "python3.11"
  timeout       = 900
  memory_size   = 2048

  filename         = data.archive_file.lambda_dummy.output_path
  source_code_hash = data.archive_file.lambda_dummy.output_base64sha256

  environment {
    variables = {
      DATA_BUCKET_NAME = var.data_bucket_name
    }
  }

  tags = var.tags
}

resource "aws_lambda_function" "iceberg_sink" {
  function_name = "${var.project_name}-${var.environment}-iceberg-sink"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "application.src.serverless.handlers.handler_iceberg_sink"
  runtime       = "python3.11"
  timeout       = 600
  memory_size   = 2048

  filename         = data.archive_file.lambda_dummy.output_path
  source_code_hash = data.archive_file.lambda_dummy.output_base64sha256

  environment {
    variables = {
      ICEBERG_CATALOG_TYPE = "glue"
      ICEBERG_WAREHOUSE    = "s3://${var.data_bucket_name}/iceberg-warehouse/"
      GLUE_DATABASE_NAME   = var.glue_database_name
    }
  }

  tags = var.tags
}

resource "aws_lambda_function" "trainer" {
  function_name = "${var.project_name}-${var.environment}-trainer"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "application.src.serverless.handlers.handler_trainer"
  runtime       = "python3.11"
  timeout       = 900
  memory_size   = 3072

  filename         = data.archive_file.lambda_dummy.output_path
  source_code_hash = data.archive_file.lambda_dummy.output_base64sha256

  environment {
    variables = {
      DATA_BUCKET_NAME = var.data_bucket_name
    }
  }

  tags = var.tags
}

resource "aws_lambda_function" "finalizer" {
  function_name = "${var.project_name}-${var.environment}-finalizer"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "application.src.serverless.handlers.handler_finalizer"
  runtime       = "python3.11"
  timeout       = 60
  memory_size   = 512

  filename         = data.archive_file.lambda_dummy.output_path
  source_code_hash = data.archive_file.lambda_dummy.output_base64sha256

  environment {
    variables = {
      LEDGER_TABLE_NAME = var.ledger_table_name
    }
  }

  tags = var.tags
}

# ==============================================================================
# CloudWatch Log Group for Step Functions Telemetry
# ==============================================================================
resource "aws_cloudwatch_log_group" "sfn_logs" {
  name              = "/aws/vendedlogs/states/${var.project_name}-${var.environment}-pipeline"
  retention_in_days = 30

  tags = var.tags
}

# ==============================================================================
# AWS Step Functions State Machine
# ==============================================================================
resource "aws_sfn_state_machine" "pipeline" {
  name     = "${var.project_name}-${var.environment}-pipeline-sfn"
  role_arn = aws_iam_role.step_functions.arn

  definition = templatefile("${path.module}/step_functions_pipeline.asl.json", {
    discovery_lambda_arn  = aws_lambda_function.discovery.arn
    validator_lambda_arn  = aws_lambda_function.validator.arn
    resolver_lambda_arn   = aws_lambda_function.resolver.arn
    iceberg_lambda_arn    = aws_lambda_function.iceberg_sink.arn
    trainer_lambda_arn    = aws_lambda_function.trainer.arn
    finalizer_lambda_arn  = aws_lambda_function.finalizer.arn
    iceberg_warehouse_uri = "s3://${var.data_bucket_name}/iceberg-warehouse/"
    glue_database_name    = var.glue_database_name
    s3_models_prefix      = "s3://${var.data_bucket_name}/models/"
    dlq_url               = aws_sqs_queue.dlq.url
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.sfn_logs.arn}:*"
    include_execution_data = true
    level                  = "ALL"
  }

  tags = var.tags
}

# ==============================================================================
# EventBridge Scheduled Ingestion Trigger (Rate: 15 minutes)
# ==============================================================================
resource "aws_cloudwatch_event_rule" "pipeline_schedule" {
  name                = "${var.project_name}-${var.environment}-pipeline-schedule"
  description         = "Periodic trigger for Serverless Alternative data pipeline"
  schedule_expression = "rate(15 minutes)"

  tags = var.tags
}

resource "aws_iam_role" "eventbridge_sfn" {
  name = "${var.project_name}-${var.environment}-eventbridge-sfn-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_policy" "eventbridge_sfn" {
  name = "${var.project_name}-${var.environment}-eventbridge-sfn-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["states:StartExecution"]
        Resource = [aws_sfn_state_machine.pipeline.arn]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eventbridge_sfn" {
  role       = aws_iam_role.eventbridge_sfn.name
  policy_arn = aws_iam_policy.eventbridge_sfn.arn
}

resource "aws_cloudwatch_event_target" "step_functions" {
  rule     = aws_cloudwatch_event_rule.pipeline_schedule.name
  arn      = aws_sfn_state_machine.pipeline.arn
  role_arn = aws_iam_role.eventbridge_sfn.arn

  input = jsonencode({
    s1_input = "s3://${var.data_bucket_name}/incoming/supply_chain_data_s1.csv"
    s2_input = "s3://${var.data_bucket_name}/incoming/financial_data_s2.csv"
  })
}
