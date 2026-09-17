# Rosa website visitor tracking

Rosa uses CloudFront standard logging v2 to retain basic website request data in
AWS. CloudFront is the correct source because it records viewer requests served
from the edge cache; S3 origin server logs would omit those cache hits.

The logging resources live in `terraform/visitor-logging/`. They attach to each
existing distribution through CloudWatch Logs delivery resources, so this module
does not import, update, or take Terraform ownership of either distribution.
The normal deployment workflow applies the narrow module before publishing site
content. Development and production use separate AWS accounts, Terraform state,
delivery resources, and buckets:

| Environment | Distribution | Log bucket | Retention |
| --- | --- | --- | --- |
| Dev | `E1FOKZO6RWD12W` | `rosa-website-traffic-logs-dev-478543871670` | 30 days |
| Prod | `E2IS3O9VPVJFGQ` | `rosa-website-traffic-logs-prod-162109821699` | 90 days |

The buckets block all public access, use S3-managed encryption, allow writes only
from the AWS log-delivery service in their own account, and are protected from
Terraform destroy. Logs are JSON and grouped by distribution and UTC date.

## Privacy boundaries

The selected fields cover timestamps, the requested hostname and path, response status and size,
referrer, user agent, country, TLS details, cache result, and timing. The delivery
does **not** record viewer IP addresses, cookies, the query string on the requested
Rosa URL, forwarded-for headers, or request bodies. Referrers are stored as sent by
the browser and can include a source site's query parameters; the reporting script
reduces them to hostnames. Rosa contact-form contents are not recorded in these
logs.

Without an IP address, cookie, or another visitor identifier, the data cannot
produce exact unique-visitor or session counts. The reporting script labels its
traffic measure as approximate browser page views: successful HTML GET requests
after a simple bot user-agent filter. Use that measure for directional trends,
not billing, attribution, or individual tracking. Raw user agents and referrers
can still be identifying in unusual cases; keep raw objects restricted and share
aggregates.

This adds no browser script, cookie, tracking pixel, or third-party analytics
dependency. Rosa's pre-existing Google Analytics, Google Ads, and Facebook Pixel
scripts are outside this AWS logging change and remain present on the homepage.

CloudFront can delay standard logs, occasionally by up to 24 hours, and delivery
is best effort. AWS does not charge extra for CloudFront standard-log delivery to
S3. Normal S3 storage, PUT, LIST, and GET charges still apply. At Rosa's expected
traffic and retention, the practical cost should be measured in cents per month.
JSON avoids the additional conversion charge associated with Parquet output.

## Retrieve a summary

Export the profile explicitly, then run the lightweight reporting script. It
uses the AWS CLI credential chain and refuses to read if the authenticated account
does not match the selected environment.

```bash
export AWS_PROFILE=csprod
python3 scripts/summarize_traffic.py --env prod --days 7
```

For development traffic:

```bash
export AWS_PROFILE=csdev
python3 scripts/summarize_traffic.py --env dev --days 7
```

To confirm that delivery has started without downloading raw records:

```bash
export AWS_PROFILE=csprod
aws s3 ls s3://rosa-website-traffic-logs-prod-162109821699/ --recursive --summarize
```

AWS says delivery becomes reliable about four hours after logging is enabled.
The report may therefore be empty immediately after the first deployment.

## Social sharing checks

The homepage and privacy page include canonical, Open Graph, and Twitter Card
metadata. The shared 1200 x 630 PNG keeps the Rosa mark and headline inside the
center of the card so wide and compact link previews remain legible.

After a development deployment, inspect the HTML and image directly. Social
services fetch the production URLs embedded in metadata, so platform validation
must wait for the approved production release. After release, check the public
URL in [LinkedIn Post Inspector](https://www.linkedin.com/post-inspector/) and
[Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/).
iMessage has no public debugger; send the production link in a new conversation
after deployment. Existing shares may retain cached previews.

## References

- [CloudFront standard logging v2](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/standard-logging.html)
- [CloudFront standard log fields](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/standard-logs-reference.html)
- [CloudWatch log delivery to S3](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AWS-logs-infrastructure-S3.html)
