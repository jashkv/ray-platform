output "state_machine_arn" {
  description = "ARN of the Step Functions State Machine"
  value       = aws_sfn_state_machine.pipeline.arn
}

output "state_machine_name" {
  description = "Name of the Step Functions State Machine"
  value       = aws_sfn_state_machine.pipeline.name
}

output "discovery_lambda_arn" {
  description = "ARN of Discovery Lambda"
  value       = aws_lambda_function.discovery.arn
}

output "validator_lambda_arn" {
  description = "ARN of Validator Lambda"
  value       = aws_lambda_function.validator.arn
}

output "resolver_lambda_arn" {
  description = "ARN of Resolver Lambda"
  value       = aws_lambda_function.resolver.arn
}

output "iceberg_sink_lambda_arn" {
  description = "ARN of Iceberg Sink Lambda"
  value       = aws_lambda_function.iceberg_sink.arn
}

output "trainer_lambda_arn" {
  description = "ARN of ML Trainer Lambda"
  value       = aws_lambda_function.trainer.arn
}

output "finalizer_lambda_arn" {
  description = "ARN of Finalizer Lambda"
  value       = aws_lambda_function.finalizer.arn
}

output "dlq_url" {
  description = "URL of SQS Dead-Letter Queue"
  value       = aws_sqs_queue.dlq.url
}
