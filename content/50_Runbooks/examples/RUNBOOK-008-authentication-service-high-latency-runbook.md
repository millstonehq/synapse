---
id: RUNBOOK-008
type: runbook
title: Authentication Service High Latency Runbook
status: approved
owner: On-Call Engineer
created: '2025-03-09T04:01:01.353Z'
updated: '2025-12-13T10:48:52.617Z'
tags:
  - runbook
  - user-authentication
summary: Authentication Service High Latency Runbook
example: true
---

## Service

- **System**: [[SYSTEM-006|Identity Provider Service]]
- **Owner team**: Identity and Access Engineering
- **On-call rotation**: PagerDuty schedule "auth-oncall"
- **Slack channel**: #auth-incidents
- **Runtime**: Kubernetes / Node.js 20 / PostgreSQL 15 / Redis 7

## Alerts

- `auth_p99_latency_high` - P99 login latency exceeds 2s for 5 consecutive minutes
- `auth_p95_latency_high` - P95 token validation latency above 500ms for 10 minutes
- `auth_token_issuance_error_rate` - JWT issuance error rate exceeds 0.5% over 3 minutes
- `auth_session_store_unavailable` - Redis session store returning errors for more than 30 seconds
- `auth_db_query_slow` - Median user-lookup query duration exceeds 200ms for 5 minutes

## Diagnosis Steps

1. **Check for recent deploys** - Review #deployments Slack channel and the ArgoCD dashboard for the `auth-api` application. If elevated latency started within 30 minutes of a deploy, treat the deploy as the probable cause and proceed directly to Remediation Step 1.
2. **Inspect error and slow-query logs** - In Kibana filter `service:auth-api` for `level:error` and `level:warn` over the last 15 minutes. Look for JWT signing failures, bcrypt timeout messages, or repeated `ECONNREFUSED` entries pointing to a downstream dependency.
3. **Assess Redis session store health** - Run `redis-cli -h auth-redis ping`. If it responds, check latency with `redis-cli -h auth-redis --latency-history -i 1` and memory pressure with `redis-cli -h auth-redis info memory`. Session cache misses will force every request through the database.
4. **Examine PostgreSQL user-lookup performance** - Connect to the auth DB and run `SELECT pid, now() - query_start AS duration, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC LIMIT 10;`. Identify any slow queries against the `users` or `sessions` tables and check for missing indexes with `EXPLAIN ANALYZE`.
5. **Check Kubernetes pod health and resource usage** - Run `kubectl top pods -n auth` and `kubectl get pods -n auth`. Pods near CPU limits will throttle bcrypt hashing and JWT signing. CrashLooping pods indicate a process-level failure rather than a latency issue.
6. **Verify upstream identity provider connectivity** - If the service federates with an external IdP (SAML/OIDC), confirm the IdP metadata endpoint is reachable and certificate validity has not expired. Check `auth_idp_roundtrip_ms` in Grafana.

## Remediation Steps

1. **If caused by a recent deploy**: Immediately roll back using the ArgoCD UI or `argocd app rollback auth-api`. Do not wait for further diagnosis; restore service first, then investigate the bad revision.
2. **If Redis session store is degraded or down**: Auth pods should fall back to stateless JWT validation. If fallback is not activating, restart pods to clear stuck connection pools: `kubectl rollout restart deployment/auth-api -n auth`. Page the infrastructure on-call if Redis itself needs recovery.
3. **If slow PostgreSQL queries are the cause**: Kill long-running queries with `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE duration > interval '3 minutes' AND state = 'active';`. If the `users` table is missing an index on `email` or `external_id`, apply it immediately on the replica and schedule a primary migration.
4. **If pods are CPU-throttled due to bcrypt load**: Scale out replicas to distribute hashing work: `kubectl scale deployment/auth-api -n auth --replicas=8`. Investigate whether a spike in registration or password-reset traffic is the root cause and consider enabling rate limiting at the gateway.
5. **If the external IdP is unreachable or returning errors**: Enable the `AUTH_IDP_BYPASS_CACHE` feature flag to serve cached identity assertions for up to 15 minutes. Notify the IdP provider's support channel and post status in #auth-incidents.
6. **If the cause remains unknown after 15 minutes**: Escalate immediately per the escalation table below. Capture a heap snapshot and CPU profile from a live pod before restarting: `kubectl exec -n auth <pod> -- node --prof-process`.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert, opens #auth-incidents bridge, begins diagnosis |
| 15 min | If unresolved, page the Auth tech lead via PagerDuty "auth-leads" schedule and post initial RCA hypothesis |
| 30 min | If unresolved, page the Engineering Manager; draft customer-facing status update for affected login flows |
| 60 min | If unresolved, declare major incident, assemble war room in #incident-war-room, and engage DBA and infra on-call |

## Dashboards

- [Auth Service Overview](https://grafana.example.com/d/auth-overview) - P50/P95/P99 latency, token issuance rate, error rate
- [Auth Database Performance](https://grafana.example.com/d/auth-db) - Query duration, connection pool usage, slow-query log
- [Auth Redis Session Store](https://grafana.example.com/d/auth-redis) - Hit rate, eviction count, memory utilization
- [Auth Service Logs](https://kibana.example.com/app/discover#/auth) - Structured error logs with trace IDs for correlation
- [Kubernetes Auth Namespace](https://grafana.example.com/d/k8s-auth) - Pod CPU/memory, throttling events, restart count
