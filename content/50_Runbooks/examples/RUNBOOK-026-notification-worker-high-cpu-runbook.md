---
id: RUNBOOK-026
type: runbook
title: Notification Worker High CPU Runbook
status: draft
owner: On-Call Engineer
created: '2025-08-08T08:34:48.622Z'
updated: '2025-06-22T05:10:51.710Z'
tags:
  - runbook
  - notification-service
summary: Notification Worker High CPU Runbook
example: true
---

## Service

- **System**: [[SYSTEM-016|Notification Service]]
- **Owner team**: Notification Service Engineering
- **On-call rotation**: PagerDuty schedule "notifications-oncall"
- **Slack channel**: #notifications-incidents
- **Runtime**: Kubernetes / Node.js 20 / PostgreSQL 15

## Alerts

- `notification_worker_cpu_high` - Worker pod CPU utilization exceeds 85% for more than 5 minutes
- `notification_worker_throttled` - CPU throttling rate exceeds 20% on any worker pod
- `notification_processing_rate_drop` - Message processing rate drops more than 30% from baseline
- `notification_worker_oom_kill` - Worker pod OOM killed in the past 10 minutes

## Diagnosis Steps

1. **Identify which worker pods are affected** - Run `kubectl top pods -n notifications -l component=notification-worker` to see current CPU usage per pod and identify the highest-consuming pods.
2. **Check for a traffic spike** - Review the queue publish rate on the notification queues dashboard. A sudden increase in incoming message volume would cause legitimate CPU increases on the worker pods.
3. **Check for a runaway template rendering loop** - Review worker logs for repeated rendering errors or infinite retry patterns. A template that causes exceptions may be retried in a tight loop, consuming CPU.
4. **Check for a recent code deployment** - Review `#notifications-releases` for recent worker deployments. CPU regressions often coincide with code changes that introduced inefficient processing paths.
5. **Check for database query contention** - Review the Notification Service database dashboard for long-running queries or high connection pool utilization that could be causing workers to spin on retries.

## Remediation Steps

1. **If CPU is high due to legitimate traffic spike**: Scale up the worker deployment to distribute load — `kubectl scale deployment/notification-worker -n notifications --replicas=10`. Monitor that CPU per pod drops after scaling.
2. **If a runaway retry loop is causing the CPU spike**: Identify the notification type or template causing the loop in the logs, and temporarily disable that notification type via the feature flag while the root cause is investigated.
3. **If a recent deployment caused a CPU regression**: Roll back the deployment using the deployment rollback procedure and verify CPU returns to baseline.
4. **If OOM kills are occurring alongside high CPU**: Increase the memory limit on the worker pods via a configuration change and trigger a rolling restart; investigate the memory leak in parallel.
5. **If the cause is a database query hotspot**: Page the database on-call to investigate and add appropriate indexing or query optimization.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 10 min | Post initial assessment in #notifications-incidents |
| 20 min | If not resolved: page Notification Service Platform Lead |
| 40 min | If delivery rate is degrading: page Engineering Manager |
| 60 min | Major incident if workers are completely unavailable |

## Dashboards

- [Notification Worker Resources](https://grafana.example.com/d/notification-workers) - CPU, memory, throttling per pod
- [Notification Processing Rate](https://grafana.example.com/d/notification-processing) - Messages processed per second, error rate
- [Notification Database](https://grafana.example.com/d/notification-db) - Query duration, connection pool, lock waits
- [Kubernetes Notifications Namespace](https://grafana.example.com/d/k8s-notifications) - Pod health, resource usage, restarts
