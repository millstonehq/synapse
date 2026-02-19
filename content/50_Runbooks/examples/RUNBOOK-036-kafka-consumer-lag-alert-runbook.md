---
id: RUNBOOK-036
type: runbook
title: Kafka Consumer Lag Alert Runbook
status: proposed
owner: On-Call Engineer
created: '2024-09-12T16:24:31.286Z'
updated: '2025-12-30T03:43:21.394Z'
tags:
  - runbook
  - data-pipeline
summary: Kafka Consumer Lag Alert Runbook
example: true
---

## Service

- **System**: [[SYSTEM-026|Kafka Cluster]]
- **Owner team**: Data Platform Engineering
- **On-call rotation**: PagerDuty schedule "data-platform-oncall"
- **Slack channel**: #kafka-incidents
- **Runtime**: Kafka 3.5 / Kubernetes / Confluent Schema Registry

## Alerts

- `kafka_consumer_lag_high` - Consumer group lag exceeds 10,000 messages for 5 minutes
- `kafka_consumer_lag_growing` - Consumer lag increasing at >1,000 messages/minute for 10 minutes
- `kafka_consumer_group_stalled` - Consumer group offset has not advanced in 15 minutes
- `kafka_consumer_deserialization_errors` - Deserialization error rate exceeds 1% for 3 minutes

## Diagnosis Steps

1. **Identify the affected consumer group** - Run `kafka-consumer-groups.sh --bootstrap-server [broker] --describe --group [group_id]` to see current lag per partition and which consumers are assigned.
2. **Check consumer pod health** - Run `kubectl get pods -n data-pipelines -l app=[consumer_name]` to confirm pods are running. Look for crashlooping pods or recent restarts that may have triggered a rebalance.
3. **Review consumer application logs** - Inspect recent logs for the consumer pods using `kubectl logs [pod_name] -n data-pipelines --since=30m`. Look for processing errors, long GC pauses, or blocked I/O that may slow throughput.
4. **Check producer throughput** - Confirm whether lag is growing because the producer rate has spiked. Review the Kafka broker metrics in Grafana for the affected topic's message rate trend.
5. **Check for rebalance events** - Look for recent rebalance events in the consumer logs; a prolonged rebalance can cause lag to accumulate.
6. **Assess partition imbalance** - Verify partition assignments are evenly distributed; an uneven distribution may cause one consumer to process a disproportionate volume.

## Remediation Steps

1. **If consumer pods are crashlooping**: Describe the pod for exit reason, fix the underlying error, and redeploy. Monitor that lag begins decreasing after pod stabilization.
2. **If processing throughput is too slow**: Scale up the consumer deployment — `kubectl scale deployment/[consumer] -n data-pipelines --replicas=[N]` — ensuring replicas do not exceed partition count.
3. **If a rebalance is stuck**: Restart the consumer deployment to force a fresh group join: `kubectl rollout restart deployment/[consumer] -n data-pipelines`.
4. **If deserialization errors are causing lag**: Pause the consumer, investigate the schema version mismatch, and apply the schema compatibility fix before resuming.
5. **If a traffic spike has overwhelmed throughput**: Temporarily increase consumer thread count via configuration and monitor lag trend.
6. **If lag does not decrease within 20 minutes of remediation**: Escalate to the Data Platform lead.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 10 min | Post initial assessment in #kafka-incidents |
| 20 min | If lag still growing: page Data Platform tech lead via PagerDuty |
| 40 min | If not resolved: notify downstream consumer teams of delay |
| 60 min | If not resolved: escalate to Engineering Manager and assess SLA breach |

## Dashboards

- [Kafka Consumer Lag Overview](https://grafana.example.com/d/kafka-consumer-lag) - Lag by consumer group and topic
- [Kafka Broker Throughput](https://grafana.example.com/d/kafka-brokers) - Producer and consumer message rates
- [Data Pipeline Pod Health](https://grafana.example.com/d/data-pipeline-pods) - Consumer pod restarts and resource usage
- [Schema Registry Errors](https://grafana.example.com/d/schema-registry) - Deserialization error rates
