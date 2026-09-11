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
variable "domain_name" {
  description = "Hostname that permanently redirects to the canonical website."
  type        = string
}
variable "canonical_hostname" {
  type = string
  validation {
    condition     = contains(["www-dev.rosa.bot", "www.rosa.bot"], var.canonical_hostname)
    error_message = "Redirects must target a Rosa website hostname."
  }
}
variable "dns_zone_id" {
  description = "Same-account zone, or null for production's separately administered management-account DNS."
  type        = string
  default     = null
}
