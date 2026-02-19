---
id: GUIDE-066
type: guide
title: Building Dead Letter Queue Handlers Guide
status: deprecated
owner: Developer Experience
created: '2025-11-17T16:16:52.335Z'
updated: '2026-08-13T20:22:58.556Z'
tags:
  - guide
  - data-pipeline
summary: Building Dead Letter Queue Handlers Guide
audience: customer
related_systems:
  - SYSTEM-028
  - SYSTEM-030
related_sops:
  - SOP-059
  - SOP-055
example: true
---

## Why This Matters

In the data pipeline, not every event can be processed successfully on first attempt. Schema deserialization failures, malformed records, enrichment errors, and transient downstream failures all produce records that cannot complete the normal ingestion path. Without a dead letter queue (DLQ) handler, these records are silently dropped — you won't know until a data quality check fails hours later.

This guide explains how to build a robust DLQ handler for the [[SYSTEM-028|Schema Registry Service]] and [[SYSTEM-030|Data Lake Ingestion Service]]. It covers the DLQ pattern, how to consume dead-letter records from their respective Kafka topics, how to triage and replay records, and how to operate the handler in production. For the deployment procedure, see [[SOP-059|SOP-059]]; for the DLQ monitoring runbook procedure, see [[SOP-055|SOP-055]].

## The DLQ Pattern in Our Pipeline

When a record fails processing in the ingestion pipeline, it is routed to a dead-letter Kafka topic (e.g., `orders-events-v2.dlq`) with a structured metadata header:

```json
{
  "original_topic": "orders-events-v2",
  "original_partition": 3,
  "original_offset": 192847,
  "error_type": "SchemaDeserializationException",
  "error_message": "Schema ID 4821 not found in registry",
  "failed_at": "2025-09-15T14:22:33Z",
  "retry_count": 0
}
```

DLQ topics follow the naming convention `{source-topic}.dlq`. They use the same partition count as the source topic. Consumer group for DLQ handler: `{service-name}-dlq-handler`.

## Building a DLQ Handler

### Step 1: Choose the Appropriate Handler Strategy

Before writing code, determine the failure type and the appropriate remediation strategy:

| Error Type | Cause | Strategy |
|-----------|-------|----------|
| `SchemaDeserializationException` | Schema ID not in registry; producer deployed new schema before registering | Register the missing schema, then replay the record |
| `NullRequiredFieldException` | Producer sent a record missing a required field | Log the record; notify the producer team; do not replay (data is corrupt) |
| `EnrichmentTimeoutException` | Downstream enrichment service was temporarily unavailable | Replay after the enrichment service recovers; check `retry_count` to avoid infinite loops |
| `IcebergWriteException` | Iceberg table write failed (e.g., table locked during compaction) | Replay after the compaction window; delay replay by 10 minutes |

### Step 2: Implement the DLQ Consumer

A DLQ handler is a standard Kafka consumer pointed at the DLQ topic. Key implementation requirements:

- **Read raw bytes**: DLQ records may contain malformed Avro that cannot be deserialized normally. Use the raw bytes consumer (no deserializer) and read the DLQ metadata header separately from the record payload.
- **Idempotent replay**: Before replaying a record, check if it has already been replayed by querying the DLQ tracking table (DynamoDB) by `(original_topic, original_partition, original_offset)`. If a replay record exists, skip the duplicate.
- **Bounded retry**: Enforce a maximum retry count (default: 3). Records exceeding the max retry count are written to the permanent dead-letter store (S3 under `s3://data-pipeline-dlq-archive/`) and not replayed again.
- **Replay to the source topic**: Replay by producing the raw record payload back to the original source topic with the same key and schema ID. Do not modify the payload.

### Step 3: Implement the Replay Producer

```python
def replay_record(dlq_record: DLQRecord, kafka_producer: KafkaProducer):
    if dlq_record.retry_count >= MAX_RETRY_COUNT:
        archive_to_s3(dlq_record)
        return

    # Produce back to the original source topic
    kafka_producer.produce(
        topic=dlq_record.original_topic,
        key=dlq_record.record_key,
        value=dlq_record.raw_payload,  # unchanged raw bytes
        headers={"x-replay": "true", "x-retry-count": str(dlq_record.retry_count + 1)}
    )

    # Mark as replayed in DynamoDB
    mark_replayed(dlq_record)
```

### Step 4: Add Monitoring

DLQ handlers must emit the following CloudWatch metrics:
- `DLQRecordsConsumed` — records read from the DLQ topic
- `DLQRecordsReplayed` — records successfully replayed to source topic
- `DLQRecordsArchived` — records exceeding max retry count, archived to S3
- `DLQConsumerLag` — lag on the DLQ consumer group

Alert thresholds:
- `DLQConsumerLag > 1,000` for 10 minutes → data engineering on-call page
- `DLQRecordsArchived > 100` in 1 hour → P2 alert (indicates systematic producer issue)

## Common DLQ Scenarios

### Schema Registry Miss

The Schema Registry Service ([[SYSTEM-028|SYSTEM-028]]) is the most common source of DLQ records. When a producer deploys a new schema before registering it:

1. Records fail deserialization with `SchemaDeserializationException`
2. Records are routed to the DLQ topic
3. Register the missing schema via `POST /subjects/{subject}/versions`
4. Trigger the DLQ handler to replay the records

The DLQ handler can detect a registry miss by checking if the schema ID in the DLQ metadata is now resolvable. If so, automatic replay can proceed.

### Transient Iceberg Write Failures

During Iceberg table compaction, the ingestion service may encounter write conflicts:

1. Wait for the compaction job to complete (check CloudWatch for the compaction task completion metric)
2. Trigger manual replay via the DLQ handler CLI tool
3. Verify the replayed records appear in the Iceberg table

## Next Steps

- Read [[SOP-059|SOP-059]] for the DLQ handler deployment procedure
- Read [[SOP-055|SOP-055]] for the DLQ monitoring and triage runbook procedure
- Review the DLQ consumer lag dashboard before your first on-call rotation
