---
id: RUNBOOK-068
type: runbook
title: Billing Event Processing Lag Runbook
status: approved
owner: On-Call Engineer
created: '2024-06-05T21:45:41.489Z'
updated: '2026-06-26T21:18:14.498Z'
tags:
  - runbook
  - billing-engine
summary: Billing Event Processing Lag Runbook
example: true
---

## Service

- **System**: [[SYSTEM-050|Billing Engine]]
- **Owner team**: Billing Platform Engineering
- **On-call rotation**: PagerDuty schedule "billing-oncall"
- **Slack channel**: #billing-incidents
- **Runtime**: Kubernetes / Java 21 / PostgreSQL 15 / Kafka

## Alerts

- `billing_event_consumer_lag_high` - Billing event consumer group lag exceeds 10,000 messages
- `billing_event_processing_latency_high` - Billing event end-to-end processing latency (publish to DB write) above 2 minutes for 10 minutes
- `billing_event_consumer_group_rebalancing` - Consumer group has been rebalancing for more than 5 minutes continuously
- `billing_revenue_recognition_event_delay` - Revenue recognition events are more than 30 minutes behind invoice finalization events

## Diagnosis Steps

1. **Check Kafka consumer group lag** - On the Billing Kafka Consumers dashboard, find the `billing-event-consumer` group and identify which partitions have the highest lag. Note whether all partitions are lagging (capacity issue) or only specific partitions (poison pill or partition imbalance).
2. **Check for rebalancing** - Frequent consumer rebalancing prevents any consumer from making forward progress. Check for recent billing service pod restarts that may be causing unstable group membership: `kubectl get events -n billing | grep billing-event-consumer`.
3. **Check consumer pod health and throughput** - Review billing event consumer pod metrics: messages consumed per second. If throughput has dropped significantly without a lag increase preceding it, check for a poison pill message.
4. **Check for poison pill messages** - A single malformed event can block an entire partition. Check the consumer logs for repeated errors processing the same offset: filter by `service:billing-event-consumer` and `level:error`. If the same offset is retried repeatedly, skip it to a dead-letter topic.
5. **Check downstream systems for back-pressure** - If the consumer is reading events but processing is slow, the bottleneck may be in the billing database write path or in a downstream service (e.g., revenue recognition ledger).

## Remediation Steps

1. **If all partitions are lagging due to insufficient consumer capacity**: Scale up the `billing-event-consumer` deployment: `kubectl scale deployment/billing-event-consumer -n billing --replicas=8`. Ensure replicas do not exceed partition count (12 partitions).
2. **If rebalancing is continuous due to pod instability**: Identify and fix the cause of pod restarts (OOM, config error). Temporarily reduce the `session.timeout.ms` in the consumer config to allow faster rebalance completion while pods stabilize.
3. **If a poison pill is blocking a partition**: Skip the problematic offset by manually committing the consumer offset past the bad message: use the `billing-kafka-admin` tool with `--skip-offset` for the specific partition. The skipped message is sent to the billing event DLQ.
4. **If the billing database is causing back-pressure**: Check billing DB query latency and connection pool. If DB writes are slow, check for lock contention or a slow query. Scale or optimize as needed before the consumer lag will clear.
5. **If revenue recognition events are specifically delayed**: Check the revenue recognition service health separately. A healthy Kafka consumer lag but delayed revenue events indicates the revenue recognition service is the bottleneck.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer checks consumer lag and identifies partition pattern |
| 15 min | Post assessment in #billing-incidents: lag magnitude, estimated catch-up time, partition count affected |
| 30 min | If lag exceeds 1 hour of events and is growing: page Billing Platform tech lead |
| 45 min | If revenue recognition events are delayed at month-end: notify Finance Operations |
| 60 min | If not recovering: page Engineering Manager for escalation to infrastructure team |

## Dashboards

- [Billing Kafka Consumers](https://grafana.example.com/d/billing-kafka) - Consumer group lag by partition, throughput, rebalance events
- [Billing Event Processing](https://grafana.example.com/d/billing-event-processing) - End-to-end event latency, DLQ depth
- [Billing Database](https://grafana.example.com/d/billing-db) - Write throughput, query latency, connection pool
- [Billing Event Consumer Logs](https://kibana.example.com/app/discover#/billing-event-consumer) - Consumer error logs, offset details
