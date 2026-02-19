---
id: SOP-100
type: sop
title: Billing Database Maintenance SOP
status: accepted
owner: DevOps Lead
created: '2024-02-23T19:57:24.938Z'
updated: '2025-01-12T22:22:18.751Z'
tags:
  - sop
  - billing-engine
summary: Billing Database Maintenance SOP
related_process: PROCESS-057
related_systems:
  - SYSTEM-049
example: true
---

## Preconditions

- A maintenance window has been approved by the Engineering Manager for the scheduled maintenance period
- No monthly billing cycle run is in progress or scheduled to start within 4 hours
- A full database backup has been taken and verified within the last 2 hours
- The maintenance plan (vacuum, index rebuild, schema migration, or archival) has been reviewed by the Billing Platform Engineer

## Materials/Access

- Read/write access to the billing PostgreSQL database (role: `billing-dba`)
- Access to database monitoring dashboards (query latency, connection pool, replication lag)
- `psql` client configured for the production billing database
- Access to the billing service admin console to disable write traffic if needed
- Slack access to #billing-operations for status updates

## Procedure

1. Post in #billing-operations: "Billing DB maintenance starting: [maintenance type]. Window: [START] - [END]. DBA: [your name]."
2. Confirm the database backup timestamp in the backup monitoring dashboard. Verify the backup completed successfully within the last 2 hours.
3. Check active database connections: `SELECT count(*) FROM pg_stat_activity WHERE state = 'active';`. Confirm no long-running billing jobs are active.
4. For **VACUUM/ANALYZE**: run `VACUUM ANALYZE [table_name];` for the target tables (invoices, usage_events, billing_runs). Monitor pg_stat_user_tables for progress.
5. For **index rebuilds**: run `REINDEX INDEX CONCURRENTLY [index_name];` to avoid locking. Monitor for completion and verify the index is valid after rebuild.
6. For **schema migrations**: apply the pre-validated migration script. Monitor for lock waits using `SELECT * FROM pg_locks JOIN pg_stat_activity ON pg_locks.pid = pg_stat_activity.pid;`. If lock waits exceed 30 seconds, abort and investigate.
7. For **data archival**: execute the archival script that moves records older than the retention window to the archive table. Verify row counts before and after.
8. After maintenance, run a query health check: execute the 3 most expensive billing queries from the query performance baseline and confirm response times are within expected bounds.
9. Post in #billing-operations: "Billing DB maintenance complete. [Summary of actions taken]. Database healthy."

## Validation

- Database connection pool utilization is below 50% and stable
- Query latency for key billing queries (invoice fetch, usage aggregate) is within baseline
- Replication lag to the read replica is below 5 seconds
- No long-running or blocked queries are present in pg_stat_activity
- Billing service health check passes and invoice generation test succeeds

## Rollback

1. If a schema migration caused unexpected errors, execute the pre-prepared rollback migration script immediately.
2. Verify the schema reverts correctly and confirm the billing service can connect and execute queries.
3. If a VACUUM or index operation caused performance degradation, restart the billing service pods to clear connection pool state: `kubectl rollout restart deployment/billing-service -n billing`.
4. If data archival removed records incorrectly, restore from the pre-maintenance backup using the database restore runbook. Alert Finance Operations immediately.
