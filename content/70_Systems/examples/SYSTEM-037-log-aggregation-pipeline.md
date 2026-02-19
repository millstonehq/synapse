---
id: SYSTEM-037
type: system
title: Log Aggregation Pipeline
status: approved
owner: Monitoring Engineering
owner_team: Monitoring Engineering
runtime: Kubernetes / .NET 8 / SQL Server 2022
created: '2025-06-11T22:52:58.196Z'
updated: '2026-12-07T00:10:59.207Z'
tags:
  - system
  - monitoring-stack
summary: Log Aggregation Pipeline
sla: 99.95% monthly uptime
repos:
  - https://git.example.com/acme/log-aggregation-pipeline
dependencies:
  - Distributed Tracing Platform
  - Alert Management Service
runbooks:
  - RUNBOOK-051
  - RUNBOOK-053
example: true
---

## Overview

The Log Aggregation Pipeline collects, parses, indexes, and stores structured log data from all services in the platform. It acts as the central log storage layer, enabling full-text search, structured field filtering, and log-to-trace correlation across all environments.

The pipeline ingests logs via Fluent Bit agents deployed as DaemonSets on every Kubernetes node, enriches them with Kubernetes metadata (namespace, pod, container, node), and indexes them in SQL Server for query. Log retention is tiered: 30 days hot storage (fully indexed), 90 days warm (compressed), and 1 year cold (archived to object storage).

## Architecture

- **Collection Layer**: Fluent Bit DaemonSet on each node tails container log files, parses JSON structured logs, and forwards to the pipeline ingestion endpoint.
- **Enrichment Layer**: Attaches Kubernetes metadata, service name from pod labels, and links trace IDs to spans in the Distributed Tracing Platform.
- **Indexing Layer**: SQL Server 2022 with full-text indexing on the `message` field and columnar indexes on `service`, `level`, `timestamp`, and `trace_id`.
- **Query Layer**: REST API for log search supporting full-text queries, field filters, time ranges, and log streaming (Server-Sent Events).
- **Alerting Integration**: Forwards error-level and above logs to the Alert Management Service for log-based alerting rules.

## Repositories

- [log-aggregation-pipeline](https://git.example.com/acme/log-aggregation-pipeline) - Application code, DB migrations, Helm chart

## Runtime Environment

- **Platform**: Kubernetes, multi-zone
- **Language**: .NET 8, ASP.NET Core
- **Replicas**: 4 ingestion pods, 2 query pods; autoscaling enabled
- **Database**: SQL Server 2022, primary + 1 read replica
- **Deployment**: Blue-green via ArgoCD

## Dependencies

- Distributed Tracing Platform - trace ID cross-referencing for log correlation
- Alert Management Service - forwarding error logs for alert rule evaluation

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.95% monthly uptime |
| Ingestion lag | P99 < 10s from log emission to indexed |
| Query latency | P95 < 3s for 1-hour searches |
| Retention | 30 days fully searchable, 1 year archived |

## Runbooks

- [[RUNBOOK-051|Log Pipeline Disk Recovery Runbook]]
- [[RUNBOOK-053|Log Ingestion Backlog Runbook]]
