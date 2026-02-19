---
id: RUNBOOK-028
type: runbook
title: Notification Database Deadlock Runbook
status: review
owner: On-Call Engineer
created: '2024-02-14T04:59:07.495Z'
updated: '2025-07-31T09:13:43.273Z'
tags:
  - runbook
  - notification-service
summary: Notification Database Deadlock Runbook
example: true
---

## Service

- **System**: [[SYSTEM-016|Notification Service]]
- **Owner team**: Notification Service Engineering
- **On-call rotation**: PagerDuty schedule "notifications-oncall"
- **Slack channel**: #notifications-incidents
- **Runtime**: Kubernetes / Node.js 20 / PostgreSQL 15

## Alerts

- `notification_db_deadlock_rate_high` - Database deadlock rate exceeds 10 per minute for 3 minutes
- `notification_db_transaction_wait_high` - Lock wait time P95 exceeds 2 seconds
- `notification_db_connection_pool_exhausted` - Available DB connections below 10%
- `notification_db_query_error_rate` - Database query error rate exceeds 5% for 2 minutes

## Diagnosis Steps

1. **Confirm deadlocks in PostgreSQL logs** - In Kibana, filter by `service:notification-db level:error` and look for `ERROR: deadlock detected` messages. Note the transaction details and tables involved.
2. **Identify the tables and operations involved** - PostgreSQL deadlock error messages include the table names and the queries holding and waiting for locks. Identify the pattern: are deadlocks on `notifications`, `delivery_attempts`, or `device_tokens`?
3. **Check for concurrent write contention** - Review recent deployments for changes to the notification status update path. Deadlocks in the `notifications` table often result from concurrent status updates (e.g., multiple workers updating the same row).
4. **Check connection pool utilization** - Run `SELECT count(*) FROM pg_stat_activity WHERE state = 'active';` on the notification database. Pool exhaustion can amplify lock waits.
5. **Identify long-running transactions** - Run `SELECT pid, now() - query_start AS duration, query, state FROM pg_stat_activity WHERE state != 'idle' ORDER BY duration DESC LIMIT 10;` to find transactions that may be holding locks.

## Remediation Steps

1. **If long-running transactions are blocking others**: Terminate them with `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE duration > interval '30 seconds' AND state = 'active' AND query NOT LIKE '%pg_stat%';`.
2. **If connection pool is exhausted**: Restart notification worker pods to release held connections — `kubectl rollout restart deployment/notification-worker -n notifications`.
3. **If deadlocks are from a code-level ordering issue**: This requires a code fix. As an immediate mitigation, reduce worker concurrency to lower the probability of concurrent contention while the fix is developed.
4. **If deadlocks are caused by a recent deployment**: Roll back the deployment and create a code fix ticket with the deadlock query pattern from the logs.
5. **If the situation does not improve within 15 minutes**: Escalate to the database on-call engineer and Notification Service Platform Lead.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 10 min | Post initial assessment in #notifications-incidents |
| 20 min | If not resolved: page Notification Service Platform Lead |
| 30 min | If connection pool exhausted or DB unavailable: page database on-call |
| 60 min | Major incident if Notification Service is unable to process any messages |

## Dashboards

- [Notification Database Overview](https://grafana.example.com/d/notification-db) - Connection pool, query duration, error rate
- [PostgreSQL Lock Waits](https://grafana.example.com/d/pg-locks) - Lock wait times, deadlock rate, blocking queries
- [Notification Worker Error Rate](https://grafana.example.com/d/notification-workers) - DB error rate from worker perspective
- [Notification Service Logs](https://kibana.example.com/app/discover#/notifications) - Database error logs with deadlock details
