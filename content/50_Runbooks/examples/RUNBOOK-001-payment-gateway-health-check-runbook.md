---
id: RUNBOOK-001
type: runbook
title: Payment Gateway Health Check Runbook
status: approved
owner: On-Call Engineer
created: '2024-02-16T01:31:13.483Z'
updated: '2026-01-16T11:37:14.214Z'
tags:
  - runbook
  - payment-processing
summary: Payment Gateway Health Check Runbook
example: true
---

## Service

- **System**: [[SYSTEM-001|Payment Gateway Service]]
- **Owner team**: Payments Engineering
- **On-call rotation**: PagerDuty schedule "payments-oncall"
- **Slack channel**: #payments-incidents
- **Runtime**: ECS Fargate / Java 21 / Aurora PostgreSQL / ElastiCache

## Alerts

- `PaymentGatewayHealthCheckFailed` — gateway health endpoint returns non-2xx for 3 consecutive checks (30-second interval)
- `PaymentGatewayLatencyHigh` — P95 gateway response time exceeds 2,000ms sustained for 5 minutes
- `PaymentGatewaySuccessRateLow` — authorization success rate falls below 95% for any 5-minute window
- `PaymentGatewayConnectionPoolExhausted` — available gateway connection pool drops below 10%

## Diagnosis Steps

1. **Check gateway status page** - Navigate to the gateway provider's status page to determine if there is an active provider-side incident affecting the region.
2. **Review recent health check logs** - Query the payment service logs for `health_check` events in the past 15 minutes; look for timeout patterns, DNS resolution failures, or TLS errors.
3. **Check certificate validity** - Confirm the gateway endpoint SSL certificate has not expired using `openssl s_client`; an expired cert produces consistent connection failures.
4. **Inspect connection pool metrics** - Check the payment service connection pool dashboard for pool exhaustion or slow connection acquisition times indicating resource contention.
5. **Correlate with recent deploys** - Review the deployment log for any payment service or gateway configuration changes in the past 2 hours.

## Remediation Steps

1. **If gateway provider incident is confirmed**: Enable gateway failover routing per the failover policy; notify Engineering Manager; monitor until provider resolves.
2. **If TLS/certificate issue**: Trigger the SSL certificate renewal runbook; do not route traffic to the affected endpoint until certificate is valid.
3. **If connection pool exhausted**: Scale the payment service horizontally by increasing the replica count by 2; monitor pool recovery over 5 minutes.
4. **If deploy-correlated**: Roll back the payment service to the previous image tag; confirm health checks recover within 3 minutes of rollback.
5. **If no clear cause**: Restart the payment service pods with a rolling restart; if health checks do not recover after restart, escalate to the payments on-call senior engineer.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 15 min | If unresolved, notify Engineering Manager via Slack DM |
| 30 min | Engineering Manager escalates to Director of Engineering; consider gateway failover |
| 60 min | Director of Engineering declares P1 incident; full incident response team engaged |

## Dashboards

- [Payment Gateway Health Overview](https://grafana.example.com/d/payment-gateway-health) - Success rates, latency, and health check status by gateway
- [Payment Service Connection Pools](https://grafana.example.com/d/payment-connections) - Connection pool utilization and acquisition latency
- [Gateway Latency Breakdown](https://grafana.example.com/d/gateway-latency) - P50/P95/P99 latency by gateway and endpoint
