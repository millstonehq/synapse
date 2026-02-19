---
id: SOP-083
type: sop
title: Investigate Customer Portal Performance Issue SOP
status: approved
owner: SRE Lead
created: '2024-03-20T05:24:45.483Z'
updated: '2025-07-01T00:07:00.342Z'
tags:
  - sop
  - customer-portal
summary: Investigate Customer Portal Performance Issue SOP
related_process: PROCESS-052
related_systems:
  - SYSTEM-044
example: true
---

## Preconditions

- A performance issue has been reported by a customer or detected via monitoring alerts
- The issue is reproducible or confirmed by monitoring data (not an isolated one-off report)
- On-call engineer has acknowledged the alert and opened an investigation ticket

## Materials/Access

- Access to Grafana portal performance dashboard
- Access to Datadog APM traces for the portal API
- Access to CDN analytics (CloudFront or equivalent)
- Browser DevTools or WebPageTest for frontend performance profiling
- Access to the #customer-portal-incidents Slack channel

## Procedure

1. Post in #customer-portal-incidents: "Investigating portal performance issue. Ticket: [TICKET-ID]. Initial observation: [brief description]."
2. Open the Grafana portal dashboard and identify the affected metrics: check LCP/TTFB for frontend issues, or P95 API latency for backend issues.
3. Determine the time the degradation started; check #customer-portal-deployments for any deployments in the preceding 30 minutes.
4. If a recent deploy correlates with the degradation onset, initiate rollback per the deploy SOP and monitor recovery before further investigation.
5. If no deploy correlation, check Datadog APM for slow traces: filter by `service:customer-portal-api`, sort by duration, and identify the slowest endpoints.
6. For identified slow endpoints, drill into the trace waterfall to pinpoint the bottleneck: database query, external API call, or compute-heavy operation.
7. Check CDN analytics for cache hit ratio; a significant drop in cache hits may indicate a cache invalidation event causing origin load.
8. If the issue is frontend (high LCP/CLS), run a WebPageTest from the affected region and analyze the waterfall for blocking resources or slow asset delivery.
9. Document findings in the investigation ticket: affected component, root cause hypothesis, and recommended remediation.

## Validation

- Grafana shows affected metrics returning to within 10% of baseline after remediation
- No new performance alerts are firing
- Customer who reported the issue confirms the portal is responsive (if applicable)
- Investigation ticket is updated with root cause and remediation actions taken

## Rollback

1. If remediation actions (config change, query optimization) make performance worse, revert the change via the change management process.
2. Restore previous configuration values from the secrets manager or config store.
3. Verify metrics stabilize after the revert before closing the rollback action.
4. Re-open the investigation with the failed remediation attempt documented for context.
