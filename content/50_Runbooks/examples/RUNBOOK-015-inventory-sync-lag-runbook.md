---
id: RUNBOOK-015
type: runbook
title: Inventory Sync Lag Runbook
status: approved
owner: On-Call Engineer
created: '2025-09-02T15:54:40.138Z'
updated: '2025-08-31T11:23:39.030Z'
tags:
  - runbook
  - inventory-management
summary: Inventory Sync Lag Runbook
example: true
---

## Service

- **System**: [[SYSTEM-011|Inventory Tracking Service]]
- **Owner team**: Inventory Engineering
- **On-call rotation**: PagerDuty schedule "inventory-oncall"
- **Slack channel**: #inventory-incidents
- **Runtime**: Kubernetes / Go 1.22 / ClickHouse / Kafka

## Alerts

- `inventory_sync_lag_high` - Kafka consumer lag for inventory sync topic exceeds 50,000 messages for 5 minutes
- `inventory_sync_warehouse_stalled` - A warehouse has had zero sync events processed for more than 10 minutes during an active sync window
- `inventory_sync_error_rate_high` - Sync event processing error rate exceeds 2% for 3 minutes
- `inventory_nightly_sync_failed` - Nightly batch sync job did not complete within 4 hours of scheduled start

## Diagnosis Steps

1. **Check consumer lag in Grafana** - Open the Inventory Kafka Consumer Lag dashboard. Identify which consumer group and topic partition is lagging. Determine if lag is growing, stable, or recovering.
2. **Check inventory sync service pod health** - Run `kubectl get pods -n inventory -l app=inventory-sync`. Look for pods in `CrashLoopBackOff`, `OOMKilled`, or `Pending` state. Check recent restarts.
3. **Check sync service error logs** - Run `kubectl logs -n inventory -l app=inventory-sync --since=15m`. Look for repeated errors indicating a downstream dependency (ClickHouse, warehouse API) is failing.
4. **Check ClickHouse write throughput** - Open the ClickHouse dashboard in Grafana. If insert throughput has dropped sharply, ClickHouse may be degraded or overloaded.
5. **Check upstream Kafka broker health** - Verify Kafka broker metrics in Grafana: under-replicated partitions, broker CPU, and disk IO. A broker failure can cause consumer lag to grow without consumer errors.

## Remediation Steps

1. **If sync service pods are crashlooping** - Check logs for OOM or panic. If OOM: increase memory limits temporarily via `kubectl edit deployment/inventory-sync -n inventory`. If panic: roll back to the previous image tag using ArgoCD.
2. **If ClickHouse is the bottleneck** - Check if a large batch or ad-hoc query is consuming ClickHouse resources. Kill the offending query via the ClickHouse admin interface. If ClickHouse is genuinely overloaded, scale down the sync consumer parallelism: reduce `SYNC_WORKER_CONCURRENCY` env var and restart pods.
3. **If a single warehouse is stalled** - Check the warehouse API health for that warehouse. If the warehouse API is timing out, disable sync for that warehouse temporarily via the admin API: `PATCH /admin/warehouses/{id}` with `"sync_enabled": false`. Re-enable after the warehouse API recovers.
4. **If Kafka broker is degraded** - This is an infrastructure issue. Page the infrastructure on-call immediately and do not attempt to resolve independently.
5. **If lag is growing but no errors are visible** - The consumer may be processing slowly due to a slow downstream. Temporarily scale up sync consumer replicas: `kubectl scale deployment/inventory-sync -n inventory --replicas=6`.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 10 min | Post initial assessment in #inventory-incidents |
| 20 min | If lag is still growing: page Inventory tech lead via PagerDuty |
| 30 min | If lag exceeds 200k messages or data freshness SLA is breached: escalate to Engineering Manager |
| 60 min | If unresolved: initiate major incident, notify downstream teams of stale inventory data |

## Dashboards

- [Inventory Sync Overview](https://grafana.example.com/d/inventory-sync) - Consumer lag, throughput, error rate by warehouse
- [Inventory ClickHouse](https://grafana.example.com/d/inventory-clickhouse) - Insert rate, query performance, disk usage
- [Kafka Broker Health](https://grafana.example.com/d/kafka-brokers) - Broker status, under-replicated partitions, consumer group lag
- [Inventory Sync Pods](https://grafana.example.com/d/k8s-inventory-sync) - Pod health, CPU, memory, restart count
