---
id: WIKI-022
type: wiki
title: Kafka Cluster - Configuration and Tuning
status: accepted
owner: Data Team
created: '2025-02-18T18:56:16.994Z'
updated: '2026-03-29T22:53:03.225Z'
tags:
  - wiki
  - data-pipeline
summary: Kafka Cluster - Configuration and Tuning
source_repo: https://git.example.com/acme/kafka-cluster
commit_sha: 9f7cb6c827ce30edf6d4b7b617a84fa8e170ef79
generated_at: '2026-11-28T19:27:11.686Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: claude-3-sonnet
importance: low
example: true
---

## Overview

This page documents the configuration and tuning parameters applied to the data pipeline's Kafka cluster. The cluster runs 6 brokers across 3 availability zones and handles all event traffic for the data pipeline domain. Key tuning goals are: durability (no data loss on broker failure), low tail latency (P99 < 500ms end-to-end), and efficient disk utilization.

This document covers broker-level config, topic-level config, producer and consumer tuning, and JVM settings. Changes to any of these parameters should go through the change management process given the production risk.

## Broker Configuration

Key broker settings applied in `server.properties`:

- `num.network.threads=8` — matched to vCPU count; handles socket accept and response threads
- `num.io.threads=16` — disk I/O threads; tuned for gp3 EBS throughput at 500 MiB/s
- `log.retention.hours=168` — 7-day retention for all topics unless overridden at topic level
- `log.segment.bytes=536870912` — 512 MB segments; balances compaction frequency and seek overhead
- `min.insync.replicas=2` — brokers require acknowledgment from 2 replicas before confirming write
- `auto.create.topics.enable=false` — all topics must be explicitly provisioned; prevents schema registry topic sprawl
- `unclean.leader.election.enable=false` — disallows out-of-sync replicas from becoming leader to prevent data loss

## Topic Configuration

Standard topic template used for pipeline event topics:

- `replication.factor=3`
- `min.insync.replicas=2`
- `retention.ms=604800000` (7 days)
- `compression.type=lz4` — LZ4 chosen for balance of CPU cost and compression ratio on Avro payloads
- `message.timestamp.type=LogAppendTime` — broker timestamp used for ordering; prevents clock skew issues from producers

High-throughput topics (>100K events/day) use additional settings:
- `segment.ms=3600000` — 1-hour rolling segments to enable faster compaction
- `delete.retention.ms=86400000` — 1-day tombstone retention for compacted topics

## Producer and Consumer Tuning

**Producer settings** (applied in the Data Lake Ingestion Service):
- `acks=all` — wait for all in-sync replicas to acknowledge
- `enable.idempotence=true` — exactly-once produce semantics within a session
- `compression.type=lz4`
- `batch.size=131072` (128 KB) — larger batches reduce broker round-trips at high throughput
- `linger.ms=5` — 5ms batching window to fill batches before send

**Consumer settings** (applied across all pipeline consumers):
- `fetch.min.bytes=65536` (64 KB) — reduces fetch RPCs during low-traffic periods
- `max.poll.records=500` — limits records per poll to bound per-batch processing time
- `isolation.level=read_committed` — ensures consumers only see fully committed transactions

## Key Components

- Cluster topology: 6 brokers, 3 AZs (us-east-1a, 1b, 1c), rack-aware replica assignment
- JVM heap: `-Xmx6g -Xms6g` per broker with G1GC; page cache is the primary performance lever
- Monitoring: JMX exported via Prometheus JMX exporter; key metrics: `UnderReplicatedPartitions`, `RequestHandlerAvgIdlePercent`, `BytesInPerSec`, consumer group lag via Burrow

## Configuration

Reference the cluster configuration repo at `https://git.example.com/acme/kafka-cluster` for the full `server.properties` templates and Ansible playbooks used to apply changes across the cluster without downtime.

