---
id: RUNBOOK-016
type: runbook
title: Warehouse API Timeout Runbook
status: approved
owner: On-Call Engineer
created: '2025-10-17T17:21:11.623Z'
updated: '2025-11-18T10:35:04.000Z'
tags:
  - runbook
  - inventory-management
summary: Warehouse API Timeout Runbook
example: true
---

## Service

- **System**: [[SYSTEM-011|Inventory Tracking Service]]
- **Owner team**: Inventory Engineering
- **On-call rotation**: PagerDuty schedule "inventory-oncall"
- **Slack channel**: #inventory-incidents
- **Runtime**: Kubernetes / Go 1.22 / ClickHouse / Kafka

## Alerts

- `warehouse_api_timeout_rate_high` - Timeout rate for outbound warehouse API calls exceeds 5% over 5 minutes
- `warehouse_api_circuit_open` - Circuit breaker for a warehouse API endpoint has opened (5 failures in 30s)
- `inventory_sync_warehouse_stalled` - A warehouse is not delivering sync events due to API connectivity failure
- `warehouse_api_latency_p95_high` - P95 latency for warehouse API calls exceeds 5 seconds

## Diagnosis Steps

1. **Identify the affected warehouse** - Check the Warehouse API Timeout dashboard in Grafana to see which warehouse integration is experiencing timeouts. Note the warehouse ID and API endpoint path.
2. **Check if this is a recent deployment** - Review the deployment history for the inventory sync service and the affected warehouse's integration adapter. Timeouts starting at deployment time indicate a configuration regression.
3. **Test connectivity to the warehouse API directly** - From a sync pod, run: `kubectl exec -n inventory -it [pod-name] -- curl -v --max-time 10 https://[warehouse-api-host]/health`. A connection timeout indicates network-level issues; a slow response indicates API performance degradation at the warehouse.
4. **Check the warehouse vendor status page** - Many warehouse management system vendors publish status pages. Look for any active incidents reported by the vendor.
5. **Review circuit breaker state** - Query the sync service admin endpoint for circuit breaker status: `GET /admin/circuit-breakers`. If the circuit is open, the service is already protecting itself; focus on when the warehouse API will recover.

## Remediation Steps

1. **If the circuit breaker is open** - The service is already protecting itself from cascading failures. Do not force-close the circuit. Monitor for recovery; the circuit will attempt a probe request after the configured recovery window (default 60 seconds).
2. **If it is a recent deployment causing timeouts** - Roll back the inventory sync service or the specific warehouse adapter to the previous version via ArgoCD. Do not attempt to fix forward under timeout pressure.
3. **If the warehouse vendor API is degraded** - Notify the Warehouse Operations Lead and open a support ticket with the WMS vendor. Disable sync for the affected warehouse via admin API to prevent log flooding: `PATCH /admin/warehouses/{id}` with `"sync_enabled": false`. Re-enable when vendor confirms resolution.
4. **If it is a network-level issue** - Page the infrastructure on-call. Do not attempt network troubleshooting independently.
5. **If timeouts are intermittent and below circuit open threshold** - Increase the timeout setting for the affected warehouse adapter as a temporary measure. File a follow-up to investigate the root cause of increased latency.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and checks circuit breaker state |
| 10 min | Post warehouse ID and initial finding in #inventory-incidents |
| 15 min | If vendor API degraded: notify Warehouse Operations Lead |
| 30 min | If sync outage will breach SLA: escalate to Engineering Manager |
| 60 min | If vendor outage is prolonged: initiate formal incident with customer impact assessment |

## Dashboards

- [Warehouse API Health](https://grafana.example.com/d/warehouse-api) - Timeout rate, latency, circuit breaker state by warehouse
- [Inventory Sync Overview](https://grafana.example.com/d/inventory-sync) - Per-warehouse sync throughput and error rates
- [Inventory Sync Pods](https://grafana.example.com/d/k8s-inventory-sync) - Pod health and recent restart events
- [Network Connectivity](https://grafana.example.com/d/network-egress) - Egress latency to external endpoints
