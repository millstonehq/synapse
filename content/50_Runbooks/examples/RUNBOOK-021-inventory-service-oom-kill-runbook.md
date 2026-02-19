---
id: RUNBOOK-021
type: runbook
title: Inventory Service OOM Kill Runbook
status: approved
owner: On-Call Engineer
created: '2024-10-07T15:01:30.883Z'
updated: '2026-10-23T06:22:46.061Z'
tags:
  - runbook
  - inventory-management
summary: Inventory Service OOM Kill Runbook
example: true
---

## Service

- **System**: [[SYSTEM-011|Inventory Tracking Service]]
- **Owner team**: Inventory Engineering
- **On-call rotation**: PagerDuty schedule "inventory-oncall"
- **Slack channel**: #inventory-incidents
- **Runtime**: Kubernetes / Go 1.22 / ClickHouse / Kafka

## Alerts

- `inventory_pod_oomkilled` - One or more inventory service pods have been OOM killed in the past 5 minutes
- `inventory_memory_usage_high` - Memory usage for inventory service pods exceeds 85% of limit for 10 minutes
- `inventory_pod_crashloop` - An inventory service pod is restarting more than 3 times in 10 minutes (often OOM-related)
- `inventory_heap_allocation_spike` - Go runtime heap allocation rate has spiked more than 5x normal for 3 minutes

## Diagnosis Steps

1. **Confirm OOM kill cause** - Run `kubectl describe pod [pod-name] -n inventory` and look for `OOMKilled` in the last state. Note the `exitCode: 137` which confirms OOM kill. Check `kubectl get events -n inventory --sort-by='.lastTimestamp'` for recent OOM events.
2. **Check memory usage trend before the kill** - Open the Inventory Pods Grafana dashboard and look at the memory usage graph for the killed pod in the 30 minutes before the kill. Is memory growing steadily (leak) or did it spike suddenly (large allocation)?
3. **Check for large request payloads** - Query the inventory API access logs for the period before the OOM kill. Look for unusually large requests: bulk operations, large list queries without pagination, or full-catalog scans that may have exhausted heap.
4. **Check for a recent code deployment** - A newly deployed version may have introduced a memory leak or a new code path that allocates large objects. Compare memory usage trends before and after the last deployment.
5. **Correlate with traffic patterns** - Check the API request rate at the time of the OOM kill. If traffic was at normal levels, a leak is more likely. If there was a spike, the fix may be rate limiting or query size limits rather than memory limit increases.

## Remediation Steps

1. **Immediate: restart the crashed pod** - Kubernetes will restart OOM killed pods automatically. If the pod is stuck in `CrashLoopBackOff`, delete it to trigger a fresh start: `kubectl delete pod [pod-name] -n inventory`.
2. **If memory leak is suspected** - Set a rolling restart schedule to mitigate the leak while the root cause is investigated: `kubectl rollout restart deployment/inventory-api -n inventory`. File a high-priority bug for the engineering team with the memory growth graph attached.
3. **If the OOM is from a large query** - Identify the query or endpoint using the access logs. Add or reduce the pagination limit for that endpoint. As a temporary measure, add a rate limit on the specific endpoint.
4. **If the OOM is caused by a recent deploy** - Roll back using ArgoCD immediately. OOM kills will continue until the bad version is removed.
5. **If multiple pods are OOM killing simultaneously** - Increase the memory limit temporarily: `kubectl set resources deployment/inventory-api -n inventory --limits=memory=2Gi`. This buys time for root cause investigation. Do not increase limits without filing a follow-up to investigate the root cause.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer confirms OOM kill and checks restart status |
| 5 min | Post initial assessment in #inventory-incidents |
| 10 min | If pods are in crashloop: roll back if recent deploy, otherwise increase memory limit |
| 20 min | If more than 2 pods are OOM killing: page Inventory tech lead |
| 30 min | If service availability is impacted: escalate to Engineering Manager |

## Dashboards

- [Inventory Pods](https://grafana.example.com/d/k8s-inventory) - Memory usage, OOM kill events, restart count by pod
- [Inventory API Overview](https://grafana.example.com/d/inventory-api) - Request rate, large response payloads, error rate
- [Go Runtime](https://grafana.example.com/d/go-runtime-inventory) - Heap size, GC frequency, goroutine count
- [Kubernetes Events](https://grafana.example.com/d/k8s-events-inventory) - Recent OOM and eviction events in inventory namespace
