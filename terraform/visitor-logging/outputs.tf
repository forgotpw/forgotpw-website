output "traffic_log_bucket" {
  description = "Private S3 bucket receiving CloudFront standard access logs."
  value       = aws_s3_bucket.traffic_logs.id
}

output "cloudfront_delivery_source" {
  description = "CloudWatch Logs delivery source attached to the existing CloudFront distribution."
  value       = aws_cloudwatch_log_delivery_source.cloudfront.name
}

output "retention_days" {
  description = "Configured S3 access-log retention."
  value       = var.retention_days
}
