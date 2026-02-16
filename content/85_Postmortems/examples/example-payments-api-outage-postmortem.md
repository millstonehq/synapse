---
id: postmortem-inc-4
type: postmortem
title: Payments API Outage - Database Connection Pool Exhaustion
status: approved
owner: On-Call Engineer
created: '2025-11-05T00:00:00.000Z'
updated: '2025-11-07T00:00:00.000Z'
tags:
  - postmortem
  - payments
  - database
  - incident
summary: >-
  Post-incident analysis of the Nov 5 Payments API outage caused by
  database connection pool exhaustion. USE A POSTMORTEM after a
  significant incident has been resolved to record what happened, why,
  and how to prevent it from recurring. Postmortems answer "what went
  wrong, what did we learn, and what will we change?" They are
  blameless retrospectives focused on systemic improvements. Compare:
  a Runbook tells you how to fix the incident in real time; a
  Postmortem analyzes it after the fact. Action items from postmortems
  often result in new or updated Runbooks, SOPs, and Standards.
incident_number: INC-4
severity: SEV-2
incident_date: '2025-11-05'
detection_time: '2025-11-05T14:23:00.000Z'
resolution_time: '2025-11-05T15:47:00.000Z'
total_duration: ~84 minutes
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: deploy-with-rollback-sop
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On November 5, 2025, the Payments API experienced an 84-minute outage caused by database connection pool exhaustion. A long-running analytics query locked several rows, causing application queries to queue up and exhaust the connection pool. The outage affected all payment processing, resulting in approximately $12,000 in delayed transactions. No data was lost.

The incident was detected by automated alerting at 14:23 UTC and resolved at 15:47 UTC when the long-running query was identified and terminated. A subsequent pod restart cleared the exhausted connection pool.

## Timeline

- **14:15** - Analytics team runs a large aggregate query against the payments database (unbeknownst to the on-call team)
- **14:18** - Payment API response times begin increasing as queries queue behind row locks
- **14:23** - `payments_latency_p95_high` alert fires. On-call engineer acknowledges.
- **14:25** - On-call checks recent deploys - none in the last 24 hours. Rules out deploy-related cause.
- **14:30** - Error logs show `connection pool exhausted` errors. On-call attempts pod restart.
- **14:35** - Pod restart provides temporary relief (30 seconds) before pool exhausts again. Root cause still active.
- **14:42** - On-call escalates to Payments tech lead per runbook escalation timeline.
- **14:50** - Tech lead checks `pg_stat_activity` and identifies a 35-minute-old analytics query holding row locks on the payments table.
- **14:52** - Long-running query terminated via `pg_terminate_backend()`.
- **14:55** - Connection pool begins draining. Response times improving but not yet normal.
- **15:00** - Full pod restart to clear stale connections. Error rate drops to baseline.
- **15:15** - Metrics stable. On-call continues monitoring per SOP.
- **15:47** - Incident formally closed after 30-minute stable observation window.

## Impact

- **Duration**: 84 minutes (14:23 - 15:47 UTC)
- **Users affected**: All customers attempting payment transactions during the window
- **Transactions impacted**: ~340 payment attempts failed with 503 errors. All were retried successfully by clients after resolution.
- **Revenue impact**: Approximately $12,000 in delayed payment processing (no permanent revenue loss)
- **SLA impact**: Monthly uptime dropped to 99.87% (below 99.9% SLA target)
- **Customer communications**: Status page updated at 14:30, customer support notified at 14:35

## Root Cause Analysis

The root cause was a combination of two factors:

1. **No query isolation**: The analytics team ran a long-running aggregate query directly against the production payments database rather than a read replica. This query acquired row-level locks that blocked application write transactions.

2. **No connection pool protection**: The Payments API connection pool had no maximum wait time configured. When connections were blocked by locks, new requests queued indefinitely rather than failing fast, eventually exhausting all 100 connections in the pool.

The analytics query was legitimate but should have been routed to a read replica. The connection pool configuration lacked defensive settings that would have limited the blast radius.

## Resolution

Immediate resolution:
1. Identified and terminated the long-running analytics query
2. Restarted all Payments API pods to clear exhausted connection pools
3. Monitored metrics for 30 minutes to confirm stable recovery

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add `statement_timeout` of 30s to application database role | DBA | P1 | 2025-11-08 | Completed |
| Configure connection pool `maxWaitTime` of 5s (fail fast) | Payments team | P1 | 2025-11-08 | Completed |
| Route analytics queries to read replica | Analytics team | P1 | 2025-11-12 | In progress |
| Add `payments_db_connection_pool_exhausted` alert at 80% utilization | SRE | P2 | 2025-11-15 | Pending |
| Update [[service-outage-runbook]] with connection pool diagnosis steps | On-call | P2 | 2025-11-15 | Pending |
| Implement query tagging so analytics vs application queries are distinguishable | DBA | P3 | 2025-11-30 | Pending |

## Lessons Learned

- **What went well**: Automated alerting detected the issue within 5 minutes. Escalation followed the runbook timeline. Tech lead identified root cause within 8 minutes of joining.
- **What went poorly**: Initial diagnosis focused on the application (pod restarts) rather than the database. The runbook didn't include steps for checking `pg_stat_activity` for long-running queries. This delayed root cause identification by ~20 minutes.
- **What was lucky**: No data was lost because all failed transactions returned 503 errors and clients retried automatically.
- **Process improvement**: Add "check for long-running queries" as step 3 in the Payments API runbook diagnosis flow, before attempting pod restarts.
- **Architecture improvement**: Connection pools should always have a `maxWaitTime` to fail fast rather than queue indefinitely. This applies to all services, not just Payments.
