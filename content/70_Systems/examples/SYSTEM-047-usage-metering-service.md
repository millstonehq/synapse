---
id: SYSTEM-047
type: system
title: Usage Metering Service
status: approved
owner: Billing Engineering
owner_team: Billing Engineering
runtime: Kubernetes / .NET 8 / SQL Server 2022
created: '2024-12-07T14:08:21.117Z'
updated: '2026-11-07T21:46:57.478Z'
tags:
  - system
  - billing-engine
summary: Usage Metering Service
sla: 99.99% monthly uptime
repos:
  - https://git.example.com/acme/usage-metering-service
dependencies:
  - Billing Event Processor
  - Invoice Generation Service
runbooks:
  - RUNBOOK-069
  - RUNBOOK-066
example: true
---

## Overview

The Usage Metering Service is the authoritative source for raw and aggregated usage data within the Billing Engine. It ingests usage events from all product surfaces, aggregates them by customer and billing period, and exposes the results to downstream systems including the Invoice Generation Service and Subscription Management Service.

The service processes approximately 800,000 usage events per day, with end-of-month aggregation bursts reaching 5,000 events/second. Aggregated usage records are the primary input for invoice line-item generation and proration calculations.

## Architecture

- **Event Ingest API**: RESTful and gRPC endpoints for submitting usage events. Authenticated via service-to-service mTLS. Batching supported up to 500 events per request.
- **Aggregation Engine**: .NET 8 background service that applies windowed aggregations (hourly, daily, billing-period) using SQL Server 2022 streaming queries. Supports SUM, COUNT, MAX, and custom aggregation functions per metric type.
- **Storage Layer**: SQL Server 2022 stores raw events (30-day retention) and pre-computed aggregates (7-year retention). Partitioned by customer ID and billing period for query efficiency.
- **Query API**: Read-only REST endpoints for querying aggregated usage. Used by Invoice Generation and the Usage Dashboard product.
- **Event Publishing**: Publishes `usage.aggregated` events to the Billing Event Processor after each aggregation cycle.

## Repositories

- [usage-metering-service](https://git.example.com/acme/usage-metering-service) - Application code, migrations, Dockerfile

## Runtime Environment

- **Platform**: Kubernetes / .NET 8 / SQL Server 2022
- **Replicas**: 3 pods minimum (ingest), 2 pods (aggregation workers), autoscaling to 8 during month-end
- **Resources**: 1Gi memory request / 2Gi limit, 500m CPU request / 2 CPU limit per pod
- **Deployment**: Rolling via ArgoCD with health check gates
- **Configuration**: Environment variables via ConfigMaps, SQL Server credentials via Kubernetes Secrets with 90-day rotation

## Dependencies

- SQL Server 2022 Always On cluster (primary + 1 replica) - connection pool max 50 per pod
- Billing Event Processor - downstream consumer of `usage.aggregated` events
- Invoice Generation Service - queries aggregated usage for invoice line items

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.99% monthly uptime |
| Ingest latency | P95 < 500ms per batch |
| Aggregation lag | < 5 minutes behind real-time |
| Error rate | < 0.05% ingest failures |

## Runbooks

- [[RUNBOOK-069|Usage Metering High Ingest Error Rate]]
- [[RUNBOOK-066|Usage Metering Aggregation Lag]]
