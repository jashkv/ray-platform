output "bucket_id" {
  description = "The S3 data bucket name"
  value       = aws_s3_bucket.data.id
}

output "bucket_arn" {
  description = "The S3 data bucket ARN"
  value       = aws_s3_bucket.data.arn
}
