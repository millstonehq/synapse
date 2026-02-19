---
id: SYSTEM-026
type: system
title: Event Streaming Platform
status: approved
owner: Data Engineering
owner_team: Data Engineering
runtime: Kubernetes / Go 1.22 / PostgreSQL 15 / Redis 7
created: '2024-04-18T06:22:36.239Z'
updated: '2026-08-15T05:14:03.698Z'
tags:
  - system
  - data-pipeline
summary: Event Streaming Platform
sla: 99.99% monthly uptime
repos:
  - https://git.example.com/acme/event-streaming-platform
dependencies:
  - Data Lake Ingestion Service
  - Data Quality Monitor
runbooks:
  - RUNBOOK-040
  - RUNBOOK-036
example: true
---

## Overview

The Event Streaming Platform is the central messaging backbone for all data pipeline operations. It handles high-throughput event ingestion, fan-out to multiple consumers, and durable log storage for replay and auditing. The platform is built on Apache Kafka and serves as the integration bus between upstream event producers and downstream processing systems.

The platform processes approximately 2 million events per day with a peak of 5,000 events per second during business hours. It provides at-least-once delivery guarantees with consumer group offset management, and integrates with the Data Lake Ingestion Service and Data Quality Monitor as primary downstream consumers.

## Architecture

- **Broker Layer**: 6-node Kafka cluster (3 AZs, replication factor 3) with topic-level retention policies. Internal topics use min.insync.replicas=2 for durability.
- **Schema Layer**: All events are serialized using Avro with schemas managed by the Schema Registry Service. Producers validate schemas before publish; consumers reject messages that fail deserialization.
- **Consumer Layer**: Consumer groups for each downstream system (ingestion, quality-monitor, analytics). Lag monitoring alerts when any consumer group exceeds 10,000 messages behind.
- **Dead Letter Layer**: Failed messages after 3 retry attempts are routed to per-topic DLQ topics. DLQ depth is monitored and alerted at depth > 500.
- **Operations Layer**: Kafka Connect cluster manages CDC connectors from upstream databases; Kafka Streams handles lightweight stateless enrichment.

## Repositories

- [event-streaming-platform](https://git.example.com/acme/event-streaming-platform) - Cluster configuration, topic definitions, connector configs

## Runtime Environment

- **Platform**: Kubernetes / Go 1.22 / PostgreSQL 15 / Redis 7
- **Brokers**: 6 pods minimum across 3 AZs, 32Gi memory each, 2TB EBS gp3 per broker
- **Deployment**: Rolling updates via ArgoCD with rack-aware partition reassignment pre-step
- **Configuration**: Broker configs via ConfigMaps; TLS keystores in Kubernetes Secrets with 90-day rotation
- **Monitoring**: JMX metrics exported to Prometheus; Grafana dashboards for lag, throughput, and under-replicated partitions

## Dependencies

- Data Lake Ingestion Service - primary downstream consumer for raw event topics
- Data Quality Monitor - subscribes to all pipeline topics for quality rule evaluation
- Schema Registry Service - validates Avro schemas at produce time (synchronous call)
- PostgreSQL 15 - Kafka Connect JDBC sink for relational projections

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.99% monthly uptime |
| End-to-end latency | P99 < 500ms from produce to consumer receipt |
| Throughput | Sustained 5,000 events/sec per partition |
| Recovery | MTTR < 15 minutes for single-broker failure |

## Runbooks

- [[RUNBOOK-040|Kafka Broker Recovery]]
- [[RUNBOOK-036|Consumer Lag Remediation]]
