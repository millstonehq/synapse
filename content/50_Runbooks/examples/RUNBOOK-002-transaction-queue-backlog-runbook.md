---
id: RUNBOOK-002
type: runbook
title: Transaction Queue Backlog Runbook
status: approved
owner: On-Call Engineer
created: '2025-11-02T03:59:25.343Z'
updated: '2026-08-20T17:19:21.715Z'
tags:
  - runbook
  - payment-processing
summary: Transaction Queue Backlog Runbook
example: true
---

## Service

- **System**: [[SYSTEM-001|Payment Gateway Service]]
- **Owner team**: Payments Engineering
- **On-call rotation**: PagerDuty schedule "payments-oncall"
- **Slack channel**: #payments-incidents
- **Runtime**: ECS Fargate / Java 21 / Aurora PostgreSQL / ElastiCache

## Alerts

- `TransactionQueueDepthHigh` — queue depth exceeds 5,000 messages sustained for 5 minutes
- `TransactionProcessingLagHigh` — oldest message in queue is more than 2 minutes old
- `TransactionConsumerDead` — no consumer heartbeat received for 90 seconds
- `TransactionQueueDLQGrowing` — dead-letter queue message count increasing (new failures accumulating)

## Diagnosis Steps

1. **Check consumer count and health** - Verify the number of active transaction queue consumers; a drop in consumer count (pod crashes, OOM kills) is the most common cause of backlog buildup.
2. **Review consumer error logs** - Query logs for the queue consumer service for panic, OOM, or repeated error patterns that indicate consumers are crashing on specific message types.
3. **Inspect DLQ contents** - Sample messages from the dead-letter queue to identify if a specific transaction type or payload format is causing repeated consumer failures.
4. **Check downstream gateway latency** - If consumers are running but slow, check gateway response latency; slow gateway responses reduce consumer throughput and cause backlog growth.
5. **Assess database write latency** - High database write latency in the payment ledger service causes consumer processing to slow; check `db_write_latency_p95` metric.

## Remediation Steps

1. **If consumer count is low**: Scale up the transaction consumer deployment to the maximum configured replica count; monitor queue depth over 10 minutes.
2. **If consumers are crashing on a specific message type**: Identify the problematic message pattern from DLQ sampling; deploy a fix or move affected messages to a manual review queue.
3. **If gateway is slow**: Reduce consumer concurrency to avoid gateway rate limiting; enable queue throttling in the consumer configuration.
4. **If database write latency is high**: Check for long-running transactions or lock contention in the payment database; kill offending queries with DBA approval if necessary.
5. **If backlog exceeds 20,000 messages**: Notify Engineering Manager; consider temporarily pausing new transaction intake to allow the backlog to drain before resuming.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and checks consumer health |
| 15 min | If queue depth still growing, notify Engineering Manager |
| 30 min | Engineering Manager assesses impact on payment SLOs; escalate to Director if SLO breach |
| 60 min | Director of Engineering declares incident; customer communication initiated |

## Dashboards

- [Transaction Queue Metrics](https://grafana.example.com/d/txn-queue) - Queue depth, consumer count, and processing lag
- [Consumer Service Health](https://grafana.example.com/d/consumer-health) - Consumer throughput, error rate, and pod restarts
- [Payment Database Performance](https://grafana.example.com/d/payment-db) - Write latency, lock waits, and connection utilization
