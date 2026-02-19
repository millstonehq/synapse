---
id: RUNBOOK-061
type: runbook
title: Customer Portal Static Asset 404 Runbook
status: approved
owner: On-Call Engineer
created: '2024-02-08T07:00:09.566Z'
updated: '2025-01-27T19:02:52.078Z'
tags:
  - runbook
  - customer-portal
summary: Customer Portal Static Asset 404 Runbook
example: true
---

## Service

- **System**: [[SYSTEM-041|Customer Portal]]
- **Owner team**: Customer Portal Engineering
- **On-call rotation**: PagerDuty schedule "portal-oncall"
- **Slack channel**: #customer-portal-incidents
- **Runtime**: Next.js / CloudFront CDN / S3 static hosting

## Alerts

- `portal_static_404_rate_high` - Static asset 404 rate exceeds 1% of static requests for 3 minutes
- `portal_js_bundle_404` - Core JavaScript bundle returning 404 (critical - renders portal blank)
- `portal_css_404` - Core CSS file returning 404 (high - renders portal unstyled)
- `portal_image_404_rate_high` - Image asset 404 rate exceeds 5% for 5 minutes

## Diagnosis Steps

1. **Identify the affected assets** - Filter CDN access logs for 404 responses on static asset paths (`/_next/static/`); list the specific file hashes or paths that are missing.
2. **Check S3 bucket contents** - Navigate to the S3 static assets bucket and verify the affected asset paths exist; if they don't, the deploy did not upload them correctly.
3. **Correlate with recent deployment** - Check #customer-portal-deployments for the most recent deploy; a deployment that failed mid-asset-upload is the most common cause of missing static files.
4. **Check browser cache** - If reports are from a small subset of users, the issue may be stale browser cache pointing to old asset hashes from a previous build; this is less likely to trigger monitoring alerts.
5. **Check CloudFront invalidation history** - Verify whether a recent invalidation may have evicted assets that were not yet re-uploaded from the new build.

## Remediation Steps

1. **If S3 is missing the assets (incomplete deploy)**: Re-run the asset upload step of the portal deployment pipeline for the current build; verify all `/_next/static/` files are uploaded before checking CDN.
2. **If the deploy was successful but CDN has stale entries**: Create a targeted CDN invalidation for the affected asset paths; do not invalidate the entire distribution unless all static assets are affected.
3. **If the JavaScript bundle is 404ing (portal is blank)**: This is a P1 incident; immediately roll back the portal to the previous stable deployment to restore service, then investigate.
4. **If missing assets are from a previous build (old deployment)**: These 404s are expected as browser caches eventually request old hashes that no longer exist; no action is needed unless the rate is unusually high.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 5 min | Determine if JS bundle is affected; if yes, immediately escalate to P1 |
| 15 min | If not resolved: page Portal Tech Lead |
| 30 min | Engineering Manager paged; status page update if portal is visibly broken |
| 60 min | If not resolved: initiate major incident process |

## Dashboards

- [Portal CDN Overview](https://grafana.example.com/d/portal-cdn-overview) - Static asset 404 rate, cache hit ratio
- [S3 Asset Bucket](https://cloudwatch.example.com/portal-s3) - Upload events, object count, 4xx responses
- [Portal Web Vitals](https://grafana.example.com/d/portal-web-vitals) - LCP, FID, CLS (degraded if JS/CSS is 404ing)
- [Portal Error Tracking](https://sentry.example.com/portal) - Frontend JS errors from missing chunk loads
