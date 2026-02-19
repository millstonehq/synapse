---
id: TDD-026
type: tdd
title: Real-Time Event Processing Engine TDD
status: review
owner: Tech Lead
created: '2025-09-16T22:48:36.400Z'
updated: '2026-07-14T02:49:04.375Z'
tags:
  - tdd
  - data-pipeline
summary: Real-Time Event Processing Engine TDD
related_adrs:
  - ADR-0024
  - ADR-0023
example: true
---

## Summary

Design the Real-Time Event Processing Engine — an ECS Fargate-based Kafka consumer service that ingests raw event streams from all upstream producers, applies Avro deserialization, performs lightweight filtering and enrichment, and writes records to Apache Iceberg tables in the data lake at low latency. This service bridges the Event Streaming Platform and the Data Lake Ingestion tier.

This TDD follows the dbt-based transformation approach from [[ADR-0024|ADR-0024: Adopt dbt for Data Transformations]] and the Iceberg table format decided in [[ADR-0023|ADR-0023: Use Apache Iceberg for Data Lake Format]].

## Overview

The Real-Time Event Processing Engine is a Java 21 application deployed as an ECS Fargate task. It uses the Confluent Kafka client with Avro deserialization, processes events via a pluggable enrichment pipeline, and writes to Iceberg tables using the Iceberg Java SDK. Per-topic consumer groups are independently scalable. Each task instance manages a single consumer group assignment to simplify offset tracking.

Key design principles:
- **At-least-once delivery**: Offsets committed only after successful Iceberg write confirmation
- **Pluggable enrichment**: Per-topic enrichment stages implemented as a chain-of-responsibility pipeline
- **Checkpoint durability**: Aurora PostgreSQL stores consumer offsets independently of Kafka for crash recovery
- **Backpressure handling**: Consumer poll loops apply backpressure by blocking on the Iceberg writer's internal buffer

## Architecture

### Component Diagram

The engine has three layers:

- **Consumer Layer**: Kafka consumer poll loop, Avro deserialization via Schema Registry client, offset management
- **Processing Layer**: Enrichment pipeline stages (timestamp normalization, customer ID resolution, null field filtering)
- **Writer Layer**: Iceberg table writer using HadoopCatalog with S3FileIO; buffers records for batch commits to minimize small file creation

### Data Flow

1. Kafka consumer polls batch of up to 500 records per poll cycle
2. Each record is deserialized from Avro using the schema ID embedded in the message header
3. Enrichment pipeline processes each record; records failing enrichment are routed to the dead-letter topic
4. Enriched records are buffered in the Iceberg writer; buffer flushes every 60 seconds or at 50,000 records
5. On flush: Iceberg write commit executes; on commit success, Kafka offsets are committed to Aurora and Kafka broker

## Information Model

### Core Entities

- **EventRecord**: Internal representation of a deserialized Kafka message. Fields: `topic`, `partition`, `offset`, `event_time`, `schema_id`, `payload` (Avro GenericRecord), `enrichment_metadata`
- **ConsumerCheckpoint**: Aurora-persisted offset record. Fields: `consumer_group`, `topic`, `partition`, `committed_offset`, `iceberg_snapshot_id`, `committed_at`
- **DeadLetterRecord**: Records that fail deserialization or enrichment. Fields: `topic`, `partition`, `offset`, `raw_bytes`, `error_type`, `error_message`, `failed_at`

### Aurora Schema

- `consumer_checkpoints` table: primary key `(consumer_group, topic, partition)`, index on `committed_at`
- `dead_letter_records` table: index on `(topic, failed_at)` for DLQ monitoring queries

## Interfaces

### Internal Enrichment Pipeline Interface

```java
public interface EnrichmentStage {
    EnrichmentResult process(EventRecord record);
}

public enum EnrichmentResult {
    PASS,       // Record passes; continue pipeline
    MODIFIED,   // Record was enriched; continue pipeline
    REJECT      // Route to dead-letter topic; stop pipeline
}
```

### Iceberg Writer Interface

```java
public interface IcebergTableWriter {
    void buffer(EventRecord record);
    SnapshotCommit flush() throws IcebergWriteException;
    void close();
}
```

## Files and Layout

```
src/main/java/com/example/pipeline/
  consumer/
    KafkaConsumerLoop.java          - Poll loop, offset management
    AvroDeserializer.java           - Schema Registry client, deserialization
    CheckpointStore.java            - Aurora checkpoint read/write
  enrichment/
    EnrichmentPipeline.java         - Chain-of-responsibility orchestrator
    stages/
      TimestampNormalizationStage.java
      CustomerIdResolutionStage.java
      NullFieldFilterStage.java
  writer/
    IcebergTableWriter.java         - Buffered Iceberg writer
    S3FileIOFactory.java            - S3FileIO configuration
  model/
    EventRecord.java
    ConsumerCheckpoint.java
    DeadLetterRecord.java
  config/
    ConsumerConfig.java             - Kafka + Schema Registry config from env
    IcebergConfig.java              - Catalog and table config
```

## Work Plan

1. **Phase 1 — Consumer Foundation (Week 1-2)**: Kafka consumer loop, Avro deserialization, Aurora checkpoint read/write
2. **Phase 2 — Iceberg Writer (Week 3-4)**: Buffered Iceberg writer with S3FileIO, flush-on-commit logic, checkpoint ordering guarantee
3. **Phase 3 — Enrichment Pipeline (Week 5)**: Chain-of-responsibility pipeline, timestamp normalization, dead-letter routing
4. **Phase 4 — Crash Recovery (Week 6)**: Crash-recovery integration tests, checkpoint gap detection, backfill tooling
5. **Phase 5 — Observability (Week 7)**: Consumer lag metrics, flush latency histograms, dead-letter rate alerts, Grafana dashboard

## Risks and Mitigations

- **Risk**: Checkpoint write before Iceberg commit causes data loss on crash. **Mitigation**: Checkpoint is written only after `SnapshotCommit` returns successfully; this is the primary correctness invariant enforced by integration tests.
- **Risk**: Buffer flush delay causes consumer lag accumulation. **Mitigation**: Flush is triggered by either 60-second interval or 50,000-record threshold; lag alert fires if either condition is not met within the expected window.
- **Risk**: Schema Registry unavailability blocks deserialization. **Mitigation**: Avro schema cache with 30-minute TTL; registry unavailability triggers DLQ routing after 3 retries.
- **Risk**: Iceberg small file accumulation degrades read performance. **Mitigation**: Daily compaction job runs against all active tables; file size target is 128 MB per data file.

## Operations

- **Deployment**: ECS Fargate rolling deployment; task count auto-scales 2–8 based on consumer lag metric.
- **Monitoring**: CloudWatch metrics for consumer lag per topic/partition, Iceberg flush latency, dead-letter record rate, checkpoint commit latency.
- **Alerting**: Page on consumer lag > 100,000 records (5-minute sustained), dead-letter rate > 1% of messages, Iceberg flush failure.
- **Rollback**: Previous task definition revision deployed via ECS service update; checkpoint state in Aurora is preserved across rollbacks.
