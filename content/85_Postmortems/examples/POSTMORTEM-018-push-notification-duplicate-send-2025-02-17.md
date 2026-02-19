---
id: POSTMORTEM-018
type: postmortem
title: Push Notification Duplicate Send 2025-02-17
status: proposed
owner: Incident Commander
created: '2025-01-14T22:57:14.094Z'
updated: '2026-07-24T07:50:06.922Z'
tags:
  - postmortem
  - notification-service
summary: Push Notification Duplicate Send 2025-02-17
incident_number: INC-359
severity: SEV-2
incident_date: '2024-04-12'
detection_time: '2024-05-13T08:47:17.457Z'
resolution_time: '2024-06-21T21:20:03.214Z'
total_duration: ~15 minutes
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-037
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On February 17, 2025, a 15-minute window of duplicate push notification sends affected approximately 28,000 users who each received 2 copies of the same notification. The root cause was a race condition in the Push Notification Gateway's idempotency check during a brief Redis unavailability event. When Redis was unavailable, the gateway fell back to processing requests without deduplication, allowing the same notification job to be processed twice by different consumer pods.

The issue was detected via user complaints and a spike in FCM send volume, and was resolved when Redis recovered. No data was lost. The incident resulted in the addition of a mandatory Redis health check before the gateway processes jobs and a configurable fail-closed behavior when Redis is unavailable.

## Timeline

- **11:03** - Redis experiences a brief leadership election during a rolling restart of the Redis cluster
- **11:03** - Push Notification Gateway consumers unable to connect to Redis for idempotency checks
- **11:03** - Gateway falls back to processing without deduplication (fail-open behavior)
- **11:05** - Two consumer pods process the same job from the queue in parallel (deduplication would have prevented this)
- **11:07** - User complaints begin arriving in support channel
- **11:09** - On-call notices spike in FCM send volume: 2x expected rate
- **11:12** - On-call correlates FCM spike with Redis unavailability in dashboards
- **11:14** - Redis leadership election completes; Redis available again
- **11:18** - Duplicate sends cease as deduplication resumes
- **11:32** - Incident formally closed after 14-minute stable observation window

## Impact

- **Duration**: 15 minutes (11:03 - 11:18 UTC)
- **Users affected**: ~28,000 users received 1 duplicate push notification each
- **Provider cost impact**: ~$280 in excess FCM charges for duplicate sends
- **Support tickets**: 47 user complaints received within 1 hour
- **SLA impact**: None — platform remained operational; this was a quality issue, not an availability issue

## Root Cause Analysis

1. **Fail-open deduplication**: The idempotency check in the Push Notification Gateway was designed to be fail-open — if Redis was unavailable, processing continued without deduplication. This was an intentional design choice to avoid blocking notifications during Redis outages, but the tradeoff (duplicate sends) was not adequately documented or communicated.

2. **Redis rolling restart without quorum protection**: The Redis cluster rolling restart was performed without ensuring that a majority of nodes were healthy before proceeding, causing a leadership election that created a 15-minute unavailability window.

## Resolution

1. Redis leadership election completed naturally, restoring deduplication
2. Monitoring confirmed no further duplicate sends after Redis recovery
3. Issued user-facing acknowledgment in app for affected users

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add fail-closed option for push idempotency (queue job rather than process without dedup) | Notification Engineering | P1 | 2025-02-24 | Completed |
| Add Redis health check to gateway startup and pre-process gate | Notification Engineering | P1 | 2025-02-24 | Completed |
| Update Redis rolling restart procedure to enforce quorum health check | SRE | P2 | 2025-02-28 | Completed |
| Add duplicate-send-rate alert (sends per user per event > 1 in 5 min) | SRE | P2 | 2025-03-07 | Pending |

## Lessons Learned

- **What went well**: Detection was fast — the FCM send volume spike was visible within 6 minutes. Redis recovery was automatic, requiring no manual intervention.
- **What went poorly**: Fail-open behavior for deduplication was a hidden design decision that was not visible in the runbook or on-call documentation. On-call had no prior knowledge that Redis unavailability could cause duplicate sends.
- **What was lucky**: The Redis outage lasted only 15 minutes. A longer outage would have caused significantly more duplicates.
