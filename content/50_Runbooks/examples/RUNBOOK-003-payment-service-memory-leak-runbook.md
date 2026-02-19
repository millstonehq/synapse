---
id: RUNBOOK-003
type: runbook
title: Payment Service Memory Leak Runbook
status: draft
owner: On-Call Engineer
created: '2025-05-12T21:08:07.359Z'
updated: '2026-04-22T00:02:47.975Z'
tags:
  - runbook
  - payment-processing
summary: Payment Service Memory Leak Runbook
example: true
---

## Service

- **System**: [[SYSTEM-001|Payment Gateway Service]]
- **Owner team**: Payments Engineering
- **On-call rotation**: PagerDuty schedule "payments-oncall"
- **Slack channel**: #payments-incidents
- **Runtime**: ECS Fargate / Java 21 / Aurora PostgreSQL / ElastiCache

## Alerts

- `PaymentServiceMemoryHigh` — JVM heap usage exceeds 85% of configured max heap for 10 consecutive minutes
- `PaymentServiceOOMKilled` — container OOM kill event detected in the payment service namespace
- `PaymentServiceGCPressureHigh` — JVM GC pause time exceeds 500ms per minute sustained for 5 minutes
- `PaymentServicePodRestartLoop` — pod restart count exceeds 3 in 30 minutes

## Diagnosis Steps

1. **Check current memory metrics** - Open the payment service memory dashboard; review heap usage trend over the past 6 hours to confirm steady growth pattern consistent with a leak.
2. **Correlate with recent deploys** - Check whether the memory growth started after a recent payment service deployment; a new code change is the most likely cause of a new leak.
3. **Review GC logs** - Inspect JVM garbage collection logs for the affected pods; sustained old-gen growth with GC unable to reclaim memory confirms a leak rather than load-driven growth.
4. **Identify leak candidates in heap dump** - If a pod is still running, trigger a heap dump via the JVM diagnostic endpoint; analyze with Eclipse MAT or JVM Profiler for retained object accumulations.
5. **Check for connection or cache leaks** - Look for growing connection pool open counts or unbounded cache entries; payment session caches and database connection pools are common leak sources.

## Remediation Steps

1. **If deploy-correlated**: Roll back to the previous payment service version immediately; monitor heap trend for 30 minutes to confirm stabilization.
2. **If pods are OOM-killing**: Temporarily increase the JVM heap size limit in the deployment config to stabilize the service; this buys time for investigation without causing downtime.
3. **If connection pool leak confirmed**: Restart the affected pods with a rolling restart; implement a connection pool timeout fix and deploy as a hotfix.
4. **If GC pressure is causing latency impact**: Enable GC log collection and trigger a graceful pod rotation to reset heap state; monitor payment latency recovery.
5. **If leak cannot be identified quickly**: Schedule a rolling restart every 4 hours as a mitigation while engineering investigates the root cause; file a P1 bug ticket.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer checks heap metrics and recent deploys |
| 15 min | If OOM kills are occurring and payment latency is impacted, notify Engineering Manager |
| 30 min | Engineering Manager engages senior payments engineer for deep leak investigation |
| 60 min | If not stabilized, declare incident and implement rolling restart mitigation |

## Dashboards

- [Payment Service JVM Metrics](https://grafana.example.com/d/payment-jvm) - Heap usage, GC frequency, and GC pause time
- [Payment Service Pod Health](https://grafana.example.com/d/payment-pods) - Pod restarts, OOM events, and resource utilization
- [Payment Latency Impact](https://grafana.example.com/d/payment-latency) - P95/P99 authorization latency during GC pressure events
