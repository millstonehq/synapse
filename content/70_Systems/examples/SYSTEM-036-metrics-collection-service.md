---
id: SYSTEM-036
type: system
title: Metrics Collection Service
status: deprecated
owner: Monitoring Engineering
owner_team: Monitoring Engineering
runtime: Kubernetes / Rust 1.75 / ScyllaDB / Redis 7
created: '2024-06-17T06:34:50.731Z'
updated: '2026-11-17T06:59:37.109Z'
tags:
  - system
  - monitoring-stack
summary: Metrics Collection Service
sla: 99.95% monthly uptime
repos:
  - https://git.example.com/acme/metrics-collection-service
dependencies:
  - Distributed Tracing Platform
  - Log Aggregation Pipeline
runbooks:
  - RUNBOOK-056
  - RUNBOOK-051
example: true
---

## Overview

The Metrics Collection Service is the central ingestion and storage layer for time-series metrics across the monitoring platform. It receives metrics from all instrumented services via Prometheus scrape endpoints and OpenTelemetry push receivers, normalizes them into a consistent schema, and writes them to ScyllaDB for long-term retention.

The service handles approximately 2 million metric samples per second at peak and supports multi-tenant metric namespacing to isolate teams. It integrates with the Distributed Tracing Platform for exemplar correlation and with the Log Aggregation Pipeline for log-metric cross-referencing.

## Architecture

The service is built on a pipeline architecture:

- **Ingestion Layer**: Exposes Prometheus remote write endpoint and OTLP gRPC receiver. Validates metric schemas and applies tenant routing rules. Rate-limited per tenant at 100k samples/sec.
- **Processing Layer**: Normalizes labels, applies relabeling rules, computes derivative metrics (rate, increase), and enforces cardinality limits (max 10k label combinations per metric name).
- **Storage Layer**: Writes to ScyllaDB using a time-bucketed partition key scheme. Redis 7 acts as a write-through cache for the last 2 hours of data to accelerate recent-range queries.
- **Query Layer**: Exposes PromQL-compatible HTTP API for dashboards and alerting rules. Supports federated queries across multiple storage shards.

## Repositories

- [metrics-collection-service](https://git.example.com/acme/metrics-collection-service) - Application code, schema migrations, Dockerfile

## Runtime Environment

- **Platform**: Kubernetes cluster, 3 availability zones
- **Language**: Rust 1.75 with Tokio async runtime
- **Replicas**: 6 pods minimum, autoscaling to 20 based on ingestion rate
- **Resources**: 2Gi memory request / 4Gi limit, 1 CPU request / 4 CPU limit per pod
- **Deployment**: Rolling update via ArgoCD with pre-deploy health gate
- **Storage**: ScyllaDB 5.x cluster (6 nodes), replication factor 3
- **Cache**: Redis 7 cluster, 3 nodes, 16GB per node

## Dependencies

- ScyllaDB cluster - primary long-term metric storage, 90-day retention
- Redis 7 cluster - short-term cache, 2-hour hot window
- Distributed Tracing Platform - exemplar trace ID linking
- Log Aggregation Pipeline - metric-to-log correlation index

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.95% monthly uptime |
| Ingestion latency | P99 < 500ms from receipt to queryable |
| Query latency | P95 < 2s for 24h range queries |
| Data loss | Zero samples lost in normal operation |

## Runbooks

- [[RUNBOOK-056|Metrics Ingestion Backlog Runbook]]
- [[RUNBOOK-051|ScyllaDB Cluster Recovery Runbook]]
