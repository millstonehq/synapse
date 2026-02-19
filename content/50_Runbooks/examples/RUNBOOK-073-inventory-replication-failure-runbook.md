---
id: RUNBOOK-073
type: runbook
title: Inventory Replication Failure Runbook
status: approved
owner: On-Call Engineer
created: '2025-05-26T02:56:53.998Z'
updated: '2026-10-20T21:23:14.625Z'
tags:
  - runbook
  - inventory-management
summary: Inventory Replication Failure Runbook
example: true
---

## Service

- **System**: [[SYSTEM-011|Inventory Replication Service]]
- **Owner team**: Inventory Platform Engineering
- **On-call rotation**: PagerDuty schedule "inventory-oncall"
- **Slack channel**: #inventory-incidents
- **Runtime**: Kubernetes / Go 1.22 / ScyllaDB 5 / Redis 7

## Alerts

- `inventory_replication_lag_high` - Replication lag between primary and replica ScyllaDB nodes exceeds 30 seconds for 5 minutes
- `inventory_replication_pod_crashloop` - Replication consumer pod restarting more than 3 times in 10 minutes
- `inventory_event_dlq_depth_high` - Dead letter queue depth for replication events exceeds 200 messages
- `inventory_replication_consistency_mismatch` - Reconciliation check detects divergence between primary and replica stock levels exceeding 0.1% of SKUs
- `inventory_replication_throughput_low` - Events processed per second drops below 50% of the 7-day baseline for 10 minutes

## Diagnosis Steps

1. **Check if a recent deploy happened** - Look at the #deployments channel and ArgoCD. If the replication failure started within 30 minutes of a deploy to the inventory-replication-service, the deploy is the most likely cause. Skip to Remediation Step 1 (rollback).

2. **Check replication consumer logs** - In Kibana, filter by `service:inventory-replication` and `level:error` for the last 30 minutes. Look for: event schema parse errors (malformed upstream events), ScyllaDB write timeout errors (replica overload), or context deadline errors (consumer falling behind the event stream).

3. **Check ScyllaDB replica health** - Connect to the ScyllaDB admin console and run `nodetool status`. All nodes should show `UN` (Up/Normal). Nodes in `DN` (Down) or `UL` (Up/Leaving) state indicate a cluster problem. Check `nodetool tpstats` for dropped mutations and `nodetool compactionstats` for compaction backlog.

4. **Check replication event stream lag** - In the Grafana inventory replication dashboard, review the "Consumer Lag" panel. If lag is growing steadily, the consumer is processing events slower than they arrive. Check consumer pod CPU and memory (`kubectl top pods -n inventory`). If pods are at CPU limits, the consumer needs scaling.

5. **Check the DLQ** - Inspect messages in the dead letter queue to understand the failure pattern. Run: `kubectl exec -n inventory deploy/inventory-replication -- ./dlq-inspector --limit 10` to see the most recent failed events. Common causes: schema version mismatch (upstream event format changed), missing `sku_id` (SKU not yet registered), and ScyllaDB partition errors.

6. **Check upstream event bus health** - Verify the Inventory Event Bus is publishing events normally. If the event bus itself is degraded, replication failures are a symptom of the upstream problem rather than a replication-specific issue. Check the #inventory-incidents channel for related alerts.

## Remediation Steps

1. **If caused by a recent deploy**: Roll back immediately using the standard deployment rollback procedure. Do not wait to investigate root cause under incident pressure — roll back first, investigate after service is restored.

2. **If ScyllaDB replica is down or degraded**: Page the infrastructure on-call (PagerDuty "infra-oncall"). Do not attempt to restart ScyllaDB nodes without DBA involvement. While awaiting infrastructure response, the replication service will accumulate lag but the primary inventory system will remain operational.

3. **If consumer is falling behind due to throughput**: Scale up the replication consumer replicas to increase parallel processing: `kubectl scale deployment/inventory-replication -n inventory --replicas=6`. Monitor the lag panel to confirm it starts decreasing. If throughput remains low after scaling, investigate CPU throttling or ScyllaDB write saturation.

4. **If DLQ contains schema parse errors**: This indicates an upstream event schema change that the replication service has not been updated to handle. Pause replication event consumption to prevent further DLQ growth: `kubectl scale deployment/inventory-replication -n inventory --replicas=0`. Escalate to the Inventory Platform tech lead immediately with the DLQ event sample.

5. **If consistency mismatch alert fires**: Do not run a manual reconciliation without tech lead approval. Incorrect reconciliation can create spurious stock adjustment events visible to merchants. Escalate to the Inventory Platform tech lead and follow the inventory reconciliation runbook for the manual reconciliation procedure.

6. **If cause is unknown after 15 minutes of diagnosis**: Escalate immediately. Post a summary of what you have checked in #inventory-incidents and page the tech lead.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 5 min | Post initial assessment in #inventory-incidents |
| 15 min | If not resolved: page Inventory Platform tech lead via PagerDuty |
| 30 min | If not resolved: page Engineering Manager, assess merchant impact, begin customer communication if stock data is stale |
| 60 min | If not resolved: initiate major incident process, assemble war room in #incident-war-room |

**Who to escalate to:**
- Inventory Platform tech lead: PagerDuty schedule "inventory-leads"
- ScyllaDB / infrastructure issues: PagerDuty schedule "infra-oncall"
- Database issues: PagerDuty schedule "dba-oncall"
- If merchant stock data is visibly stale: notify merchant success team via #merchant-success-ops

## Dashboards

- [Inventory Replication Overview](https://grafana.example.com/d/inventory-replication) - Consumer lag, throughput, DLQ depth
- [ScyllaDB Cluster Health](https://grafana.example.com/d/scylladb-inventory) - Node status, compaction backlog, dropped mutations
- [Inventory Replication Logs](https://kibana.example.com/app/discover#/inventory-replication) - Error logs with event details
- [Kubernetes Inventory Namespace](https://grafana.example.com/d/k8s-inventory) - Pod health, resource usage, restarts
- [Consistency Reconciliation](https://grafana.example.com/d/inventory-consistency) - Primary vs replica divergence metrics
