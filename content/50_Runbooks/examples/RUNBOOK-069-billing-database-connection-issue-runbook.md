---
id: RUNBOOK-069
type: runbook
title: Billing Database Connection Issue Runbook
status: approved
owner: On-Call Engineer
created: '2024-02-09T08:05:41.403Z'
updated: '2026-12-20T13:22:50.169Z'
tags:
  - runbook
  - billing-engine
summary: Billing Database Connection Issue Runbook
example: true
---

## Service

- **System**: [[SYSTEM-050|Billing Engine]]
- **Owner team**: Billing Platform Engineering
- **On-call rotation**: PagerDuty schedule "billing-oncall"
- **Slack channel**: #billing-incidents
- **Runtime**: Kubernetes / Java 21 / PostgreSQL 15 / Kafka

## Alerts

- `billing_db_connection_pool_exhausted` - Available billing DB connections below 10% for 3 minutes
- `billing_db_connection_acquisition_timeout` - DB connection acquisition timeout rate above 1%
- `billing_db_replica_lag_high` - Read replica replication lag above 60 seconds
- `billing_service_db_unavailable` - Billing service cannot establish any DB connections

## Diagnosis Steps

1. **Check total active connections** - Run `SELECT count(*), state FROM pg_stat_activity WHERE datname = 'billing' GROUP BY state;`. Compare active count to the connection pool max (configured as 100 for the billing service).
2. **Check for long-running queries holding connections** - Run `SELECT pid, now() - pg_stat_activity.query_start AS duration, query, state FROM pg_stat_activity WHERE datname = 'billing' AND state != 'idle' ORDER BY duration DESC LIMIT 10;`. Queries running longer than 5 minutes are connection hogs.
3. **Check billing service pod count vs. pool config** - If billing service was recently scaled up, total connection demand may exceed the DB's `max_connections`. Each pod opens `billing.db.pool.max-size` connections (default: 10). 12 pods × 10 = 120 connections, exceeding the default 100 limit.
4. **Check for connection leaks** - Review billing service logs for `ConnectionLeakDetected` warnings. These indicate connections are not being returned to the pool after use.
5. **Check if the DB itself is under pressure** - Check Billing Database Performance dashboard for CPU, memory, and I/O. If the DB host is resource-constrained, it may be refusing new connections.

## Remediation Steps

1. **If long-running queries are exhausting connections**: Kill the long-running queries: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'billing' AND state = 'active' AND now() - query_start > interval '5 minutes' AND query NOT LIKE '%pg_stat%';`. Restart billing service pods to reset the connection pool.
2. **If scaling caused pool exhaustion**: Reduce billing service replica count to bring total connections back below the DB limit: `kubectl scale deployment/billing-service -n billing --replicas=8`. Alternatively, reduce per-pod pool size via environment variable `BILLING_DB_POOL_MAX_SIZE=8`.
3. **If connection leaks are detected**: Restart billing service pods to force-release leaked connections: `kubectl rollout restart deployment/billing-service -n billing`. File a bug ticket for the connection leak. Monitor the leak rate after restart.
4. **If the DB host itself is failing**: Page the infrastructure on-call for the billing DB host. Failover to the read replica for read-heavy operations while the primary is recovered.
5. **If replica lag is high and queries are hitting the replica**: Force routing to the primary by disabling read replica routing in the billing service config: `kubectl set env deployment/billing-service -n billing BILLING_DB_READ_REPLICA_ENABLED=false`.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer checks connection count and identifies exhaustion source |
| 10 min | Post initial assessment in #billing-incidents |
| 20 min | If billing service cannot process invoices: page Billing Platform tech lead |
| 30 min | If primary DB is failing over: page infrastructure on-call and Engineering Manager |
| 60 min | If billing cycle is blocked by DB unavailability: initiate major incident process |

## Dashboards

- [Billing Database](https://grafana.example.com/d/billing-db) - Connection pool usage, active/idle counts, acquisition latency
- [Billing Database Performance](https://grafana.example.com/d/billing-db-perf) - Query latency, pg_stat_statements, long-running queries
- [Billing Database Replication](https://grafana.example.com/d/billing-db-replication) - Replica lag, WAL send rate
- [Kubernetes Billing Namespace](https://grafana.example.com/d/k8s-billing) - Billing service pod count, resource usage
