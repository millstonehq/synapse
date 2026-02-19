---
id: RUNBOOK-011
type: runbook
title: Login Spike Investigation Runbook
status: draft
owner: On-Call Engineer
created: '2024-10-17T16:15:40.688Z'
updated: '2025-05-02T14:03:38.718Z'
tags:
  - runbook
  - user-authentication
summary: Login Spike Investigation Runbook
example: true
---

## Service

- **System**: [[SYSTEM-006|Identity Provider Service]]
- **Owner team**: Platform Engineering
- **On-call rotation**: PagerDuty schedule "auth-oncall"
- **Slack channel**: #auth-incidents
- **Runtime**: Kubernetes / Node.js 20 / Redis 7 / DynamoDB

## Alerts

- `auth_login_rps_spike` - Login requests per second exceed 5x the rolling baseline for 2 minutes
- `auth_service_cpu_high` - Authentication service CPU utilization exceeds 80% for 3 minutes
- `auth_db_connection_pool_high` - Authentication database connection pool utilization above 85%
- `auth_rate_limiter_triggered` - Global rate limiter is rejecting more than 5% of login requests

## Diagnosis Steps

1. **Determine spike origin** - In Grafana, view the `auth_login_rps` metric grouped by `source_ip` and `user_agent`. Determine whether the spike is from a distributed set of user IPs (legitimate traffic) or a small number of IPs (bot/attack traffic).
2. **Check for a product event or announcement** - Verify with the product team whether a marketing campaign, product launch, or scheduled email was sent that could explain a legitimate traffic spike.
3. **Check for credential stuffing patterns** - In Kibana, filter for `event_type:login_failed` and review the failure rate. If the failure rate is above 20% of total login attempts, this is likely a credential stuffing attack; proceed to Remediation Step 2.
4. **Check authentication service resource utilization** - Run `kubectl top pods -n auth` to check CPU and memory. If pods are near resource limits, scale up immediately while continuing diagnosis.
5. **Check downstream dependencies** - Verify the authentication database and session store are healthy. Elevated login traffic may saturate the database connection pool; check `auth_db_connection_pool_utilization` in Grafana.

## Remediation Steps

1. **If legitimate traffic spike**: Scale up authentication service replicas immediately: `kubectl scale deployment/auth-service -n auth --replicas=8`. Monitor resource utilization after scaling.
2. **If credential stuffing attack**: Enable the enhanced rate limiting profile (`AUTH_RATE_LIMIT_PROFILE=strict`) which reduces per-IP login attempts to 3 per minute. Notify the security team to begin brute force investigation (SOP-013).
3. **If database connection pool is saturated**: Reduce authentication service replicas temporarily to ease DB connection pressure, then scale the database connection pooler (PgBouncer) if available.
4. **If autoscaling is insufficient**: Enable the authentication service degraded mode which serves cached session validations and rate-limits new login attempts to protect service stability.
5. **If cause is unknown after 10 minutes**: Escalate to the Platform Lead immediately and enable traffic capture on one pod for detailed analysis.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and pulls login RPS breakdown |
| 5 min | Determine if legitimate or attack traffic; post in #auth-incidents |
| 15 min | If not resolved: page Platform Lead via PagerDuty |
| 30 min | If attack traffic: notify Security Engineer and CISO; if legitimate: notify Engineering Manager |
| 60 min | Escalate to Director of Engineering; assess broader impact on product availability |

## Dashboards

- [Auth Service Overview](https://grafana.example.com/d/auth-overview) - Login RPS, success rate, error rate, latency
- [Auth Service Resources](https://grafana.example.com/d/auth-resources) - CPU, memory, pod count, autoscaling status
- [Auth Rate Limiting](https://grafana.example.com/d/auth-rate-limit) - Rate limiter triggers, blocked IPs, per-IP request rates
