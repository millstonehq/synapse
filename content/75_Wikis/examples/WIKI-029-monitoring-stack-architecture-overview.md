---
id: WIKI-029
type: wiki
title: Monitoring Stack - Architecture Overview
status: approved
owner: Monitoring Team
created: '2025-12-20T10:18:50.124Z'
updated: '2026-11-29T14:05:44.320Z'
tags:
  - wiki
  - monitoring-stack
summary: Monitoring Stack - Architecture Overview
source_repo: https://git.example.com/acme/monitoring-stack
commit_sha: 7eead4a1c7f94ecd6e585559b91f797329b99448
generated_at: '2026-10-12T22:38:13.727Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: gpt-4o
importance: medium
example: true
---

## Overview

The monitoring stack is a set of five integrated services that together provide metrics collection, log aggregation, distributed tracing, alert management, and external status communication for the entire platform. Each component has a distinct responsibility and communicates with others through well-defined APIs and message queues.

The design principle is defense-in-depth: if any single observability signal (metrics, logs, or traces) is unavailable, the others continue to function. The Alert Management Service and Status Page Service are intentionally isolated from the data plane components to remain operational during major incidents.

## Architecture

The stack is organized into three tiers:

- **Data Ingestion Tier**: Metrics Collection Service (Prometheus remote write + OTLP push), Log Aggregation Pipeline (Fluent Bit → pipeline), and Distributed Tracing Platform (OTLP via Kafka). All three accept data from instrumented services and store it in separate, purpose-optimized backends (ScyllaDB, SQL Server, ClickHouse).
- **Control Tier**: Alert Management Service consumes signal from the metrics and log layers to evaluate alert rules and route notifications. It is the single point of integration with PagerDuty and Slack.
- **Communication Tier**: Status Page Service consumes availability signals from the metrics layer and exposes them publicly. It is CDN-fronted and designed for independent availability.

## Key Components

- **Metrics Collection Service**: Rust-based ingestion and query service. Backs all Grafana dashboards. Stores 90 days of time-series data in ScyllaDB.
- **Log Aggregation Pipeline**: .NET 8 pipeline with SQL Server backend. Supports full-text log search and trace-ID cross-referencing.
- **Distributed Tracing Platform**: Go service using Kafka for decoupled ingestion and ClickHouse for high-volume span storage. 14-day full trace retention.
- **Alert Management Service**: Node.js routing engine backed by PostgreSQL. Manages deduplication, routing trees, maintenance windows, and notification delivery.
- **Status Page Service**: TypeScript/Next.js with Redis-cached status signals. CDN-backed static fallback for resilience.

## Configuration

Key operational configuration:

- All services deploy to the `monitoring` Kubernetes namespace
- Prometheus scrape configs and AlertManager routing rules are maintained in `https://git.example.com/acme/monitoring-stack`
- Grafana provisioning (dashboards, datasources) is automated via the provisioning pipeline
- Service-to-service authentication uses mTLS via the cluster service mesh

## Dependencies

| Component | Storage | Protocol |
|-----------|---------|----------|
| Metrics Collection | ScyllaDB + Redis | Prometheus remote write, OTLP |
| Log Aggregation | SQL Server | Fluent Bit HTTP |
| Distributed Tracing | ClickHouse + Kafka | OTLP gRPC |
| Alert Management | PostgreSQL | AlertManager webhook |
| Status Page | PostgreSQL + Redis | Internal REST API |
