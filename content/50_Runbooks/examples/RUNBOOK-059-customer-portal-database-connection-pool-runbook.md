---
id: RUNBOOK-059
type: runbook
title: Customer Portal Database Connection Pool Runbook
status: review
owner: On-Call Engineer
created: '2025-11-21T15:04:14.612Z'
updated: '2025-12-03T02:14:52.015Z'
tags:
  - runbook
  - customer-portal
summary: Customer Portal Database Connection Pool Runbook
example: true
---

## Service

- **System**: [[SYSTEM-041|Customer Portal]]
- **Owner team**: Customer Portal Engineering
- **On-call rotation**: PagerDuty schedule "portal-oncall"
- **Slack channel**: #customer-portal-incidents
- **Runtime**: Node.js 20 / PostgreSQL 15 / PgBouncer connection pooler

## Alerts

- `portal_db_connection_pool_exhausted` - Available PgBouncer connections below 10% for 2 minutes
- `portal_db_query_duration_p95_high` - P95 query duration exceeds 2 seconds for 5 minutes
- `portal_db_active_connections_high` - Active database connections exceed 80% of max_connections
- `portal_api_5xx_rate_high` - API 5xx rate exceeds 2% for 3 minutes (often secondary to DB saturation)

## Diagnosis Steps

1. **Check PgBouncer pool status** - Run `psql -h pgbouncer -p 6432 -U pgbouncer pgbouncer -c "SHOW POOLS;"` to view current pool utilization; check `cl_active`, `cl_waiting`, and `sv_active` columns.
2. **Check active database connections** - Query `SELECT count(*), state FROM pg_stat_activity GROUP BY state;` on the portal database; identify how many connections are `active` vs `idle` vs `idle in transaction`.
3. **Identify long-running queries** - Run `SELECT pid, now() - query_start AS duration, query, state FROM pg_stat_activity WHERE state != 'idle' ORDER BY duration DESC LIMIT 10;` to surface queries holding connections for more than expected.
4. **Correlate with recent deployments** - Check #customer-portal-deployments for any recent deploys; a new connection leak or inefficient query could have been introduced.
5. **Check portal API pod count** - Run `kubectl top pods -n customer-portal`; if the number of pods has scaled up unexpectedly, total connection demand may exceed the pool size.

## Remediation Steps

1. **If idle-in-transaction connections are blocking the pool**: Kill them with `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle in transaction' AND now() - query_start > interval '5 minutes';`
2. **If a long-running query is exhausting pool slots**: Identify and terminate it with `SELECT pg_terminate_backend([pid]);`; investigate the query in the slow query log before the next deploy.
3. **If a connection leak was introduced by a recent deploy**: Roll back the deployment immediately using the portal deploy SOP rollback procedure.
4. **If the pool is undersized for current traffic**: Temporarily increase the PgBouncer `max_client_conn` setting via the configuration management system; open a change ticket to review pool sizing.
5. **If pod scaling caused pool exhaustion**: Scale the portal deployment down to the baseline replica count and re-evaluate auto-scaling thresholds.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 10 min | Post initial assessment in #customer-portal-incidents |
| 20 min | If not resolved: page Portal Tech Lead via PagerDuty |
| 30 min | If not resolved: page DBA on-call for database-level intervention |
| 60 min | If not resolved: Engineering Manager paged; customer status update posted |

## Dashboards

- [Portal Database Overview](https://grafana.example.com/d/portal-db) - Connection pool, query duration, active connections
- [PgBouncer Stats](https://grafana.example.com/d/portal-pgbouncer) - Pool utilization, client wait time, server connections
- [Portal API Errors](https://grafana.example.com/d/portal-api-errors) - Error rate by endpoint, 5xx breakdown
- [Portal Kubernetes](https://grafana.example.com/d/portal-k8s) - Pod count, replica scaling, resource usage
