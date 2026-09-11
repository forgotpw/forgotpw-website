# Dedicated redirect resources: do not import or change the live www distribution.
resource "aws_acm_certificate" "redirect" {
  domain_name       = var.domain_name
  validation_method = "DNS"
  lifecycle {
    create_before_destroy = true
  }
}

locals {
  validation = one(aws_acm_certificate.redirect.domain_validation_options)
}

# Development DNS is in the deployment account. Production DNS is owned by the
# management account; publish the validation_record output there once and retain
# it for automatic ACM renewal. No cross-account IAM grant is needed.
resource "aws_route53_record" "validation" {
  count   = var.dns_zone_id == null ? 0 : 1
  zone_id = var.dns_zone_id
  name    = local.validation.resource_record_name
  type    = local.validation.resource_record_type
  ttl     = 300
  records = [local.validation.resource_record_value]
}

resource "aws_acm_certificate_validation" "redirect" {
  certificate_arn         = aws_acm_certificate.redirect.arn
  validation_record_fqdns = [local.validation.resource_record_name]
  depends_on              = [aws_route53_record.validation]
  timeouts {
    create = "15m"
  }
}

resource "aws_cloudfront_function" "redirect" {
  name    = "rosa-apex-redirect-${var.environment}"
  runtime = "cloudfront-js-2.0"
  comment = "Permanent redirect to the canonical Rosa website"
  publish = true
  code = templatefile("${path.module}/redirect.js.tftpl", {
    canonical_hostname = var.canonical_hostname
  })
}

resource "aws_cloudfront_distribution" "redirect" {
  enabled         = true
  is_ipv6_enabled = true
  aliases         = [var.domain_name]
  comment         = "Rosa canonical hostname redirect (${var.environment})"
  price_class     = "PriceClass_100"

  # CloudFront requires an origin. The viewer-request function returns every
  # response at the edge, before this existing website origin is contacted.
  origin {
    origin_id   = "website"
    domain_name = "${var.canonical_hostname}.s3.amazonaws.com"
    s3_origin_config {
      origin_access_identity = ""
    }
  }
  default_cache_behavior {
    target_origin_id       = "website"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    viewer_protocol_policy = "allow-all"
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.redirect.arn
    }
  }
  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate_validation.redirect.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
}

resource "aws_route53_record" "redirect" {
  for_each = var.dns_zone_id == null ? toset([]) : toset(["A", "AAAA"])
  zone_id  = var.dns_zone_id
  name     = var.domain_name
  type     = each.key
  alias {
    name                   = aws_cloudfront_distribution.redirect.domain_name
    zone_id                = aws_cloudfront_distribution.redirect.hosted_zone_id
    evaluate_target_health = false
  }
}
