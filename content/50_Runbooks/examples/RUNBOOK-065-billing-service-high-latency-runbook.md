---
id: RUNBOOK-065
type: runbook
title: Billing Service High Latency Runbook
status: approved
owner: On-Call Engineer
created: '2025-03-10T19:48:27.789Z'
updated: '2026-06-12T22:53:34.785Z'
tags:
  - runbook
  - billing-engine
summary: Billing Service High Latency Runbook
example: true
---

## Service

- **System**: [[SYSTEM-050|Billing Engine]]
- **Owner team**: Billing Platform Engineering
- **On-call rotation**: PagerDuty schedule "billing-oncall"
- **Slack channel**: #billing-incidents
- **Runtime**: Kubernetes / Java 21 / PostgreSQL 15 / Kafka

## Alerts

- `billing_api_latency_p95_high` - Billing API P95 latency above 2 seconds for 5 minutes
- `billing_api_latency_p99_high` - Billing API P99 latency above 5 seconds for 3 minutes
- `billing_invoice_generation_latency_high` - Invoice generation P95 latency above 10 seconds
- `billing_db_query_latency_high` - Billing DB query P95 latency above 500ms for 5 minutes

## Diagnosis Steps

1. **Identify the latency hotspot** - Check the Billing Engine Overview dashboard. Determine whether the latency is in the billing API layer, invoice generation, tax calculation calls, or database queries. The breakdown chart will show where time is being spent.
2. **Check the billing database** - High DB query latency is the most common cause. Run `SELECT query, calls, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;` to find slow queries. Check if any table has missing or bloated indexes.
3. **Check the tax calculation service latency** - If invoice-related API calls are slow, check if the tax calculation service is responding slowly. Its latency feeds directly into billing API response times for any request that triggers invoice generation.
4. **Check Kafka consumer lag** - For billing event processing latency, check the Kafka consumer group lag in the Kafka dashboard. High consumer lag indicates billing event workers are falling behind.
5. **Check Kubernetes resource pressure** - Run `kubectl top pods -n billing` to check CPU and memory. If billing service pods are CPU-throttled or near memory limits, this will manifest as sustained high latency.

## Remediation Steps

1. **If caused by slow database queries**: Check for missing indexes on recently added filters. If a specific query is dominating, check for lock contention with `SELECT * FROM pg_locks JOIN pg_stat_activity ON pg_locks.pid = pg_stat_activity.pid WHERE NOT granted;`. Kill blocking queries if safe to do so.
2. **If tax calculation service is slow**: Enable response caching for tax rate lookups in the billing service config. Check if the tax service is under-scaled and needs horizontal scaling.
3. **If Kafka consumer lag is high**: Scale up billing event consumer workers by increasing the `billing-event-consumer` deployment replicas. Check for poison pill messages blocking a partition.
4. **If pods are CPU or memory constrained**: Scale up billing service replicas: `kubectl scale deployment/billing-service -n billing --replicas=6`. Submit a right-sizing ticket if this is recurrent.
5. **If a recent deploy is correlated**: Roll back the billing service per the Deploy Billing Service Update SOP rollback procedure.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and opens billing dashboard |
| 10 min | Post latency hotspot assessment in #billing-incidents |
| 20 min | If customer-facing API latency is above 5s: page Billing Platform tech lead |
| 30 min | If billing cycle run is impacted: page Engineering Manager |
| 60 min | If unresolved: escalate to infrastructure on-call for Kubernetes or DB-level issues |

## Dashboards

- [Billing Engine Overview](https://grafana.example.com/d/billing-overview) - API latency breakdown, invoice generation latency
- [Billing Database Performance](https://grafana.example.com/d/billing-db-perf) - Query latency, pg_stat_statements, lock contention
- [Billing Kafka Consumers](https://grafana.example.com/d/billing-kafka) - Consumer group lag, partition assignment, throughput
- [Kubernetes Billing Namespace](https://grafana.example.com/d/k8s-billing) - Pod CPU/memory, resource limits, restarts
- [Tax Service Health](https://grafana.example.com/d/tax-service) - Response latency, error rate, cache hit rate
