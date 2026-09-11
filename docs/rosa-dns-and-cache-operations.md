# Rosa apex DNS, HTTPS redirect and deployment caching

## Ownership and diagnosis

Checked September 11, 2026 UTC:

- EnCirca holds the registration, active through May 4, 2027. No registrar change is needed.
- The authoritative parent zone is `ZI3OYIPDF3C7O` in management account
  `775893492659` (`AWS_PROFILE=csmaster`). Its four nameservers match registration:
  `ns-1289.awsdns-33.org`, `ns-318.awsdns-39.com`,
  `ns-1897.awsdns-45.co.uk`, `ns-843.awsdns-41.net`.
- The old apex A alias targets `rosa.bot.s3-website-us-east-1.amazonaws.com`
  with alias zone `Z3AQBSTGFYJSTF`. Authoritative DNS returned NOERROR with no
  address. The underlying management-account bucket exists and is configured to
  redirect to `https://www.rosa.bot`; S3 website hosting cannot terminate HTTPS.
- Production `www` is a separate delegated zone in account `162109821699`
  (`csprod`). Its existing CloudFront distribution is `E2IS3O9VPVJFGQ`,
  `dtlkaanpfcwi0.cloudfront.net`. Its existing certificate covers only `www.rosa.bot`.
- Prior to the September 10 redesign release, deployment supplied neither
  Cache-Control nor CloudFront invalidation. Old browser copies of HTML could be
  treated as fresh using heuristic caching. An in-app browser still displayed the
  legacy page while ordinary Chrome and all six compressed/uncompressed GETs of
  `/`, `/index.html`, and `/privacy.html` returned the redesign. This supports
  retained browser caching; the original visitor's cache headers were not captured.
  No service-worker registration exists in the site code.
- The current website distributions have MinTTL=0, DefaultTTL=300, MaxTTL=3600.
  HTML already used `no-cache` and the redesign invalidation completed. The
  remaining future-deployment risk was stable asset URLs with one-hour freshness.

## Terraform and release ownership

`terraform/apex-redirect` owns only the new ACM certificate, its validation wait,
CloudFront Function and dedicated redirect distribution. State is at
`s3://terraform-state-ACCOUNT/rosa-website-apex-redirect/terraform.tfstate`, using
the existing account-specific DynamoDB lock table. GitHub Actions applies the saved
plan through the existing deployment roles; production retains its approval gate.
The provider permits only the configured account and uses us-east-1 for ACM.

Development manages its validation CNAME and redirect A/AAAA aliases in
`www-dev.rosa.bot` zone `Z25H8GAU4QTOBV` in account `478543871670` (`csdev`).
Its hostname is `redirect.www-dev.rosa.bot`, pointing to `https://www-dev.rosa.bot`.
This exercises certificate issuance, real DNS, TLS and the same edge function
before production promotion.

Production parent DNS lives in the separate management account. The website
deployment role has no access there. Its records are administered using the
authorized management-account DNS change, while ACM and CloudFront remain managed
by Terraform in production. Keep the validation CNAME for automatic renewal.
No new cross-account IAM access is required.

Do not apply the old `terraform/dev` or `terraform/prod` website configuration, or
the legacy `forgotpw-infrastructure/terraform/master` configuration as part of a
website release. The latter contains the obsolete S3 apex alias; any future
revival/migration must reconcile that resource with the live CloudFront target.

## First production setup

1. Review the development deployment, then promote to the existing production
   branch and approve its protected GitHub environment.
2. Terraform requests the `rosa.bot` certificate. During the first validation wait,
   read its DNS validation name/value from ACM using `csprod` (the same values are
   the module's `validation_record` output). In `csmaster`, compare the current
   parent-zone records and add that exact CNAME with TTL 300. Certificate validation
   times out after 15 minutes with a visible failure if the record is absent;
   rerun the failed workflow after correcting DNS rather than bypassing validation.
3. Wait for certificate issuance and the redirect distribution to be fully deployed.
   Inspect its aliases, issued certificate coverage and `distribution_domain_name`
   output before directing traffic to it.
4. In zone `ZI3OYIPDF3C7O`, replace only the apex A alias and add the apex AAAA alias
   to that new distribution, using CloudFront alias zone `Z2FDTNDATAQYW2` and
   `EvaluateTargetHealth=false`. Preserve MX, TXT, NS, SOA and all subdomain
   delegations. Preserve an exact pre-change record snapshot for comparison.
5. Wait for Route 53 INSYNC, then verify authoritative DNS, public resolvers and
   TLS. Existing negative answers may remain cached for the observed 900-second
   negative-cache TTL.

For both HTTP and HTTPS, `/` must return 301 to `https://www.rosa.bot/`, and
`/privacy.html?utm_source=dns-check&tag=a&tag=b%26c` must retain its path and query
at the canonical host. Unknown paths redirect to the same path and then return the
website's existing 404. The function uses a fixed destination rather than the
request's Host header. No browser JavaScript redirect is involved.

## Cache behavior and checks

`prepare_site.py` copies the source tree and adds SHA-256-based filenames for the
assets listed in `VERSIONED_ASSETS`. It updates relative HTML references and
absolute social-image URLs, preserving canonical URLs, sitemap, schema and robots
policies. Add newly introduced mutable page assets to that list. Files remain in
their original directories, so CSS relative paths retain their directory context;
new CSS asset dependencies also need explicit versioned references.

Unchanged files keep the same content-based URL across releases. Original URLs
are retained for compatibility; old versioned objects are never deleted by deploy.
Assets retain `public,max-age=3600`. HTML uses
`no-cache,max-age=0,must-revalidate`, and existing vCard URLs retain `no-cache`.
Assets upload before HTML, and the job waits for the all-path invalidation.

Validate the actual prepared development/production artifact against ordinary live
URLs without cache-busting query strings. Compare root/index/privacy bytes, robots
and sitemap, plus every referenced versioned asset; inspect HTML Cache-Control.
Check browser navigation to the ordinary root and privacy links. Local focused
tests cover source preservation, robots policy, canonical links, changed-asset
versions and redirect handling; the real development deployment proves the AWS
boundaries that local tests cannot.

CloudFront invalidation cannot clear a browser's already-fresh historical copy.
Future server headers cannot retroactively change those stored headers. Such a
visitor may still need one refresh or cache expiry; subsequent navigations receive
the revalidation policy and new asset URLs. Already-open pages do not update
themselves automatically.

References: [AWS cache invalidation and browser caches](https://aws.amazon.com/blogs/networking-and-content-delivery/host-single-page-applications-spa-with-tiered-ttls-on-cloudfront-and-s3/),
[CloudFront file versioning](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/UpdatingExistingObjects.html),
[CloudFront Function events](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/functions-event-structure.html).
