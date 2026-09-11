data "aws_caller_identity" "current" {}

locals {
  log_bucket_name      = "rosa-website-traffic-logs-${var.environment}-${var.expected_account_id}"
  distribution_arn     = "arn:aws:cloudfront::${var.expected_account_id}:distribution/${var.cloudfront_distribution_id}"
  logs_service_arn     = "arn:aws:logs:${var.aws_region}:${var.expected_account_id}:*"
  delivery_source_name = "rosa-website-cloudfront-access-logs"
}

resource "aws_s3_bucket" "traffic_logs" {
  bucket = local.log_bucket_name

  lifecycle {
    prevent_destroy = true

    precondition {
      condition     = data.aws_caller_identity.current.account_id == var.expected_account_id
      error_message = "Authenticated AWS account does not match expected_account_id."
    }
  }
}

# CloudWatch vended log delivery writes bucket-owner-full-control ACLs. Keep ACLs
# enabled for delivered objects while retaining bucket ownership.
resource "aws_s3_bucket_ownership_controls" "traffic_logs" {
  bucket = aws_s3_bucket.traffic_logs.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_public_access_block" "traffic_logs" {
  bucket = aws_s3_bucket.traffic_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "traffic_logs" {
  bucket = aws_s3_bucket.traffic_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "traffic_logs" {
  bucket = aws_s3_bucket.traffic_logs.id

  rule {
    id     = "expire-cloudfront-access-logs"
    status = "Enabled"

    filter {}

    expiration {
      days = var.retention_days
    }
  }
}

data "aws_iam_policy_document" "traffic_log_delivery" {
  statement {
    sid    = "AWSLogDeliveryAclCheck"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["delivery.logs.amazonaws.com"]
    }

    actions   = ["s3:GetBucketAcl", "s3:ListBucket"]
    resources = [aws_s3_bucket.traffic_logs.arn]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [var.expected_account_id]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = [local.logs_service_arn]
    }
  }

  statement {
    sid    = "AWSLogDeliveryWrite"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["delivery.logs.amazonaws.com"]
    }

    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.traffic_logs.arn}/AWSLogs/${var.expected_account_id}/*"]

    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-acl"
      values   = ["bucket-owner-full-control"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [var.expected_account_id]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = [local.logs_service_arn]
    }
  }
}

resource "aws_s3_bucket_policy" "traffic_logs" {
  bucket = aws_s3_bucket.traffic_logs.id
  policy = data.aws_iam_policy_document.traffic_log_delivery.json
}

# Standard logging v2 attaches to the existing distribution through CloudWatch
# delivery resources. This module never owns or updates the distribution.
resource "aws_cloudwatch_log_delivery_source" "cloudfront" {
  name         = local.delivery_source_name
  log_type     = "ACCESS_LOGS"
  resource_arn = local.distribution_arn
}

resource "aws_cloudwatch_log_delivery_destination" "s3" {
  name          = "${local.delivery_source_name}-s3"
  output_format = "json"

  delivery_destination_configuration {
    destination_resource_arn = aws_s3_bucket.traffic_logs.arn
  }
}

resource "aws_cloudwatch_log_delivery" "cloudfront_to_s3" {
  delivery_source_name     = aws_cloudwatch_log_delivery_source.cloudfront.name
  delivery_destination_arn = aws_cloudwatch_log_delivery_destination.s3.arn

  # These fields answer traffic questions without storing viewer IP addresses,
  # cookies, query strings, forwarded headers, or request bodies.
  record_fields = [
    "date",
    "time",
    "x-edge-location",
    "sc-bytes",
    "cs-method",
    "cs(Host)",
    "cs-uri-stem",
    "sc-status",
    "cs(Referer)",
    "cs(User-Agent)",
    "x-edge-result-type",
    "x-edge-request-id",
    "cs-protocol",
    "time-taken",
    "ssl-protocol",
    "x-edge-response-result-type",
    "x-edge-detailed-result-type",
    "sc-content-type",
    "sc-content-len",
    "c-country",
    "cache-behavior-path-pattern",
  ]

  s3_delivery_configuration {
    enable_hive_compatible_path = false
    suffix_path                 = "cloudfront/{distributionid}/{yyyy}/{MM}/{dd}/{HH}"
  }

  depends_on = [
    aws_s3_bucket_ownership_controls.traffic_logs,
    aws_s3_bucket_policy.traffic_logs,
  ]
}
