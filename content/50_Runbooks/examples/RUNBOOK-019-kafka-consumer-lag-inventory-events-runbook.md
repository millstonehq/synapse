---
id: RUNBOOK-019
type: runbook
title: Kafka Consumer Lag Inventory Events Runbook
status: draft
owner: On-Call Engineer
created: '2025-01-13T01:04:55.584Z'
updated: '2025-07-03T10:21:30.340Z'
tags:
  - runbook
  - inventory-management
summary: Kafka Consumer Lag Inventory Events Runbook
example: true
---

## Service

- **System**: [[SYSTEM-011|Inventory Tracking Service]]
- **Owner team**: Inventory Engineering
- **On-call rotation**: PagerDuty schedule "inventory-oncall"
- **Slack channel**: #inventory-incidents
- **Runtime**: Kubernetes / Go 1.22 / ClickHouse / Kafka

## Alerts

- `inventory_kafka_consumer_lag_critical` - Consumer group `inventory-events-processor` lag exceeds 100,000 messages for 10 minutes
- `inventory_kafka_consumer_lag_warning` - Consumer lag exceeds 20,000 messages for 5 minutes (early warning)
- `inventory_kafka_consumer_no_progress` - Consumer has committed zero offsets for 5 minutes during expected processing hours
- `inventory_events_dlq_depth_high` - Dead letter queue for inventory events contains more than 500 messages

## Diagnosis Steps

1. **Measure lag per partition** - Run: `kafka-consumer-groups.sh --bootstrap-server [broker] --group inventory-events-processor --describe`. Identify if lag is concentrated in specific partitions or spread evenly; concentrated lag suggests a hot partition or a stuck consumer.
2. **Check inventory event processor pod health** - Run `kubectl get pods -n inventory -l app=inventory-event-processor`. Look for crash loops or pods stuck in `Pending` state. Check recent restart count.
3. **Check event processor logs for errors** - Run `kubectl logs -n inventory -l app=inventory-event-processor --since=15m`. Look for deserialization errors (bad message format), ClickHouse write errors, or resource exhaustion messages.
4. **Inspect the dead letter queue** - If DLQ depth is high, examine the messages in the DLQ. Repeated deserialization failures indicate a schema change in the event producer that the consumer cannot handle.
5. **Check producer throughput** - Verify that the upstream event producers (warehouse adapters, sync service) have not experienced a sudden traffic spike that is overwhelming the consumer's normal throughput capacity.

## Remediation Steps

1. **If consumer pods are crashlooping** - Check logs for the crash reason. OOM: increase memory limit temporarily via `kubectl edit deployment/inventory-event-processor -n inventory`. Bad message causing panic: route that message to the DLQ via the admin skip endpoint and restart pods.
2. **If DLQ is accumulating deserialization errors** - This indicates a schema mismatch. Do not restart consumers; the problem will persist. Identify which producer changed their schema, notify the producing team, and pause the consumer group until the schema issue is resolved: `kafka-consumer-groups.sh --bootstrap-server [broker] --group inventory-events-processor --execute --reset-offsets --to-datetime [pre-issue-timestamp]`.
3. **If lag is growing due to throughput spike** - Scale up consumer replicas: `kubectl scale deployment/inventory-event-processor -n inventory --replicas=[N+2]`. Consumer group rebalancing will occur automatically.
4. **If ClickHouse write failures are causing lag** - The consumer is processing but cannot write to ClickHouse. Follow the diagnosis steps in the Inventory Sync Lag Runbook for ClickHouse-specific remediation.
5. **If a hot partition is the cause** - This requires a longer-term fix (repartitioning). As an immediate measure, scale consumers to match partition count to ensure one consumer per partition.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer checks lag per partition and consumer pod health |
| 10 min | Post lag magnitude and initial finding in #inventory-incidents |
| 20 min | If lag exceeds 100k and is still growing: page Inventory tech lead |
| 45 min | If DLQ is accumulating and schema issue suspected: page event producer team lead |
| 60 min | If consumer lag will breach data freshness SLA: escalate to Engineering Manager |

## Dashboards

- [Inventory Kafka Consumer](https://grafana.example.com/d/inventory-kafka) - Consumer lag by partition, offset commit rate, DLQ depth
- [Kafka Broker Health](https://grafana.example.com/d/kafka-brokers) - Broker health, throughput, under-replicated partitions
- [Inventory Event Processor](https://grafana.example.com/d/inventory-event-proc) - Processing rate, error rate, pod health
- [Inventory ClickHouse](https://grafana.example.com/d/inventory-clickhouse) - Write throughput, error rate, disk usage
