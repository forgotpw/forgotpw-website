output "validation_record" {
  description = "Publish this CNAME in the management-account parent zone for production certificate validation and renewal."
  value = {
    name  = local.validation.resource_record_name
    type  = local.validation.resource_record_type
    value = local.validation.resource_record_value
  }
}
output "distribution_domain_name" {
  value = aws_cloudfront_distribution.redirect.domain_name
}
output "distribution_id" {
  value = aws_cloudfront_distribution.redirect.id
}
output "alias_zone_id" {
  value = aws_cloudfront_distribution.redirect.hosted_zone_id
}
output "redirect_url" {
  value = "https://${var.domain_name}"
}
