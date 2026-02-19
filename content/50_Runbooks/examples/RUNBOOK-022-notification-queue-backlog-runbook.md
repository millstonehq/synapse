---
id: RUNBOOK-022
type: runbook
title: Notification Queue Backlog Runbook
status: approved
owner: On-Call Engineer
created: '2025-12-03T03:15:05.863Z'
updated: '2026-10-20T04:38:11.605Z'
tags:
  - runbook
  - notification-service
summary: Notification Queue Backlog Runbook
example: true
---

## Service

- **System**: [[SYSTEM-016|Notification Service]]
- **Owner team**: Notification Service Engineering
- **On-call rotation**: PagerDuty schedule "notifications-oncall"
- **Slack channel**: #notifications-incidents
- **Runtime**: Kubernetes / Node.js 20 / PostgreSQL 15 / SQS

## Alerts

- `notification_queue_depth_high` - Queue depth exceeds 10,000 messages for more than 10 minutes
- `notification_consumer_lag_high` - Consumer processing lag exceeds 30 minutes
- `notification_worker_restarts` - Worker pod restarting more than 3 times in 15 minutes
- `notification_dlq_depth_high` - Dead-letter queue depth exceeds 500 messages

## Diagnosis Steps

1. **Check queue depth by channel** - In the SQS console, check queue depths for email, push, and SMS queues separately. Identify which channel(s) are backlogged to narrow the cause.
2. **Check worker pod health** - Run `kubectl top pods -n notifications` and `kubectl get pods -n notifications` to identify crashed or resource-constrained worker pods contributing to slow consumption.
3. **Check for provider-side slowdown** - Review Notification Service logs for elevated provider response times or rate limit responses. If the provider is throttling, the backlog will grow faster than workers can drain it.
4. **Check for runaway event producer** - Look for abnormally high message publish rates in the queue publish metrics. A bug in an upstream service may be flooding the queue with duplicate or invalid events.
5. **Check message age distribution** - In the SQS console, check the approximate age of oldest message. If messages are older than the TTL, the backlog may be partially composed of expired items that need to be drained.

## Remediation Steps

1. **If worker pods are crashed or insufficient**: Scale up the notification worker deployment — `kubectl scale deployment/notification-worker -n notifications --replicas=8` — and confirm pods start successfully.
2. **If provider is rate-limiting**: Reduce worker concurrency via configuration to stay within provider limits, and notify the Platform Lead to assess whether the backlog will drain before SLA breach.
3. **If a runaway producer is flooding the queue**: Identify and pause the upstream service emitting the excessive events. Purge duplicate/invalid messages from the queue before resuming processing.
4. **If the backlog contains expired messages**: Execute the Notification Queue Drain SOP to remove expired items and allow workers to catch up on valid messages.
5. **If cause is unknown after 15 minutes**: Escalate to the Notification Service Platform Lead immediately.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 10 min | Post initial assessment in #notifications-incidents |
| 20 min | If not resolved: page the Notification Service Platform Lead via PagerDuty |
| 40 min | If not resolved: page Engineering Manager and assess customer impact |
| 60 min | If SLA breach confirmed: initiate major incident process |

## Dashboards

- [Notification Queue Depth](https://grafana.example.com/d/notification-queues) - Queue depth per channel, consumer lag, DLQ depth
- [Notification Worker Health](https://grafana.example.com/d/notification-workers) - Pod restarts, CPU, memory, processing rate
- [Notification Delivery Rates](https://grafana.example.com/d/notification-delivery) - Delivery success rate by channel
- [SQS Queue Metrics](https://grafana.example.com/d/notification-sqs) - Publish rate, receive rate, oldest message age
