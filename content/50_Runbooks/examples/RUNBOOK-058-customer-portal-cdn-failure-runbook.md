---
id: RUNBOOK-058
type: runbook
title: Customer Portal CDN Failure Runbook
status: draft
owner: On-Call Engineer
created: '2025-02-04T20:38:05.784Z'
updated: '2025-08-04T16:49:56.109Z'
tags:
  - runbook
  - customer-portal
summary: Customer Portal CDN Failure Runbook
example: true
---

## Service

- **System**: [[SYSTEM-041|Customer Portal]]
- **Owner team**: Customer Portal Engineering
- **On-call rotation**: PagerDuty schedule "portal-oncall"
- **Slack channel**: #customer-portal-incidents
- **Runtime**: CloudFront CDN / Next.js / Node.js 20 / PostgreSQL 15

## Alerts

- `portal_cdn_origin_error_rate_high` - CDN origin error rate exceeds 5% for 3 minutes
- `portal_cdn_cache_hit_ratio_low` - Cache hit ratio drops below 50% for 5 minutes
- `portal_static_asset_5xx` - Static asset requests returning 5xx for more than 1 minute
- `portal_ttfb_high` - Time to first byte exceeds 3 seconds at P95 for 5 minutes

## Diagnosis Steps

1. **Check CDN distribution status** - Open the CloudFront console and check the distribution status; look for any active CloudFront service health events in the AWS Health Dashboard that may explain a platform-level CDN outage.
2. **Check origin health** - Verify the portal origin servers are healthy by hitting the origin directly (bypassing CDN) using the health endpoint; if the origin is returning errors, the issue is upstream of the CDN.
3. **Check cache hit ratio** - In the CDN analytics dashboard, compare current cache hit ratio to the 7-day baseline; a sudden drop often indicates a recent deploy invalidated the cache or misconfigured cache headers are preventing caching.
4. **Inspect error logs** - Filter CloudFront access logs for 5xx responses; check the origin response time and status codes to distinguish CDN-level failures from origin failures.
5. **Check recent configuration changes** - Review the CDN distribution change history for recent behaviors, cache policies, or origin configuration changes that could explain the issue.

## Remediation Steps

1. **If CDN platform outage (AWS service event)**: Switch portal traffic to the backup CDN distribution or enable the maintenance page while the AWS outage resolves. Communicate via status page.
2. **If cache hit ratio collapsed after deploy**: The cold cache after a deployment is expected; it will self-heal as CloudFront warms up. If TTL settings are misconfigured, update `Cache-Control` headers in the portal server config and redeploy.
3. **If origin is unhealthy**: Redirect investigation to the portal application runbook; the CDN itself is functioning but cannot fix origin failures.
4. **If a specific CDN behavior or cache policy was misconfigured**: Revert the distribution configuration to the last known-good state using the CloudFront console's configuration history.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 10 min | Post initial assessment in #customer-portal-incidents |
| 20 min | If not resolved: escalate to Portal Tech Lead via PagerDuty |
| 30 min | If not resolved: Engineering Manager paged; status page update posted |
| 60 min | If not resolved: initiate major incident, escalate to AWS support if platform event |

## Dashboards

- [Portal CDN Overview](https://grafana.example.com/d/portal-cdn-overview) - Cache hit ratio, origin error rate, TTFB
- [Portal Origin Health](https://grafana.example.com/d/portal-origin) - Origin response times, error rates, pod health
- [CloudFront Access Logs](https://cloudwatch.example.com/portal-cf-logs) - Raw CDN access logs with status codes
- [Portal Performance](https://grafana.example.com/d/portal-perf) - LCP, TTFB, and Core Web Vitals trends
