# One-time adoption of the distribution and alias records from the Terraform 0.11 stacks
# (removed from their state with `terraform state rm`). Import blocks are no-ops once the
# resources are in state.

import {
  to = aws_cloudfront_distribution.site
  id = var.distribution_id
}

import {
  for_each = toset(["A", "AAAA"])
  to       = aws_route53_record.alias[each.key]
  id       = "${var.dns_zone_id}_${var.hostname}_${each.key}"
}
