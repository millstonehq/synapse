---
id: RUNBOOK-063
type: runbook
title: Customer Portal Memory Leak Runbook
status: draft
owner: On-Call Engineer
created: '2024-07-15T20:31:21.031Z'
updated: '2026-09-17T04:46:42.484Z'
tags:
  - runbook
  - customer-portal
summary: Customer Portal Memory Leak Runbook
example: true
---

## Service

- **System**: [[SYSTEM-041|Customer Portal]]
- **Owner team**: Customer Portal Engineering
- **On-call rotation**: PagerDuty schedule "portal-oncall"
- **Slack channel**: #customer-portal-incidents
- **Runtime**: Node.js 20 / Kubernetes / PostgreSQL 15

## Alerts

- `portal_pod_memory_usage_high` - Pod memory usage exceeds 85% of memory limit for 10 minutes
- `portal_pod_oom_killed` - One or more portal pods killed by OOMKiller
- `portal_heap_usage_trending_up` - Node.js heap size increasing monotonically for 30 minutes without plateau
- `portal_pod_restart_count_high` - Pod restart count exceeds 5 in 1 hour

## Diagnosis Steps

1. **Check recent pod restart history** - Run `kubectl describe pod -n customer-portal -l app=customer-portal` and look at the last restart reason; `OOMKilled` confirms memory exhaustion as the cause.
2. **Check memory trend** - Open the Kubernetes pod memory dashboard in Grafana and examine the memory trend over the past 2-4 hours; a steady upward trend with no GC sawtooth pattern is a strong indicator of a leak.
3. **Correlate with recent deployments** - Check #customer-portal-deployments; a memory leak that appeared after a specific deploy points to a regression introduced in that change.
4. **Identify the leaking process** - Connect to a high-memory pod using `kubectl exec -it [pod-name] -n customer-portal -- node --inspect` and take a heap snapshot; use `clinic.js` or `node-memwatch` if pre-instrumented.
5. **Check for connection pool leaks** - Verify database and Redis connection counts are not growing unboundedly; unclosed connections accumulate in memory alongside the connection object.

## Remediation Steps

1. **Immediate mitigation - cycle the pods**: Run `kubectl rollout restart deployment/customer-portal -n customer-portal` to restart all pods on a rolling basis; this temporarily recovers memory at the cost of brief connection interruptions.
2. **If caused by a recent deploy**: Roll back the deployment to the previous stable image SHA using the portal deploy SOP rollback procedure.
3. **If the leak is in database connections**: Check that the ORM's connection pool `destroy` is called on application shutdown; add `process.on('SIGTERM')` handlers if missing.
4. **Increase memory limits as a temporary measure**: If the leak rate is slow and a fix will ship within hours, update the Kubernetes pod memory limit via the Helm values; this buys time without a rollback.
5. **If cause is unknown after 30 minutes**: Escalate to Portal Tech Lead; do not continue sole investigation under incident pressure.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 10 min | Cycle affected pods to restore immediate memory headroom |
| 15 min | Post root cause hypothesis in #customer-portal-incidents |
| 30 min | If root cause unknown: page Portal Tech Lead |
| 60 min | Engineering Manager paged; plan for permanent fix in next deploy |

## Dashboards

- [Portal Kubernetes Resources](https://grafana.example.com/d/portal-k8s) - Pod memory, CPU, restart count
- [Portal Node.js Heap](https://grafana.example.com/d/portal-nodejs) - Heap used, heap total, GC pause duration
- [Portal Database Connections](https://grafana.example.com/d/portal-db) - Connection pool utilization per pod
- [Portal Pod Logs](https://kibana.example.com/portal-pods) - OOMKilled events and heap snapshot output
