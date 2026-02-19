---
id: SYSTEM-038
type: system
title: Distributed Tracing Platform
status: approved
owner: Monitoring Engineering
owner_team: Monitoring Engineering
runtime: Kubernetes / Go 1.22 / ClickHouse / Kafka
created: '2024-02-11T01:49:37.427Z'
updated: '2025-05-30T06:50:41.177Z'
tags:
  - system
  - monitoring-stack
summary: Distributed Tracing Platform
sla: 99.99% monthly uptime
repos:
  - https://git.example.com/acme/distributed-tracing-platform
dependencies:
  - Metrics Collection Service
  - Alert Management Service
runbooks:
  - RUNBOOK-056
  - RUNBOOK-078
example: true
---

## Overview

The Distributed Tracing Platform collects, stores, and visualizes distributed traces from all microservices using the OpenTelemetry protocol. It enables engineers to follow a request end-to-end across service boundaries, identify latency bottlenecks, and correlate errors with specific code paths.

The platform receives OTLP trace spans from all instrumented services via Kafka, processes and enriches them with service graph metadata, and stores them in ClickHouse for sub-second query at high data volumes. Retention is 14 days at full resolution, with a 90-day aggregated summary for SLO reporting.

## Architecture

- **Ingestion Layer**: OTLP gRPC and HTTP receivers publish spans to Kafka topics partitioned by `trace_id`. This decouples ingestion throughput from ClickHouse write latency.
- **Processing Layer**: Go consumers read from Kafka, assemble span trees, compute root span duration, and enrich spans with service graph topology. Emits exemplars to the Metrics Collection Service.
- **Storage Layer**: ClickHouse cluster (6 nodes) with a `traces` table using `trace_id` as the partition key and `timestamp` as the sort key. Enables O(1) lookups by trace ID and efficient time-range scans.
- **Query API**: REST and gRPC API supporting trace lookup by ID, service/operation search, and dependency graph queries. Used by Grafana Tempo datasource.

## Repositories

- [distributed-tracing-platform](https://git.example.com/acme/distributed-tracing-platform) - Application code, ClickHouse migrations, Kafka topic configs

## Runtime Environment

- **Platform**: Kubernetes, 3 availability zones
- **Language**: Go 1.22
- **Storage**: ClickHouse 23.x, 6-node cluster, replication factor 2
- **Message bus**: Kafka 3.x, 6 brokers, 30-day topic retention
- **Replicas**: 3 ingest pods, 3 processor pods, 2 query API pods

## Dependencies

- Metrics Collection Service - exemplar metric linkage for trace-to-metric correlation
- Alert Management Service - trace-based alert evaluation (error rate per service/operation)

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.99% monthly uptime |
| Trace ingestion lag | P99 < 5s from span receipt to queryable |
| Query latency | P95 < 1s for trace ID lookup |
| Retention | 14 days full resolution, 90 days aggregated |

## Runbooks

- [[RUNBOOK-056|Tracing Ingestion Backlog Runbook]]
- [[RUNBOOK-078|Prometheus Disk Full Recovery Runbook]]
