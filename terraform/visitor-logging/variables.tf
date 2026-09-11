variable "aws_region" {
  description = "AWS region used for CloudFront standard logging v2 API calls and log storage."
  type        = string
  default     = "us-east-1"

  validation {
    condition     = var.aws_region == "us-east-1"
    error_message = "CloudFront standard logging v2 API calls must use us-east-1."
  }
}

variable "environment" {
  description = "Deployment environment."
  type        = string

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be dev or prod."
  }
}

variable "expected_account_id" {
  description = "AWS account that owns the existing CloudFront distribution."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.expected_account_id))
    error_message = "Expected account ID must contain exactly 12 digits."
  }
}

variable "cloudfront_distribution_id" {
  description = "ID of the existing Rosa CloudFront distribution. Terraform does not manage the distribution itself."
  type        = string
}

variable "retention_days" {
  description = "Number of days before CloudFront access log objects expire."
  type        = number

  validation {
    condition     = var.retention_days >= 1 && var.retention_days <= 365
    error_message = "Retention must be between 1 and 365 days."
  }
}
