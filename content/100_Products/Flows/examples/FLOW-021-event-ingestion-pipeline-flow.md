---
id: FLOW-021
type: flow
title: Event Ingestion Pipeline Flow
status: draft
owner: QA Engineer
created: '2025-04-16T10:08:51.995Z'
updated: '2026-03-13T23:22:44.054Z'
tags:
  - flow
  - data-pipeline
summary: Event Ingestion Pipeline Flow
feature_area: Data Pipeline
related_prds:
  - PRD-028
example: true
---

## Steps

### Step 1: Producer Publishes Event to Kafka

An upstream service (e.g., order service, inventory service) publishes an Avro-encoded event to the designated Kafka topic. The message header contains a 5-byte magic byte + schema ID prefix per the Confluent wire format. The Kafka broker assigns a partition and offset to the message and acknowledges to the producer.

### Step 2: ECS Ingestion Consumer Polls Kafka

The Data Lake Ingestion Service ECS task polls the Kafka topic in batches of up to 500 records per poll cycle. The consumer deserializes each record using the Schema Registry client, which resolves the schema ID from the message header and fetches the Avro schema (from cache or DynamoDB if cache miss). Successfully deserialized records are passed to the enrichment pipeline; records that fail deserialization are routed to the dead-letter Kafka topic.

### Step 3: Enrichment Pipeline Processes Records

Each deserialized record passes through the enrichment pipeline stages in order: timestamp normalization (converts epoch milliseconds to UTC ISO-8601), customer ID resolution (enriches with customer tier from cache), and null field filtering (drops records with required fields null). Records rejected by any stage are routed to the dead-letter topic with the rejection reason. Records passing all stages are buffered in the Iceberg writer.

### Step 4: Iceberg Writer Flushes Buffer

When the buffer reaches 50,000 records or 60 seconds have elapsed (whichever occurs first), the Iceberg writer commits the buffered records to the target Iceberg table. The write creates a new Iceberg snapshot containing the new data files. On commit success, the Iceberg snapshot ID is written to the Aurora checkpoint table along with the committed Kafka offsets. The Kafka consumer then commits the offsets to the Kafka broker.

### Step 5: dbt Transformation Picks Up New Data

On the Airflow-scheduled dbt run (hourly for standard topics, every 15 minutes for Tier-1 topics), the dbt incremental models detect new Iceberg snapshots via watermark comparison. dbt executes the incremental SQL against the Trino cluster, reading only the new partitions. Transformed records are written to the staging and mart layer Iceberg tables.

### Step 6: Data Quality Check Validates New Data

Post-dbt, the Airflow quality check DAG triggers the Data Quality Validation Framework Lambda. The Lambda evaluates completeness, uniqueness, and freshness rules against the updated mart tables. Rule results are written to DynamoDB and CloudWatch. If any P1 rules fail, an SNS alert is published to the on-call PagerDuty topic.

## Expected Results

- Events published to Kafka are ingested into the raw Iceberg table within 5 minutes (standard topics) or 5 minutes (Tier-1 micro-batch topics) of publication
- All records pass enrichment or are routed to the dead-letter topic with a logged rejection reason; no records are silently dropped
- Transformed mart tables reflect the new ingested data within 15 minutes (Tier-1) or 65 minutes (standard) of Kafka publication
- Quality rules pass for the updated data; P1 failures generate PagerDuty pages within 5 minutes of detection
- On ECS task crash and restart, no records are skipped or duplicated (checkpoint guarantee)

## User Info

| Field | Value |
|-------|-------|
| Role | Data pipeline operator / on-call engineer |
| Permissions | Read access to Kafka consumer group metrics, Iceberg table metadata, CloudWatch metrics, Aurora checkpoint table |
| Test topic | `orders-events-test-v2` (staging environment) |
| Test Iceberg table | `data-lake-staging.raw.orders_events` |
| Environment | Staging |
