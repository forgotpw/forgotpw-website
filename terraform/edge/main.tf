# The website's CloudFront distribution and its DNS aliases. They were created by the
# Terraform 0.11 stacks in terraform/dev and terraform/prod, whose AWS provider cannot
# attach a response headers policy or set the TLS 1.2 minimum by name; imports.tf adopted
# them here.

data "aws_acm_certificate" "site" {
  domain   = var.hostname
  statuses = ["ISSUED"]
}

resource "aws_cloudfront_response_headers_policy" "site" {
  name    = "rosa-website-security-${var.environment}"
  comment = "Security headers for ${var.hostname}"

  security_headers_config {
    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains         = true
      override                   = true
    }
    content_type_options {
      override = true
    }
    frame_options {
      frame_option = "DENY"
      override     = true
    }
    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
      override        = true
    }
    content_security_policy {
      content_security_policy = "frame-ancestors 'none'"
      override                = true
    }
  }
}

resource "aws_cloudfront_distribution" "site" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  aliases             = [var.hostname]
  price_class         = "PriceClass_100"

  origin {
    origin_id   = var.hostname
    domain_name = "${var.hostname}.s3.amazonaws.com"
  }

  default_cache_behavior {
    # All methods are allowed for CORS.
    allowed_methods            = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods             = ["GET", "HEAD"]
    target_origin_id           = var.hostname
    viewer_protocol_policy     = "redirect-to-https"
    min_ttl                    = 0
    default_ttl                = 300
    max_ttl                    = 3600
    compress                   = true
    response_headers_policy_id = aws_cloudfront_response_headers_policy.site.id

    forwarded_values {
      query_string = true
      headers      = ["Access-Control-*", "Origin"]
      cookies {
        forward = "none"
      }
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = data.aws_acm_certificate.site.arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
}

resource "aws_route53_record" "alias" {
  for_each = toset(["A", "AAAA"])
  zone_id  = var.dns_zone_id
  name     = var.hostname
  type     = each.key

  alias {
    name                   = aws_cloudfront_distribution.site.domain_name
    zone_id                = aws_cloudfront_distribution.site.hosted_zone_id
    evaluate_target_health = false
  }
}
