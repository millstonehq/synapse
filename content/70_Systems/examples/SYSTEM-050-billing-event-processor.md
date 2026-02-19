---
id: SYSTEM-050
type: system
title: Billing Event Processor
status: approved
owner: Billing Engineering
owner_team: Billing Engineering
runtime: Kubernetes / Python 3.12 / PostgreSQL 16 / RabbitMQ 3.13
created: '2025-09-30T11:54:20.996Z'
updated: '2026-03-12T03:47:26.807Z'
tags:
  - system
  - billing-engine
summary: Billing Event Processor
sla: 99.99% monthly uptime
repos:
  - https://git.example.com/acme/billing-event-processor
dependencies:
  - Usage Metering Service
  - Subscription Management Service
runbooks:
  - RUNBOOK-068
  - RUNBOOK-064
example: true
---

## Overview

The Billing Event Processor is the central event routing and orchestration service in the Billing Engine. It consumes billing-domain events from RabbitMQ (usage aggregated, subscription renewed, payment received, refund issued) and dispatches them to the appropriate downstream handlers — triggering invoice generation, tax recalculation, ledger entries, and notifications as needed.

The service processes approximately 200,000 billing events per day and serves as the integration backbone between the Usage Metering Service, Subscription Management Service, and downstream financial systems. It is designed for at-least-once delivery with idempotency enforcement at the handler level.

## Architecture

- **Event Consumer**: Python 3.12 consumers subscribed to RabbitMQ 3.13 exchange. Separate consumer pools per event type with configurable prefetch and concurrency.
- **Routing Engine**: Dispatch table maps event types to handler chains. Handlers are composable; a single event can trigger multiple downstream actions in sequence.
- **Idempotency Store**: PostgreSQL 16 table stores processed event IDs (event_id + handler_id) for deduplication. TTL of 30 days.
- **Dead Letter Queue**: Events that fail after 3 retries are published to a DLQ exchange for manual review and reprocessing.
- **Audit Trail**: All event processing outcomes (success, failure, skipped) are persisted for compliance and debugging.

## Repositories

- [billing-event-processor](https://git.example.com/acme/billing-event-processor) - Application code, consumer definitions, Dockerfile

## Runtime Environment

- **Platform**: Kubernetes / Python 3.12 / PostgreSQL 16 / RabbitMQ 3.13
- **Replicas**: 4 pods minimum per consumer group, autoscaling to 12 based on queue depth
- **Resources**: 512Mi memory request / 1Gi limit, 250m CPU request / 1 CPU limit per pod
- **Deployment**: Rolling via ArgoCD
- **Configuration**: RabbitMQ credentials via Kubernetes Secrets with 90-day rotation

## Dependencies

- RabbitMQ 3.13 cluster - event bus, 3-node highly available setup
- PostgreSQL 16 cluster - idempotency store and audit trail
- Usage Metering Service - upstream producer of `usage.aggregated` events
- Subscription Management Service - upstream producer of `subscription.state_changed` events

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.99% monthly uptime |
| Event processing latency | P95 < 10 seconds end-to-end |
| DLQ rate | < 0.1% of events |
| Duplicate processing rate | < 0.01% (idempotency enforcement) |

## Runbooks

- [[RUNBOOK-068|Billing Event Processor Dead Letter Queue Spike]]
- [[RUNBOOK-064|Billing Event Processor Consumer Group Lag]]
