#!/usr/bin/env bash
set -euo pipefail

# Website deployment entrypoint for local use and GitHub Actions.
# Preview is the default; --apply uploads files and invalidates CloudFront.
mode="${1:---dry-run}"
if [[ $# -gt 1 || ( "$mode" != "--dry-run" && "$mode" != "--apply" ) ]]; then
  echo "Usage: AWS_ENV=dev|prod [AWS_PROFILE=csdev|csprod] ./deploy.sh [--dry-run|--apply]" >&2
  exit 1
fi
: "${AWS_ENV:?Set AWS_ENV to dev or prod}"
case "$AWS_ENV" in
  dev) bucket="www-dev.rosa.bot"; expected_account="478543871670"; distribution="E1FOKZO6RWD12W" ;;
  prod) bucket="www.rosa.bot"; expected_account="162109821699"; distribution="E2IS3O9VPVJFGQ" ;;
  *) echo "AWS_ENV must be dev or prod" >&2; exit 1 ;;
esac
if [[ -n "${AWS_PROFILE:-}" && "${AWS_PROFILE:-}" != "cs${AWS_ENV}" ]]; then
  echo "Use AWS_PROFILE=cs${AWS_ENV} for AWS_ENV=${AWS_ENV}" >&2
  exit 1
fi
export AWS_PAGER=""
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
release_dir="$(mktemp -d)"
trap 'rm -rf "$release_dir"' EXIT
site_dir="$release_dir/site"
python3 "$repo_dir/scripts/prepare_site.py" --environment "$AWS_ENV" --output "$site_dir"
for required in index.html privacy.html robots.txt sitemap.xml rosa.vcf css/rosa.css scripts/rosa.js Images/rosa-logo.svg Images/rosa-social-card.png Images/rosa-explainer-poster.jpg videos/rosa-explainer-v1.mp4 videos/rosa-explainer-en.vtt; do
  [[ -s "$site_dir/$required" ]] || { echo "Missing site file: $required" >&2; exit 1; }
done
actual_account="$(aws sts get-caller-identity --query Account --output text)"
[[ "$actual_account" == "$expected_account" ]] || { echo "Wrong AWS account: $actual_account" >&2; exit 1; }
origin="$(aws cloudfront get-distribution --id "$distribution" --query 'Distribution.DistributionConfig.Origins.Items[0].DomainName' --output text)"
[[ "$origin" == "$bucket.s3.amazonaws.com" ]] || { echo "Unexpected CloudFront origin: $origin" >&2; exit 1; }
printf 'Target: %s (account %s), CloudFront %s, mode %s\n' "$bucket" "$actual_account" "$distribution" "$mode"
upload_s3() {
  if [[ "$mode" == "--apply" ]]; then
    aws s3 "$@"
  else
    aws s3 "$@" --dryrun
  fi
}
# Upload assets first and HTML last. Never empty the bucket or delete media.
upload_s3 sync "$site_dir/" "s3://$bucket/" --exclude '*.html' --exclude 'rosa.vcf' --cache-control 'public,max-age=3600'
upload_s3 cp "$site_dir/rosa.vcf" "s3://$bucket/rosa.vcf" --content-type text/vcard --content-disposition 'attachment; filename="rosa.vcf"' --cache-control no-cache
# Keep the historical trailing-period URL used in SMS messages.
upload_s3 cp "$site_dir/rosa.vcf" "s3://$bucket/rosa.vcf." --content-type text/vcard --content-disposition 'attachment; filename="rosa.vcf"' --cache-control no-cache
upload_s3 cp "$site_dir/" "s3://$bucket/" --recursive --exclude '*' --include '*.html' --cache-control no-cache
if [[ "$mode" == "--apply" ]]; then
  invalidation="$(aws cloudfront create-invalidation --distribution-id "$distribution" --paths '/*' --query Invalidation.Id --output text)"
  echo "Waiting for CloudFront invalidation $invalidation"
  aws cloudfront wait invalidation-completed --distribution-id "$distribution" --id "$invalidation"
  echo "Published: https://$bucket"
else
  echo "Preview complete. No objects changed and no invalidation submitted."
fi
