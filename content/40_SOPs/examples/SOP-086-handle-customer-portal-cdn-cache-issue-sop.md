---
id: SOP-086
type: sop
title: Handle Customer Portal CDN Cache Issue SOP
status: accepted
owner: SRE Lead
created: '2025-07-13T22:32:39.996Z'
updated: '2025-08-11T12:14:26.887Z'
tags:
  - sop
  - customer-portal
summary: Handle Customer Portal CDN Cache Issue SOP
related_process: PROCESS-052
related_systems:
  - SYSTEM-043
example: true
---

## Preconditions

- A CDN cache issue has been reported (stale assets, wrong content served, cache miss spike, or cache poisoning suspicion)
- The affected CDN distribution and origin configuration are known
- On-call engineer has opened an investigation ticket and posted in #customer-portal-incidents
- Read access to CDN analytics dashboard is available

## Materials/Access

- Access to CDN management console (CloudFront or equivalent) with invalidation permissions
- Access to Grafana portal CDN metrics dashboard
- CDN distribution ID and origin domain
- Access to #customer-portal-incidents Slack channel

## Procedure

1. Post in #customer-portal-incidents: "Investigating CDN cache issue. Ticket: [TICKET-ID]. Symptoms: [stale assets / cache miss spike / other]."
2. Open the CDN analytics dashboard and identify the affected distribution; check cache hit ratio and origin request volume over the last 30 minutes.
3. If cache hit ratio has dropped sharply, check whether a portal deployment or manual invalidation in the past hour could explain the miss spike (expected behavior post-deploy).
4. If stale content is being served, identify the affected asset paths by comparing the served asset hash against the expected hash in the deployment manifest.
5. For stale static assets (JS, CSS, images): create a targeted CDN invalidation for the affected paths; avoid wildcard invalidation unless the scope is truly portal-wide.
6. Submit the invalidation and monitor the CDN console for completion (typically 2-5 minutes for CloudFront).
7. Verify the correct asset version is now served by fetching the affected asset directly and checking its `ETag` or `Last-Modified` header against the expected value.
8. If the issue is a cache poisoning suspicion (incorrect content for different users), escalate immediately to Security Lead and block the affected distribution while investigating.
9. Post in #customer-portal-incidents: "CDN cache issue resolved. Invalidation complete. [Affected paths]. Normal cache hit ratio restored."

## Validation

- CDN analytics show cache hit ratio returning to normal baseline (typically >85%)
- Affected assets are returning the correct version (verified by hash or version header)
- No customer reports of stale content in the 10 minutes following invalidation
- Grafana portal dashboard shows no residual error rate increase from origin overload

## Rollback

1. If a CDN configuration change caused the issue, revert the change in the CDN console to the previous configuration version.
2. If origin cache headers were changed and caused over-caching, revert the `Cache-Control` headers in the portal's server configuration and redeploy.
3. Verify cache behavior normalizes after the revert by monitoring cache hit ratio for 15 minutes.
4. Document the root cause and configuration change in the investigation ticket.
