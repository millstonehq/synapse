---
id: service-outage-runbook
type: runbook
title: Service Outage (Payments API)
status: approved
owner: On-Call Engineer
created: '2025-10-18T00:00:00.000Z'
updated: '2025-10-18T00:00:00.000Z'
tags:
  - runbook
  - incidents
  - payments
summary: >-
  Diagnose and remediate outages impacting the Payments API. USE A
  RUNBOOK when something is BROKEN or an alert is firing and someone
  needs to diagnose and fix it under pressure. Runbooks answer "an alert
  just fired - now what?" They are incident-response documents tied to
  a specific service, with diagnosis trees, remediation steps, and
  escalation paths. Compare: an SOP is for planned operational tasks
  (deploying, migrating); a Process defines the governance around who
  can do what; a Guide teaches the concepts. Runbooks assume something
  unexpected happened and the reader needs to fix it NOW.
example: true
---

## Service

- **System**: [[SYSTEM-001|Payment Gateway Service]]
- **Owner team**: Payments Engineering
- **On-call rotation**: PagerDuty schedule "payments-oncall"
- **Slack channel**: #payments-incidents
- **Runtime**: Kubernetes / Go 1.21 / PostgreSQL 14 / Redis 7

## Alerts

- `payments_5xx_rate_high` - 5xx error rate exceeds 1% for 3 minutes
- `payments_latency_p95_high` - P95 latency above 1s for 5 minutes
- `payments_pod_crashloop` - Pod restarting more than 3 times in 10 minutes
- `payments_db_connection_pool_exhausted` - Available DB connections below 5%
- `payments_queue_depth_high` - SQS dead letter queue depth exceeds 100 messages

## Diagnosis Steps

1. **Check if a recent deploy happened** - Look at #deployments channel and the ArgoCD dashboard. If the issue started within 30 minutes of a deploy, the deploy is the likely cause. Skip to Remediation Step 1 (rollback).
2. **Check the error logs** - In Kibana, filter by `service:payments-api` and `level:error` for the last 30 minutes. Look for: repeated stack traces (code bug), connection timeout errors (dependency issue), or OOM killed messages (resource exhaustion).
3. **Check database health** - Run `SELECT count(*) FROM pg_stat_activity WHERE state = 'active';` on the payments DB. If active connections are near the pool max (100), the DB is saturated. Check for long-running queries with `SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC LIMIT 5;`
4. **Check Redis health** - Verify Redis is responding: `redis-cli -h payments-redis ping`. Check memory usage: `redis-cli -h payments-redis info memory`. If memory is above 80%, eviction pressure may be causing cache misses.
5. **Check upstream dependencies** - Verify the auth service, notification service, and payment gateway are healthy. Check their status pages and recent deploy history. If an upstream dependency is down, the payments API may be failing on calls to that service.
6. **Check Kubernetes resource pressure** - Run `kubectl top pods -n payments` to check CPU and memory. If pods are near limits, the service may need scaling or there may be a resource leak.

## Remediation Steps

1. **If caused by a recent deploy**: Roll back immediately using the [[example-production-deployment-sop|Production Deployment SOP]] rollback procedure. Do not wait - roll back first, investigate later.
2. **If database connection pool is exhausted**: Kill long-running queries with `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE duration > interval '5 minutes' AND state = 'active' AND query NOT LIKE '%pg_stat%';`. Then restart pods to reset connection pools: `kubectl rollout restart deployment/payments-api -n payments`.
3. **If Redis is down or degraded**: The payments API should degrade gracefully (bypass cache, hit DB directly). If it's not degrading gracefully, this is a code bug - restart pods as a temporary fix and file a bug ticket. If Redis itself needs recovery, page the infrastructure on-call.
4. **If upstream dependency is down**: Check if the payments API has circuit breakers configured for that dependency. If not, the API will keep retrying and exhausting its own resources. Restart pods to clear stuck connections. If the upstream outage is prolonged (>15 min), consider enabling the maintenance page.
5. **If pods are resource-constrained**: Scale up replicas: `kubectl scale deployment/payments-api -n payments --replicas=6`. This buys time while you investigate the root cause (memory leak, traffic spike, etc).
6. **If cause is unknown after 15 minutes of diagnosis**: Escalate immediately. Do not spend more time diagnosing alone.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 5 min | Post initial assessment in #payments-incidents |
| 15 min | If not resolved: page the Payments tech lead via PagerDuty |
| 30 min | If not resolved: page the Engineering Manager, begin customer communication |
| 60 min | If not resolved: initiate major incident process, assemble war room in #incident-war-room |

**Who to escalate to:**
- Payments tech lead: PagerDuty schedule "payments-leads"
- Infrastructure issues (K8s, networking): PagerDuty schedule "infra-oncall"
- Database issues: PagerDuty schedule "dba-oncall"
- External payment gateway issues: Contact gateway support at support@gateway.example.com with merchant ID

## Dashboards

- [Payments API Overview](https://grafana.example.com/d/payments-overview) - Error rates, latency, throughput
- [Payments Database](https://grafana.example.com/d/payments-db) - Connection pool, query duration, replication lag
- [Payments Redis](https://grafana.example.com/d/payments-redis) - Hit rate, memory, evictions
- [Payments API Logs](https://kibana.example.com/app/discover#/payments) - Error logs with full stack traces
- [Kubernetes Payments Namespace](https://grafana.example.com/d/k8s-payments) - Pod health, resource usage, restarts
