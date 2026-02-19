---
id: RUNBOOK-018
type: runbook
title: Inventory Database Connection Pool Runbook
status: approved
owner: On-Call Engineer
created: '2024-05-16T11:17:26.154Z'
updated: '2026-11-26T14:37:00.556Z'
tags:
  - runbook
  - inventory-management
summary: Inventory Database Connection Pool Runbook
example: true
---

## Service

- **System**: [[SYSTEM-011|Inventory Tracking Service]]
- **Owner team**: Inventory Engineering
- **On-call rotation**: PagerDuty schedule "inventory-oncall"
- **Slack channel**: #inventory-incidents
- **Runtime**: Kubernetes / Go 1.22 / ClickHouse / Kafka

## Alerts

- `inventory_db_connection_pool_exhausted` - Available database connections fall below 5% of pool max for 2 minutes
- `inventory_db_query_latency_p95_high` - P95 database query latency exceeds 2 seconds for 5 minutes
- `inventory_db_connection_wait_high` - Average connection wait time exceeds 500ms, indicating pool pressure
- `inventory_db_long_running_queries` - One or more queries have been running for more than 60 seconds

## Diagnosis Steps

1. **Check connection pool metrics in Grafana** - Open the Inventory Database dashboard. Identify current pool utilization, wait time trend, and whether the exhaustion is growing or stable.
2. **Check for long-running queries** - Run on the inventory database primary: `SELECT pid, now() - query_start AS duration, query, state FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC LIMIT 10;`. Queries running longer than 30 seconds are candidates for termination.
3. **Check recent deploys** - A recent inventory service deployment may have introduced a query regression or a connection leak. Check deployment history in ArgoCD.
4. **Check inventory service pod count vs. pool size** - Each pod maintains its own connection pool. If the service scaled up unexpectedly, total connections may exceed the database's `max_connections`. Run: `kubectl get pods -n inventory -l app=inventory-api | wc -l` and multiply by the per-pod pool size.
5. **Check for upstream traffic spike** - Review Grafana for inventory API request rate. A sudden traffic spike may be exhausting the connection pool legitimately; in this case, the fix is to scale the database read replica, not kill queries.

## Remediation Steps

1. **If long-running queries are the cause** - Terminate the top offenders: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE now() - query_start > interval '60 seconds' AND state = 'active' AND query NOT LIKE '%pg_stat%';`. Then restart inventory API pods to reset connection pools: `kubectl rollout restart deployment/inventory-api -n inventory`.
2. **If pool exhaustion is from too many pods** - Reduce inventory API replicas to the normal count: `kubectl scale deployment/inventory-api -n inventory --replicas=[normal_count]`. If this was caused by an HPA runaway, check the HPA status: `kubectl get hpa -n inventory`.
3. **If caused by a recent deploy** - Roll back the inventory service via ArgoCD to the previous stable version.
4. **If traffic spike is legitimate** - Scale the read replica capacity. Page the DBA on-call for this. As a temporary measure, enable the read-only cache bypass to reduce database reads from the API layer.
5. **If cause is unknown after 15 minutes** - Escalate to the Inventory Platform Engineer and DBA on-call simultaneously.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer checks pool metrics and identifies long-running queries |
| 5 min | Post assessment in #inventory-incidents |
| 15 min | If pool still exhausted: page Inventory tech lead and DBA on-call |
| 30 min | If inventory API is returning errors to users: escalate to Engineering Manager |
| 60 min | If unresolved: initiate major incident process |

## Dashboards

- [Inventory Database](https://grafana.example.com/d/inventory-db) - Connection pool utilization, query latency, active connections
- [Inventory API Overview](https://grafana.example.com/d/inventory-api) - Request rate, error rate, latency percentiles
- [Inventory Pods](https://grafana.example.com/d/k8s-inventory) - Pod count, CPU, memory, HPA status
- [PostgreSQL Queries](https://grafana.example.com/d/pg-queries) - Slow query log, lock waits, index hit rates
