---
id: RUNBOOK-042
type: runbook
title: Kafka Broker Disk Full Runbook
status: approved
owner: On-Call Engineer
created: '2024-12-30T12:05:36.020Z'
updated: '2026-02-19T08:36:12.615Z'
tags:
  - runbook
  - data-pipeline
summary: Kafka Broker Disk Full Runbook
example: true
---

## Service

- **System**: [[SYSTEM-026|Kafka Cluster]]
- **Owner team**: Data Platform Engineering
- **On-call rotation**: PagerDuty schedule "data-platform-oncall"
- **Slack channel**: #kafka-incidents
- **Runtime**: Kafka 3.5 / Kubernetes / EBS volumes

## Alerts

- `kafka_broker_disk_usage_critical` - Broker disk usage exceeds 85% of capacity
- `kafka_broker_disk_usage_warning` - Broker disk usage exceeds 70% of capacity
- `kafka_log_cleaner_backlog_high` - Log cleaner is not keeping pace with write rate
- `kafka_broker_offline_partitions` - Broker has gone offline likely due to disk exhaustion

## Diagnosis Steps

1. **Identify the affected broker** - Review the Kafka broker disk dashboard in Grafana to see disk usage per broker node; identify which brokers are at or near capacity.
2. **Check topic retention settings** - Run `kafka-topics.sh --bootstrap-server [broker] --describe --topic [topic]` for high-traffic topics to review `retention.bytes` and `retention.ms` settings; topics with very long retention are a common cause.
3. **Identify the largest topics** - Use `kafka-log-dirs.sh` to list log directory sizes by topic; identify which topics are consuming the most disk space on the affected broker.
4. **Check log cleaner status** - Review broker logs for log cleaner activity; if the cleaner is falling behind due to a high write rate, disk accumulates faster than it is cleaned.
5. **Check for consumer lag driving retention** - If consumers are severely lagged, Kafka retains messages longer than the time-based retention to allow consumers to catch up, inflating disk usage.

## Remediation Steps

1. **If consumer lag is causing retention to hold data longer than expected**: Address the consumer lag first (see RUNBOOK-036); once consumers catch up, Kafka can clean old log segments.
2. **If a topic has excessive retention configured**: Reduce `retention.bytes` or `retention.ms` for the offending topic — `kafka-configs.sh --alter --entity-type topics --entity-name [topic] --add-config retention.ms=[value]`.
3. **If disk is critically full (>90%)**: Immediately reduce retention on the largest topics to trigger log segment deletion and free space.
4. **If a broker has gone offline**: Restore disk space first, then restart the broker; do not restart without clearing space as it will immediately go offline again.
5. **If disk volumes need to be expanded**: Request an EBS volume expansion from the infrastructure team; Kafka does not require downtime for disk expansion on most configurations.
6. **If multiple brokers are affected**: Escalate immediately — this is a cluster-wide issue requiring coordinated remediation.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer identifies affected broker(s) and checks topic retention |
| 10 min | Post status in #kafka-incidents |
| 20 min | If broker disk is >90%: page Data Platform lead immediately |
| 30 min | If broker is offline: escalate to Engineering Manager and infrastructure team |

## Dashboards

- [Kafka Broker Disk Usage](https://grafana.example.com/d/kafka-disk) - Disk utilization per broker node
- [Kafka Topic Log Sizes](https://grafana.example.com/d/kafka-log-sizes) - Log directory size per topic
- [Kafka Consumer Lag](https://grafana.example.com/d/kafka-consumer-lag) - Lag by consumer group (affects retention)
- [Kafka Log Cleaner Activity](https://grafana.example.com/d/kafka-log-cleaner) - Cleaner throughput and backlog
