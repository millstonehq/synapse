---
id: WIKI-046
type: wiki
title: Kafka Topics - Partitioning Strategy
status: approved
owner: Data Team
created: '2025-06-05T13:13:04.391Z'
updated: '2026-08-31T10:25:42.576Z'
tags:
  - wiki
  - data-pipeline
summary: Kafka Topics - Partitioning Strategy
source_repo: https://git.example.com/acme/kafka-topics
commit_sha: b623a504d771215c1adcf555069d5242b1a18f67
generated_at: '2025-11-05T14:24:48.017Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: gpt-4
importance: high
example: true
---

## Overview

This page documents the Kafka topic partitioning strategy for the data pipeline's Event Streaming Platform. Correct partitioning is critical for achieving ordered delivery within a business entity, maximizing parallelism in the ingestion tier, and maintaining balanced broker load. This page covers the partitioning philosophy, per-topic configurations, partition key selection criteria, and the process for changing partition counts on existing topics.

## Partitioning Philosophy

The data pipeline uses two partitioning goals that are sometimes in tension:

1. **Ordering within an entity**: For topics where consumers need ordered processing (e.g., CDC streams where a DELETE must be processed after an INSERT for the same row), messages for the same entity must land on the same partition. This is achieved by choosing an entity-scoped partition key.

2. **Throughput parallelism**: For topics where ordering is not required (e.g., independent event streams), maximize partition count to allow more concurrent ECS consumer task instances. Each partition is consumed by exactly one consumer task at a time; more partitions = more possible parallelism.

The platform standard is 8 partitions for standard topics and 24 partitions for Tier-1 high-volume topics. Partition count is set at topic creation and cannot be reduced; increasing partition count breaks ordering guarantees if a hash-based partition key is used.

## Topic Inventory and Partition Configuration

| Topic | Partitions | Partition Key | Ordering Required | Notes |
|-------|-----------|---------------|-------------------|-------|
| `orders-events-v2` | 24 | `order_id` | Yes — status transitions | Tier-1, high volume |
| `inventory-updates-v2` | 24 | `product_id` | Yes — stock level updates | Tier-1, high volume |
| `session-events-v2` | 24 | `session_id` | Yes — session lifecycle | Tier-1, high volume |
| `pricing-updates-v3` | 24 | `sku_id` | Yes — price history | Tier-1, high volume |
| `user-profile-changes-v2` | 24 | `user_id` | Yes — profile state | Tier-1, high volume |
| `audit-log-events-v1` | 8 | null (round-robin) | No | Standard; no entity ordering |
| `notification-requests-v1` | 8 | `user_id` | No | Standard; key for dedup only |
| `payment-webhook-events-v1` | 8 | `payment_id` | Yes — webhook replay order | Standard |
| `data-quality-alerts-v1` | 4 | null (round-robin) | No | Low volume; 4 partitions sufficient |

## Partition Key Selection Rules

Follow this decision tree when selecting a partition key for a new topic:

1. **Does message ordering matter within a business entity?** — If yes, the partition key must be the entity's primary identifier (e.g., `order_id`, `user_id`, `product_id`).

2. **Is the primary identifier high-cardinality (> 10,000 unique values)?** — If yes, use the raw ID as the key; Kafka's default hash partitioning distributes well with high cardinality. If no, consider a secondary grouping (e.g., group by customer segment) or use round-robin.

3. **Are there hot partitions concerns?** — If a small number of entity IDs account for a disproportionate share of messages (e.g., a single high-volume seller account), use a compound key (e.g., `{entity_id}#{shard_number}`) to distribute load. Shard count is typically the partition count.

4. **Is this a CDC (Change Data Capture) stream?** — Always use the primary key of the source table as the partition key to guarantee row-level ordering.

## Changing Partition Counts

Increasing partition count on an existing topic **breaks hash-based ordering** for the transition period. Procedure:

1. Assess whether the topic requires ordered delivery. If yes, the consumer must handle a temporary re-ordering window or a new topic must be created with the new partition count (and the old topic drained).
2. Announce the change in #data-pipeline-incidents with 48 hours notice for Tier-1 topics; 24 hours for standard topics.
3. Coordinate with all consumer teams whose consumer groups will be affected by the rebalance.
4. Apply the partition change via the Kafka admin API during off-peak hours (Sunday 02:00–06:00 UTC preferred).
5. Monitor consumer group rebalance completion in Grafana; verify consumer lag returns to baseline within 30 minutes.

Partition count must not be increased without a corresponding ECS task count review — insufficient task instances will leave new partitions without a consumer.

## Replication and Retention

All topics use the following cluster-wide defaults unless explicitly overridden:

| Setting | Value | Rationale |
|---------|-------|-----------|
| Replication factor | 3 | Survives loss of 1 broker without data loss |
| min.insync.replicas | 2 | Producer acks require 2 in-sync replicas |
| Retention | 7 days | Covers Kafka-based replay recovery window (see checkpoint recovery runbook) |
| Max message size | 1 MB | Large messages indicate a schema design issue; they should be chunked |
| Compression | LZ4 | Good balance of CPU cost and compression ratio for Avro-encoded events |

Tier-1 topics that are subject to the Real-Time Analytics Pipeline SLA must not have their retention reduced below 7 days without a documented impact assessment confirming that the checkpoint recovery window is still satisfied.
