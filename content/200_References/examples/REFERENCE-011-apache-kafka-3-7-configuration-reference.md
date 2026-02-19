---
id: REFERENCE-011
type: reference
title: Apache Kafka 3.7 Configuration Reference
status: draft
owner: Platform Team
created: '2024-12-10T02:53:40.037Z'
updated: '2025-08-06T22:36:36.661Z'
tags:
  - reference
  - data-pipeline
summary: Apache Kafka 3.7 Configuration Reference
upstream_url: https://docs.example.com/apache-kafka-3-7-configuration-reference
last_synced: '2025-05-05T09:36:52.532Z'
attribution: NIST
license: CC BY-SA 4.0
category: api-reference
example: true
---

## Overview

Apache Kafka 3.7 is the latest stable release in the 3.x series and continues the transition away from Apache ZooKeeper toward the native KRaft consensus protocol. In KRaft mode, a quorum of broker nodes handles metadata management directly, eliminating the operational complexity of running a separate ZooKeeper ensemble. Kafka 3.7 also brings improvements to tiered storage, fetch protocol performance, and producer delivery semantics.

This reference covers the configuration properties most relevant to platform teams operating Kafka in production. Properties are drawn from the official Apache Kafka documentation and annotated with practical guidance for typical deployments.

## Broker Configuration

Broker properties are set in `server.properties` (legacy) or passed as JVM system properties in KRaft mode. The following properties have the most impact on cluster stability and throughput.

- `broker.id` — Unique integer identifier for each broker. In KRaft clusters this is replaced by `node.id`, which must be distinct across all controllers and brokers.
- `log.dirs` — Comma-separated list of directories where Kafka stores log segments. Spreading across multiple physical disks significantly improves sequential write throughput.
- `num.partitions` — Default partition count for auto-created topics. A value of 6–12 balances parallelism against metadata overhead for most workloads.
- `default.replication.factor` — Minimum recommended value is `3` for production; combined with `min.insync.replicas=2` this tolerates a single broker failure without data loss.
- `log.retention.hours` — How long Kafka retains messages before deletion. Set alongside `log.retention.bytes` to bound disk usage; whichever limit is reached first triggers cleanup.
- `auto.create.topics.enable` — Set to `false` in production to prevent clients from accidentally creating topics with default settings.

## Producer Settings

Producers are configured per client instance. The properties below govern durability, throughput, and ordering guarantees.

- `acks` — Controls durability. `acks=all` (or `acks=-1`) requires acknowledgment from all in-sync replicas before the write is confirmed; pair with `min.insync.replicas` on the broker.
- `enable.idempotence` — Set to `true` to enable exactly-once delivery at the producer level. This also forces `acks=all` and `max.in.flight.requests.per.connection=5`.
- `retries` — Number of retry attempts on transient failures. Defaults to `Integer.MAX_VALUE` when idempotence is enabled; do not lower this without understanding the ordering implications.
- `batch.size` and `linger.ms` — Tune together to control batching behavior. Larger batches improve throughput; a non-zero `linger.ms` allows time for records to accumulate before dispatch.
- `compression.type` — `lz4` and `zstd` offer the best compression-to-CPU tradeoff for most payloads. `snappy` is a reasonable default if CPU is constrained.

## Consumer Settings

Consumer configuration governs how consumer groups coordinate, commit offsets, and recover from lag.

- `group.id` — Identifies the consumer group. All instances sharing a `group.id` participate in the same partition assignment and offset tracking.
- `auto.offset.reset` — Determines behavior when no committed offset exists for a partition. Use `earliest` for event-sourcing workloads; `latest` for live-feed consumers that should skip historical data.
- `enable.auto.commit` — Set to `false` for exactly-once or at-least-once processing where the application controls when offsets are committed. Combine with manual `commitSync()` or `commitAsync()` calls after processing.
- `fetch.min.bytes` and `fetch.max.wait.ms` — Together these control the consumer's batching behavior on the broker side. Raising `fetch.min.bytes` reduces round trips at the cost of increased latency.
- `max.poll.records` — Caps the number of records returned per `poll()` call. Tune this alongside `max.poll.interval.ms` so processing a full batch never exceeds the session timeout.
- `isolation.level` — Set to `read_committed` when consuming from topics written by transactional producers to suppress uncommitted or aborted messages.

## Sync Notes

This reference summarizes configuration properties for Apache Kafka 3.7. For the full canonical property list, including all default values and valid ranges, refer to the upstream URL. Re-sync when upgrading to a new minor version, as property names and defaults occasionally change between releases.

Deprecated ZooKeeper-mode properties (`zookeeper.connect`, `zookeeper.session.timeout.ms`) are intentionally omitted; new deployments should use KRaft exclusively.
