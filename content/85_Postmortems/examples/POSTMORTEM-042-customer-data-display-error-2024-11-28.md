---
id: POSTMORTEM-042
type: postmortem
title: Customer Data Display Error 2024-11-28
status: approved
owner: Incident Commander
created: '2024-03-31T12:29:54.457Z'
updated: '2025-10-10T09:37:17.729Z'
tags:
  - postmortem
  - customer-portal
summary: Customer Data Display Error 2024-11-28
incident_number: INC-833
severity: SEV-2
incident_date: '2024-01-04'
detection_time: '2026-03-08T22:36:01.527Z'
resolution_time: '2026-06-30T11:14:24.915Z'
total_duration: ~15 minutes
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-090
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On November 28, 2024, the Customer Portal displayed incorrect account data to a subset of customers for approximately 15 minutes. A caching bug introduced in a November 27 deploy caused the preference service cache to return another customer's display name and notification settings when a cache key collision occurred under specific concurrent-login conditions. No sensitive financial or personal data was exposed beyond display name and notification preferences. A long-running analytics query locked several rows, causing application queries to queue up and exhaust the connection pool. The outage affected all payment processing, resulting in approximately $12,000 in delayed transactions. No data was lost.

The bug was detected at 14:22 UTC by a customer support ticket reporting an incorrect display name. The root cause was identified and the deploy was rolled back at 14:37 UTC. Total customer-visible duration was approximately 15 minutes.

## Timeline

- **14:20** - Customer submits support ticket reporting they see another customer's name in the portal header
- **14:22** - Support agent flags ticket as a data display issue and pages on-call
- **14:24** - On-call acknowledges; checks recent deploys — deploy from Nov 27 19:45 UTC identified as suspect
- **14:28** - Engineer reviews the Nov 27 deploy; identifies a cache key change in the preference service
- **14:33** - Root cause confirmed: cache key construction uses `customer_id` as a suffix but a refactor changed integer to string formatting, causing key collisions for IDs differing only by trailing zeros
- **14:37** - Nov 27 deploy rolled back; preference cache flushed
- **14:42** - Confirmed display names correct across test accounts
- **14:50** - Incident closed; 14 affected customer accounts identified for notification

## Impact

- **Duration**: ~15 minutes of customer-visible incorrect data (14:22 - 14:37 UTC)
- **Users affected**: 14 customer accounts saw another customer's display name and notification preference settings
- **Data exposed**: Display names and notification preferences only. No financial, authentication, or contact data was exposed.
- **SLA impact**: No SLA breach (service remained available; data accuracy incident)
- **Customer notifications**: 14 affected customers notified by email within 2 hours

## Root Cause Analysis

1. **Cache key collision from integer-to-string formatting change**: A refactor of the preference service changed `customer_id` from integer to string format in cache key construction. String `"10"` and `"100"` — previously distinct integers 10 and 100 — share no collision, but `"1000"` and `"10000"` collided when the key suffix was truncated to 4 characters.

2. **No integration test for cache key uniqueness**: The preference service had no test verifying that cache keys for different customer IDs never collide. The formatting change passed unit tests because tests used IDs 1, 2, 3 which have no collision.

## Resolution

1. Rolled back the November 27 deploy to restore previous cache key format
2. Flushed the preference service Redis cache to remove all potentially-affected entries
3. Verified correct data display across affected customer accounts
4. Notified 14 affected customers

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Fix cache key construction to use full customer_id without truncation | Preference Service team | P1 | 2024-12-02 | Completed |
| Add cache key collision integration test to preference service | Preference Service team | P1 | 2024-12-05 | Completed |
| Add data accuracy monitoring alert (cross-account data detection) | SRE | P2 | 2024-12-15 | In progress |
| Audit other services for similar integer-to-string cache key patterns | Engineering leads | P2 | 2024-12-20 | Pending |

## Lessons Learned

- **What went well**: Customer self-reported the issue within 2 minutes of the bug becoming active. Rollback was fast once root cause was identified.
- **What went poorly**: The cache key truncation bug was not caught by tests. No automated monitoring existed to detect cross-customer data leakage.
- **What was lucky**: The exposed data was limited to display name and notification preferences. The same bug in a different context could have exposed sensitive data.
