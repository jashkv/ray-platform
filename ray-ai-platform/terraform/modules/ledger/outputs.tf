output "table_name" {
  description = "The DynamoDB ledger table name"
  value       = aws_dynamodb_table.ledger.name
}

output "table_arn" {
  description = "The DynamoDB ledger table ARN"
  value       = aws_dynamodb_table.ledger.arn
}
