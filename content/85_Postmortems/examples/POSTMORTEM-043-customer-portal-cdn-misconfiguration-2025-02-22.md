---
id: POSTMORTEM-043
type: postmortem
title: Customer Portal CDN Misconfiguration 2025-02-22
status: approved
owner: On-Call Engineer
created: '2024-04-05T04:58:02.735Z'
updated: '2026-05-17T12:51:49.410Z'
tags:
  - postmortem
  - customer-portal
summary: Customer Portal CDN Misconfiguration 2025-02-22
incident_number: INC-834
severity: SEV-3
incident_date: '2024-09-11'
detection_time: '2025-03-30T07:11:20.647Z'
resolution_time: '2024-03-22T12:32:38.371Z'
total_duration: ~4 hours
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-088
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On February 22, 2025, a CDN configuration change intended to improve static asset caching for the Customer Portal inadvertently applied overly aggressive caching rules to API responses. GraphQL responses from the Customer API Gateway were cached at the CDN edge for 4 hours, causing customers to see stale data — including outdated notification counts, support ticket statuses, and preference settings — for approximately 4 hours.

The incident was detected at 11:05 UTC via customer support tickets and an anomaly in the notification engagement rate dropping to zero. Root cause was identified at 11:40 UTC and CDN cache was purged by 12:08 UTC, restoring live data.

## Timeline

- **09:30** - Platform engineer applies CDN cache rule change intended for `/static/*` but accidentally matching `/api/*` as well
- **09:32** - API responses begin being cached at CDN with 4-hour TTL
- **11:05** - On-call receives customer support ticket: "My support ticket status isn't updating"
- **11:10** - On-call checks API health; all pods healthy, error rate normal — response data looks stale but metrics show no errors
- **11:25** - Second wave of support tickets arrives; on-call escalates to portal tech lead
- **11:40** - Tech lead reviews CDN access logs; identifies API responses being served from edge cache
- **11:45** - Platform engineer identified as having made CDN config change at 09:30
- **11:50** - CDN cache purge for `/api/*` initiated
- **12:08** - CDN purge complete; live API responses confirmed
- **13:30** - Incident closed after 90-minute stable observation window

## Impact

- **Duration**: ~4 hours of stale data served (09:32 - 12:08 UTC)
- **Users affected**: All portal users who accessed API-driven content during the window
- **Data staleness**: Notification counts, support ticket statuses, preference settings — all stale by up to 4 hours
- **SLA impact**: No availability SLA breach (portal was up; data freshness not covered by current SLA)
- **Customer communications**: Status page updated at 11:50; 23 support tickets received

## Root Cause Analysis

1. **Overly broad CDN cache rule pattern**: The cache rule was written as `path: /` with `cache: 4h`, intended to target the Next.js static asset path `/static/`. The pattern matched all paths including `/api/*`, causing API responses to be cached.

2. **No CDN change review process**: CDN configuration changes were not subject to the standard change management review process. The change was applied directly without a second reviewer or a staging environment test.

## Resolution

1. Purged CDN cache for all `/api/*` paths
2. Applied corrected CDN rule scoped to `/static/*` only
3. Confirmed API responses are no longer cached at edge

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add CDN config changes to standard change management process | Engineering Manager | P1 | 2025-03-01 | Completed |
| Add `cache-control: no-store` header to all Customer API Gateway responses | Gateway team | P1 | 2025-03-01 | Completed |
| Add CDN cache-hit-rate alert for `/api/*` paths | SRE | P2 | 2025-03-08 | Completed |
| Document CDN configuration in portal runbook | Portal team | P3 | 2025-03-15 | In progress |

## Lessons Learned

- **What went well**: Multiple support tickets from customers enabled faster detection than monitoring alone would have provided.
- **What went poorly**: CDN changes were not in scope for change management review. A reviewer would have caught the overly broad pattern.
- **What was lucky**: The 4-hour cache TTL meant the issue would have self-resolved by 13:32 even without intervention. Worse: a permanent cache configuration could have caused indefinite staleness.
