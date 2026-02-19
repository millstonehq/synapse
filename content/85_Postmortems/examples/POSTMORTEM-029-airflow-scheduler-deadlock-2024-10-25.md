---
id: POSTMORTEM-029
type: postmortem
title: Airflow Scheduler Deadlock 2024-10-25
status: approved
owner: On-Call Engineer
created: '2025-03-08T13:44:05.939Z'
updated: '2026-07-19T13:22:54.221Z'
tags:
  - postmortem
  - data-pipeline
summary: Airflow Scheduler Deadlock 2024-10-25
incident_number: INC-550
severity: SEV-1
incident_date: '2025-07-22'
detection_time: '2024-12-07T21:04:48.563Z'
resolution_time: '2024-05-17T19:17:14.719Z'
total_duration: ~4 hours
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-060
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On October 25, 2024, the Airflow scheduler responsible for orchestrating data pipeline transformation jobs entered a deadlock state, causing all pipeline DAG executions to halt for approximately 4 hours. The deadlock was triggered by a combination of a slow database query on the Airflow metadata database and a misconfigured DAG with an infinite retry loop that saturated the scheduler's task slot pool.

The incident was detected when 14 downstream analytics consumers reported stale data at approximately 10:30 UTC. The scheduler was restarted and the misconfigured DAG was paused, restoring normal operation by 14:45 UTC.

## Timeline

- **06:15** - New DAG deployed with `retries=99999` and `retry_delay=timedelta(seconds=1)` — misconfiguration not caught in code review
- **06:20** - DAG begins executing; first task fails and immediately begins retry storm, consuming scheduler slots
- **08:30** - Scheduler task slot pool saturated (512/512 slots occupied by retry tasks from the misconfigured DAG)
- **09:45** - Slow query on Airflow metadata DB begins; scheduler heartbeat interval drops from 5s to 45s
- **10:28** - Scheduler enters deadlock between slot allocation lock and metadata DB query lock
- **10:30** - 14 analytics consumers report stale data; on-call acknowledges
- **10:45** - On-call identifies scheduler as unresponsive; Airflow UI shows all DAGs as "running" but no tasks executing
- **11:30** - Root cause identified: infinite retry DAG + slow metadata query combination
- **12:00** - Misconfigured DAG paused via Airflow API; retry tasks begin clearing
- **13:15** - Slot pool drains to normal levels; metadata DB slow query identified and terminated
- **14:30** - Scheduler restarted; DAGs begin executing normally
- **14:45** - Downstream analytics consumers confirm data freshness restored

## Impact

- **Duration**: 4 hours 15 minutes of scheduler inactivity (10:30 - 14:45 UTC)
- **DAGs affected**: All 47 production DAGs halted during the deadlock window
- **Downstream impact**: 14 analytics consumers received stale data; BI dashboards 4+ hours out of date
- **Data loss**: Zero — all transformation jobs backfilled once scheduler recovered
- **SLA impact**: Tier-1 data freshness SLA breached for the 4-hour window

## Root Cause Analysis

1. **Unconstrained retry configuration**: The misconfigured DAG had `retries=99999` with a 1-second retry delay, creating a retry storm that consumed all 512 scheduler task slots within 2 hours. No DAG validation prevented deployment with obviously pathological retry settings.

2. **Slot pool exhaustion triggers scheduler deadlock**: When the slot pool was fully saturated, the scheduler's internal locking behavior combined with a concurrent slow metadata DB query created a deadlock condition. The scheduler has a known upstream issue with this combination that was not patched in the version in use (Airflow 2.6.1).

## Resolution

1. Paused the misconfigured DAG via the Airflow REST API to stop new retry task creation
2. Waited for existing retry tasks to drain from the slot pool (approximately 2 hours)
3. Terminated the slow metadata DB query via `pg_terminate_backend()`
4. Restarted the Airflow scheduler pod to clear the deadlock state
5. Confirmed all 47 DAGs resumed normal execution

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add DAG validation rule rejecting `retries > 10` or `retry_delay < 60s` | Data Engineering | P1 | 2024-11-01 | Completed |
| Upgrade Airflow to 2.7.3 (contains deadlock fix) | Infra | P1 | 2024-11-08 | Completed |
| Add scheduler heartbeat alert (> 30s interval triggers page) | SRE | P1 | 2024-11-01 | Completed |
| Add task slot utilization alert (> 80% for 10 minutes triggers warning) | SRE | P2 | 2024-11-08 | Completed |

## Lessons Learned

- **What went well**: Stale data detection by downstream consumers provided an alternative alert path when the scheduler alert was not firing.
- **What went poorly**: The misconfigured DAG passed code review without the retry settings being flagged. No automated guardrail existed to prevent obviously pathological configurations from reaching production.
- **What was lucky**: The deadlock occurred during business hours when on-call response was fast. An overnight occurrence would have resulted in 8+ hours of stale data.
