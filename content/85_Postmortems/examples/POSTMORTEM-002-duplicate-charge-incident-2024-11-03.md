---
id: POSTMORTEM-002
type: postmortem
title: Duplicate Charge Incident 2024-11-03
status: approved
owner: Incident Commander
created: '2024-08-17T04:50:55.851Z'
updated: '2025-03-05T05:27:04.455Z'
tags:
  - postmortem
  - payment-processing
summary: Duplicate Charge Incident 2024-11-03
incident_number: INC-73
severity: SEV-4
incident_date: '2025-02-21'
detection_time: '2024-06-29T23:40:55.238Z'
resolution_time: '2026-05-10T01:30:34.117Z'
total_duration: ~1 hour
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-003
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On November 3, 2024, 23 customers were charged twice for the same purchase due to a race condition in the idempotency enforcement logic introduced in a deploy earlier that day. A code defect caused idempotency key lookups to use an eventually-consistent Redis read replica rather than the primary, allowing concurrent retries from clients to bypass deduplication and trigger double captures against Stripe.

All 23 duplicate charges were identified within 4 hours and fully refunded by end of day. Total duplicate charge value was $4,847. No data integrity issues persisted after remediation.

## Timeline

- **09:14** - Deploy 3.4.2 ships, including a Redis configuration change that inadvertently routes idempotency key reads to a read replica.
- **11:30** - First customer support ticket about a duplicate charge received.
- **12:15** - Second and third duplicate charge tickets received. Support escalates to Payments team.
- **12:22** - On-call engineer begins investigation. Reviews deploy history — 3.4.2 deploy flagged as potentially relevant.
- **12:40** - Engineer identifies the Redis read-replica routing change in the deploy diff.
- **12:55** - Hotfix prepared routing idempotency reads to Redis primary. Deploy approved.
- **13:10** - Hotfix deployed. Duplicate charges cease.
- **13:30** - Full audit query run to identify all affected transactions. 23 duplicate charges found.
- **15:00** - All 23 refunds initiated via Stripe API.
- **17:45** - All refunds confirmed by Stripe. Incident closed.

## Impact

- **Duplicate charges**: 23 customers charged twice
- **Total value duplicated**: $4,847
- **Refund status**: 100% refunded by end of day
- **Customer communication**: Personalised emails sent to all 23 affected customers with apology and refund confirmation
- **SLA impact**: No availability SLA breach; incident classified as data quality incident

## Root Cause Analysis

1. **Idempotency key reads routed to Redis read replica**: The deploy introduced a Redis client configuration change that sent reads to a replica node rather than the primary. Redis replication is asynchronous with a typical lag of 50–500ms. Under concurrent client retries, a newly written idempotency key was not yet visible on the replica, causing the duplicate check to return "not found" and allowing a second capture to proceed.

2. **No integration test for Redis replica lag**: The idempotency enforcement code had unit tests but no integration test covering the scenario where a key written in one request is not yet visible on subsequent reads due to replication lag.

## Resolution

1. Deployed hotfix routing idempotency key reads to Redis primary
2. Ran audit query to identify all transactions with duplicate capture events
3. Initiated and confirmed refunds for all 23 affected customers via Stripe API

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Fix Redis client configuration to always read idempotency keys from primary | Payments team | P1 | 2024-11-04 | Completed |
| Add integration test for idempotency under concurrent requests | Payments team | P1 | 2024-11-15 | Completed |
| Add automated duplicate charge detection alert | SRE | P2 | 2024-11-22 | Completed |
| Add Redis configuration to pre-deploy checklist | Platform | P2 | 2024-12-01 | Completed |
| Review all other Redis read paths for similar replica routing issues | DBA | P3 | 2024-12-15 | Completed |

## Lessons Learned

- **What went well**: Customer support escalation was prompt. Refund process was executed quickly and 100% of affected customers were made whole by end of day.
- **What went poorly**: The Redis configuration change was not flagged as high-risk in the deploy review. The impact of read-replica lag on idempotency semantics was not considered during the code review.
- **What was lucky**: The duplicate charge rate was low (23 transactions out of ~45,000 that day) because most clients do not retry aggressively. A more aggressive retry strategy would have caused significantly more duplicates.
