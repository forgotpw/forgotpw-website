# Rosa marketing website

Static marketing website for [Rosa.bot](https://www.rosa.bot), formerly ForgotPW. Plain HTML, CSS, and a small script; no build step or package installation is required. Product direction is in the private `forgotpw/product` repository.

## Local preview

```sh
python3 -m http.server 8794 --bind 127.0.0.1 --directory src
```

Open [the local preview](http://127.0.0.1:8794). Check the homepage and `privacy.html`, narrow mobile layouts, menu open/close, FAQ disclosures, and the SMS/contact links. The phone illustration is an example conversation, not a live credential interface. Do not submit real passwords while reviewing the marketing site.

The homepage uses `src/css/rosa.css` and `src/scripts/rosa.js`. The original Rosa logo is retained. The existing analytics/ad identifiers and SMS conversion events are preserved on the homepage. The published privacy policy wording and effective date are retained with updated layout/navigation; it still contains legacy ForgotPW references and needs a separate policy review before a broader relaunch.

## Hosting and deployment

Rosa already uses S3 static files behind CloudFront, matching the VillageMetrics hosting model. The deployment workflow reuses those existing resources; it does not apply the legacy Terraform configuration or migrate infrastructure.

Verified with AWS read-only queries on September 10, 2026:

| Environment | AWS profile | AWS account | S3 bucket / website | CloudFront distribution |
| --- | --- | --- | --- | --- |
| Dev | `csdev` | `478543871670` | `www-dev.rosa.bot` | `E1FOKZO6RWD12W` |
| Prod | `csprod` | `162109821699` | `www.rosa.bot` | `E2IS3O9VPVJFGQ` |

Pushes to `develop` deploy to the development site. Pushes to the production branch, `master`, deploy to production after the protected `production` GitHub Environment is approved. The workflow authenticates to AWS through GitHub OIDC; it does not use long-lived AWS keys. The existing CommerceSong roles already trust repositories owned by `forgotpw`:

- Development: `arn:aws:iam::478543871670:role/github-actions-deploy-dev`
- Production: `arn:aws:iam::162109821699:role/github-actions-deploy-prod`

The workflow calls `deploy.sh`, so automated and manual deployments share the same safeguards. The script checks the account, required local files, and CloudFront origin before proceeding. It defaults to a read-only upload preview. An explicit `--apply` uploads assets first, HTML last, preserves the vCard URLs, and waits for CloudFront invalidation. It never empties the bucket or deletes existing media. Obsolete unreferenced files can be cleaned up separately after review.

`master` remains the production/default branch for now. Keeping the existing branch avoids combining a default-branch migration with the first automated release. The release path is `develop` -> `master`; migrating to `main` can be handled separately after the pipeline is proven.

### One-time GitHub setup

The public `forgotpw` repository inherits the organization-level `AWS_ACCOUNT_ID_DEV` and `AWS_ACCOUNT_ID_PROD` Actions secrets. These GitHub Environments are configured:

| Environment | Allowed branch | Protection |
| --- | --- | --- |
| `development` | `develop` | No approval required |
| `production` | `master` | Required reviewer; self-review allowed for a solo release |

The environment branch rules are defense in depth; the workflow also maps each branch to a fixed AWS account, bucket, and CloudFront distribution.

### Automated release

1. Push or merge to `develop` and verify the development deployment at [www-dev.rosa.bot](https://www-dev.rosa.bot).
2. Merge `develop` into `master`.
3. Approve the pending `production` environment deployment in GitHub Actions.
4. Verify [www.rosa.bot](https://www.rosa.bot) after the workflow completes.

### Manual recovery deployment

Routine releases must use GitHub Actions. `deploy.sh` remains available for reviewed recovery use when CI/CD is unavailable.

### Development

```sh
export AWS_ENV=dev
export AWS_PROFILE=csdev
./deploy.sh --dry-run
# Recovery only, after reviewing the preview:
./deploy.sh --apply
```

### Production

```sh
export AWS_ENV=prod
export AWS_PROFILE=csprod
./deploy.sh --dry-run
# Recovery only, after reviewing the site and authorizing publication:
./deploy.sh --apply
```

Use the normal AWS SSO login for the chosen profile if its session has expired. The old `fpwdev`/`fpwprod` profiles and `iam-starter` wrapper are no longer the documented deployment path. Do not apply the legacy infrastructure repository wholesale merely to publish a website update.

## Visitor tracking and social sharing

CloudFront standard logging v2 stores privacy-minimized access logs in a separate
private S3 bucket in each AWS account. The narrow Terraform module attaches to
the existing distributions without taking ownership of them. A local script
summarizes requests, approximate browser page views, referrers, user agents, and
daily trends. The homepage and privacy page also publish canonical Open Graph and
Twitter Card metadata with a dedicated 1200 x 630 social image. See
[`docs/website-visitor-tracking.md`](docs/website-visitor-tracking.md) for the
architecture, privacy limits, costs, retrieval commands, and release checks.

## Explainer video

The old YouTube embed (`x1QAvQasiZg`) is unavailable and has been removed. Doug confirmed the recovered original. The homepage now uses a local MP4 source, ready to be delivered with the site.

VillageMetrics uses a native HTML `<video>` with controls, `playsInline`, a poster, `preload="none"`, and a progressive-download MP4 served by S3/CloudFront (`assets.villagemetrics.com/videos/homepage-demo.mp4`). Use the same delivery method here. Rosa can initially serve `/videos/rosa-explainer-v1.mp4` from its existing website bucket and CloudFront distribution, without a new domain or a new hosting dependency. A separate `assets.rosa.bot` distribution is unnecessary for the first video.

VillageMetrics tracks its 48 MB MP4 in its `static-assets` repository. Rosa's approximately 16.5 MB MP4 is also small enough to keep in ordinary Git. The website-ready copy is tracked under `src/videos/`, so a fresh checkout contains all required media and the manual deployment uploads it with the website. A separate unmodified master is retained locally in `../recovered-media/` and remains available in Google Drive.

The player uses native controls, `playsinline`, `preload="none"`, a poster, and captions. It never autoplays. The confirmed original is `Rosa Try 2 Fiverr.mp4` from Google Drive (file `1fOPslsVcoo8aujPtXxo1RIficPnchEBX`).

The website cut removes the obsolete Alexa promotion at source timestamps **01:43.500–02:05.200**. The original is unchanged. English captions were transcribed locally and corrected against the source script and visible password examples.
