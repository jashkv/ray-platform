output "state_bucket_name" {
  description = "The S3 bucket name created for remote state storage"
  value       = aws_s3_bucket.terraform_state.id
}

output "state_bucket_arn" {
  description = "The ARN of the remote state S3 bucket"
  value       = aws_s3_bucket.terraform_state.arn
}

output "dynamodb_table_name" {
  description = "The DynamoDB table name for state locking"
  value       = aws_dynamodb_table.terraform_lock.name
}

output "kms_key_arn" {
  description = "The KMS Key ARN used for encrypting Terraform state and locks"
  value       = aws_kms_key.terraform_state.arn
}

output "backend_config_example" {
  description = "Terraform backend configuration block to use across subsequent layers"
  value       = <<-EOT
    terraform {
      backend "s3" {
        bucket         = "${aws_s3_bucket.terraform_state.id}"
        key            = "layer-name/terraform.tfstate"
        region         = "${var.aws_region}"
        dynamodb_table = "${aws_dynamodb_table.terraform_lock.name}"
        encrypt        = true
        kms_key_id     = "${aws_kms_key.terraform_state.arn}"
      }
    }
  EOT
}
