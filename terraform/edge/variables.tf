variable "environment" {
  type = string
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be dev or prod."
  }
}
variable "expected_account_id" {
  type = string
}
variable "hostname" {
  description = "The website's hostname, also its S3 bucket name."
  type        = string
}
variable "distribution_id" {
  description = "The website's existing CloudFront distribution, adopted by imports.tf."
  type        = string
}
variable "dns_zone_id" {
  description = "The hosted zone that holds the hostname's alias records."
  type        = string
}
