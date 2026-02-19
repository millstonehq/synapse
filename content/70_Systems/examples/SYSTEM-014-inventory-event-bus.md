---
id: SYSTEM-014
type: system
title: Inventory Event Bus
status: accepted
owner: Inventory Engineering
owner_team: Inventory Engineering
runtime: Kubernetes / Rust 1.75 / ScyllaDB / Redis 7
created: '2025-10-22T16:03:11.424Z'
updated: '2026-06-02T02:27:18.710Z'
tags:
  - system
  - inventory-management
summary: Inventory Event Bus
sla: 99.99% monthly uptime
repos:
  - https://git.example.com/acme/inventory-event-bus
dependencies:
  - Stock Level Calculator
  - Warehouse Sync Gateway
runbooks:
  - RUNBOOK-016
  - RUNBOOK-015
example: true
---

## Overview

The Inventory Event Bus is the central message broker for all stock movement and inventory state change events across the platform. It decouples event producers (Warehouse Sync Gateway, order management, returns processing) from consumers (Stock Level Calculator, analytics, notifications) via a topic-based pub/sub model.

Built in Rust for high throughput and low latency, the bus handles peaks of 5,000 events per second with end-to-end delivery guarantees. Events are durably persisted in ScyllaDB before acknowledgement, enabling replay for new consumer onboarding and audit purposes.

## Architecture

- **Publish API**: gRPC and HTTP/2 endpoints for producers to submit stock events. Validates event schema against the registered schema registry before acceptance.
- **Topic Router**: Routes events to subscriber queues based on event type and warehouse/SKU partition keys. Supports fan-out to multiple consumer groups.
- **Persistence Layer**: ScyllaDB stores the full event log partitioned by `(event_type, date)` with a configurable retention window (default 90 days).
- **Consumer Groups**: Named subscriber groups with independent offsets, enabling independent replay and catch-up without affecting other consumers.
- **Dead Letter Handling**: Events that fail consumer acknowledgement after 3 retries are moved to a per-consumer DLQ topic, with alerts firing when DLQ depth exceeds threshold.

## Repositories

- [inventory-event-bus](https://git.example.com/acme/inventory-event-bus) - Core broker, schema registry, consumer group management

## Runtime Environment

- **Platform**: Kubernetes / Rust 1.75 with ScyllaDB cluster (3 nodes) and Redis 7 for consumer offset tracking
- **Replicas**: 4 broker pods minimum, autoscaling to 16 based on inbound event rate
- **Deployment**: Blue-green via ArgoCD; zero consumer disruption during broker upgrades via graceful handoff

## Dependencies

- Stock Level Calculator - primary downstream consumer of stock movement events
- Warehouse Sync Gateway - primary upstream producer of warehouse stock events
- ScyllaDB - durable event log storage
- Redis 7 - consumer group offset management and DLQ depth counters

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.99% monthly uptime |
| End-to-end publish latency | P99 < 50ms |
| Consumer delivery lag | P95 < 500ms from publish to delivery |
| Durability | Zero event loss; all events persisted before ACK |

## Runbooks

- [[RUNBOOK-016|Inventory Event Bus Degradation Runbook]]
- [[RUNBOOK-015|Event Bus Consumer Lag Runbook]]
