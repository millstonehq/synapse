---
id: RUNBOOK-057
type: runbook
title: Customer Portal High Response Time Runbook
status: approved
owner: On-Call Engineer
created: '2025-05-03T00:01:07.731Z'
updated: '2025-04-30T08:36:22.439Z'
tags:
  - runbook
  - customer-portal
summary: Customer Portal High Response Time Runbook
example: true
---

## Service

- **System**: [[SYSTEM-041|Customer Portal]]
- **Owner team**: Customer Experience Engineering
- **On-call rotation**: PagerDuty schedule "customer-portal-oncall"
- **Slack channel**: #customer-portal-incidents
- **Runtime**: Kubernetes / Node.js 20 / PostgreSQL 15 / Redis 7 / React 18

## Alerts

- `portal_response_time_p95_high` - P95 response time exceeds 3s for 5 consecutive minutes
- `portal_response_time_p99_critical` - P99 response time exceeds 8s for 3 consecutive minutes
- `portal_5xx_rate_elevated` - HTTP 5xx error rate exceeds 2% of requests over 5 minutes
- `portal_db_slow_query_rate` - Slow query count (>1s) exceeds 20 per minute
- `portal_upstream_timeout_rate` - Timeout errors to backend APIs exceed 5% of calls over 3 minutes

## Diagnosis Steps

1. **Check recent deployments** - Review #deployments Slack channel and the ArgoCD dashboard for any portal or backend service deploys in the last 60 minutes. If the latency spike correlates with a deploy timestamp, treat that deploy as the primary suspect and proceed to rollback.
2. **Review application error logs** - In Kibana, filter by `service:customer-portal` and `level:error` for the past 30 minutes. Look for repeated timeout messages, upstream API errors, or unhandled exception traces that indicate a specific failing code path.
3. **Inspect database performance** - Connect to the portal PostgreSQL replica and run `SELECT pid, now() - query_start AS duration, state, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC LIMIT 10;`. Long-running queries or a high active connection count (above 80 of the 100-connection pool) indicate DB saturation.
4. **Check Redis session and cache health** - Run `redis-cli -h portal-redis info stats` and examine `keyspace_hits` vs `keyspace_misses`. A sudden drop in hit rate forces all traffic to the DB, compounding latency. Also confirm Redis memory usage is below 85% with `redis-cli -h portal-redis info memory`.
5. **Inspect upstream API dependencies** - The portal calls the User Service, Content Delivery API, and Billing Service. Check the status dashboards for each. If any upstream is returning elevated 5xx rates or timeouts, the portal's response time will follow directly.
6. **Check Kubernetes pod resource utilisation** - Run `kubectl top pods -n customer-portal` and compare CPU and memory against resource limits. Pods near their CPU limit will throttle and inflate response times even when the application itself is healthy.

## Remediation Steps

1. **If a recent deployment is the cause**: Initiate a rollback immediately via ArgoCD by selecting the previous healthy revision and clicking Sync. Do not spend time on further diagnosis before rolling back — restoring service to users takes priority.
2. **If slow database queries are the cause**: Terminate the longest-running queries with `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE now() - query_start > interval '3 minutes' AND state = 'active';`, then restart portal pods to reset connection pool state: `kubectl rollout restart deployment/customer-portal -n customer-portal`.
3. **If Redis is degraded or unavailable**: Confirm whether the portal is falling back to DB reads. If not, restart pods to re-initialise the Redis client. If Redis itself is unhealthy, page the infrastructure on-call via PagerDuty schedule "infra-oncall" and do not attempt self-remediation of the Redis cluster.
4. **If an upstream API (User Service, Billing Service) is the source**: Verify whether circuit breakers are open by checking the portal's `/health/dependencies` endpoint. If the upstream outage exceeds 10 minutes, enable the portal maintenance banner via the feature flag `portal.maintenance_mode=true` in LaunchDarkly to prevent further user-facing errors.
5. **If pods are CPU or memory constrained**: Scale the deployment horizontally: `kubectl scale deployment/customer-portal -n customer-portal --replicas=8`. Monitor response time in Grafana to confirm relief. Investigate root cause (traffic spike, memory leak) once stability is restored.
6. **If cause remains unidentified after 15 minutes**: Stop solo investigation and escalate immediately. Document current findings in #customer-portal-incidents before paging the tech lead.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges the alert and begins diagnosis using this runbook |
| 15 min | If not resolved, page the Customer Portal tech lead via PagerDuty "portal-leads" schedule and post a status update in #customer-portal-incidents |
| 30 min | If not resolved, page the Engineering Manager and begin drafting customer-facing status page update |
| 60 min | If not resolved, declare a major incident, open war room in #incident-war-room, and engage Customer Success to notify affected enterprise accounts |

## Dashboards

- [Customer Portal Overview](https://grafana.example.com/d/portal-overview) - Request rate, P95/P99 latency, error rate, and apdex score
- [Customer Portal Database](https://grafana.example.com/d/portal-db) - Active connections, slow query count, connection pool utilisation, replication lag
- [Customer Portal Redis](https://grafana.example.com/d/portal-redis) - Cache hit rate, memory usage, eviction rate, connected clients
- [Customer Portal Logs](https://kibana.example.com/app/discover#/customer-portal) - Filterable application error and access logs with full stack traces
- [Kubernetes Customer Portal Namespace](https://grafana.example.com/d/k8s-portal) - Pod health, CPU/memory utilisation, restart counts, and HPA scaling events
