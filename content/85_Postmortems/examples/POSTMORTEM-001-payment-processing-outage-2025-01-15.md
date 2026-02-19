---
id: POSTMORTEM-001
type: postmortem
title: Payment Processing Outage 2025-01-15
status: approved
owner: On-Call Engineer
created: '2025-09-13T19:58:23.120Z'
updated: '2026-12-19T16:22:31.409Z'
tags:
  - postmortem
  - payment-processing
summary: Payment Processing Outage 2025-01-15
incident_number: INC-72
severity: SEV-2
incident_date: '2024-10-24'
detection_time: '2024-04-17T14:38:04.244Z'
resolution_time: '2026-04-11T23:41:23.258Z'
total_duration: ~1 hour
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-004
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On January 15, 2025, the Payments API experienced an 84-minute outage caused by database connection pool exhaustion. A long-running analytics query ran directly against the production payments database, acquiring row-level locks that blocked application write transactions and eventually exhausted all available connections in the pool. The outage affected all payment processing, resulting in approximately $12,000 in delayed transactions. No data was lost.

The incident was detected by automated alerting at 14:23 UTC and resolved at 15:47 UTC when the long-running query was identified and terminated. A pod restart cleared the exhausted connection pool and service recovered to baseline within 15 minutes.

## Timeline

- **14:15** - Analytics team runs a large aggregate query against the production payments database
- **14:18** - Payment API response times begin increasing as queries queue behind row locks
- **14:23** - `payments_latency_p95_high` alert fires. On-call engineer acknowledges.
- **14:25** - On-call checks recent deploys — none in the last 24 hours. Rules out deploy cause.
- **14:30** - Error logs show `connection pool exhausted` errors. On-call attempts pod restart.
- **14:35** - Pod restart provides 30 seconds of relief before pool exhausts again. Root cause still active.
- **14:42** - On-call escalates to Payments tech lead per runbook escalation timeline.
- **14:50** - Tech lead queries `pg_stat_activity` and identifies a 35-minute-old analytics query holding row locks.
- **14:52** - Long-running query terminated via `pg_terminate_backend()`.
- **14:55** - Connection pool begins draining. Response times improving.
- **15:00** - Full pod restart clears stale connections. Error rate drops to baseline.
- **15:15** - Metrics stable. On-call continues monitoring.
- **15:47** - Incident formally closed after 30-minute stable observation window.

## Impact

- **Duration**: 84 minutes (14:23 - 15:47 UTC)
- **Transactions impacted**: ~340 payment attempts failed with 503 errors; all retried successfully after resolution
- **Revenue impact**: Approximately $12,000 in delayed payment processing (no permanent revenue loss)
- **SLA impact**: Monthly uptime dropped to 99.85%, breaching the 99.9% SLA target
- **Customer communications**: Status page updated at 14:30, customer support notified at 14:35

## Root Cause Analysis

1. **No query isolation between analytics and application workloads**: The analytics team ran a long-running aggregate query directly against the production database rather than a read replica. This query acquired row-level locks that blocked application write transactions. There was no documented policy or technical enforcement preventing analytics queries from hitting the production primary.

2. **Connection pool lacked defensive configuration**: The Payments API connection pool had no maximum wait time configured. When connections were blocked by locks, new requests queued indefinitely rather than failing fast with a clear error, eventually exhausting all 100 available connections.

## Resolution

1. Identified and terminated the long-running analytics query via `pg_terminate_backend()`
2. Restarted all Payments API pods to clear the exhausted connection pool state
3. Monitored error rate and latency for 30 minutes to confirm stable recovery

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add `statement_timeout=30s` to application database role | DBA | P1 | 2025-01-20 | Completed |
| Configure connection pool `maxWaitTime=5s` (fail fast) | Payments team | P1 | 2025-01-20 | Completed |
| Route analytics queries to read replica | Analytics team | P1 | 2025-01-27 | Completed |
| Add `payments_db_connection_pool_exhausted` alert at 80% utilisation | SRE | P2 | 2025-02-01 | Completed |
| Update runbook with `pg_stat_activity` diagnosis steps | On-call | P2 | 2025-02-01 | Completed |
| Implement query tagging to distinguish analytics vs application queries | DBA | P3 | 2025-02-28 | In progress |

## Lessons Learned

- **What went well**: Automated alerting fired within 8 minutes of degradation onset. Escalation followed the runbook timeline. Tech lead identified root cause within 8 minutes of joining the incident.
- **What went poorly**: Initial diagnosis focused on the application layer (pod restarts) rather than the database. The runbook lacked `pg_stat_activity` diagnosis steps, delaying root cause identification by approximately 20 minutes.
- **What was lucky**: All failed transactions returned 503 errors and client-side retry logic handled recovery automatically. No payments were silently lost or double-charged.
