---
id: SYSTEM-013
type: system
title: Stock Level Calculator
status: review
owner: Inventory Engineering
owner_team: Inventory Engineering
runtime: Kubernetes / Python 3.12 / PostgreSQL 16 / RabbitMQ 3.13
created: '2025-01-29T01:56:37.531Z'
updated: '2025-10-05T16:05:30.620Z'
tags:
  - system
  - inventory-management
summary: Stock Level Calculator
sla: 99.9% monthly uptime
repos:
  - https://git.example.com/acme/stock-level-calculator
dependencies:
  - Inventory Event Bus
  - Inventory Tracking Service
runbooks:
  - RUNBOOK-021
  - RUNBOOK-020
example: true
---

## Overview

The Stock Level Calculator is the authoritative computation engine for on-hand, reserved, available, and in-transit stock quantities across all SKUs and warehouse locations. It consumes stock movement events from the Inventory Event Bus and maintains a continuously updated projection of current stock state in PostgreSQL, with a read-optimized cache served via RabbitMQ-backed workers.

The service handles approximately 15,000 stock events per day and serves stock level queries to the order management, fulfillment, and merchant-facing systems. Correctness is prioritized over latency: the service uses event ordering guarantees and idempotency checks to ensure no movement is double-counted or missed.

## Architecture

- **Event Consumer**: RabbitMQ consumers subscribe to stock movement topics from the Inventory Event Bus. Events are processed in order per SKU/location partition to prevent out-of-order calculation errors.
- **Calculation Engine**: Python workers apply the stock movement delta to the current projection using a read-modify-write pattern with optimistic locking on the PostgreSQL stock_levels table.
- **Query API**: A RESTful HTTP API exposes current stock levels with filtering by SKU, warehouse, and stock state (on-hand, reserved, available). Responses are cached in Redis with a 5-second TTL.
- **Recalculation Job**: A scheduled job can recompute stock levels from the full event log for any SKU, used for reconciliation and corruption recovery.

## Repositories

- [stock-level-calculator](https://git.example.com/acme/stock-level-calculator) - Application code, migrations, consumer workers

## Runtime Environment

- **Platform**: Kubernetes / Python 3.12 with PostgreSQL 16 and RabbitMQ 3.13
- **Replicas**: 3 consumer workers minimum, autoscaling to 10 based on queue depth
- **Deployment**: Rolling via ArgoCD; migrations applied as init containers before rollout

## Dependencies

- Inventory Event Bus - source of stock movement events via RabbitMQ subscription
- Inventory Tracking Service - cross-check source for reconciliation
- PostgreSQL 16 - persistent stock level projections with row-level optimistic locking
- Redis - query result cache, 5-second TTL

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.9% monthly uptime |
| Event processing lag | P95 < 2s from event publish to level update |
| Query latency | P95 < 100ms for cached reads |
| Calculation accuracy | Zero double-counts; reconciliation variance < 0.01% |

## Runbooks

- [[RUNBOOK-021|Stock Level Calculation Runbook]]
- [[RUNBOOK-020|Stock Calculator Lag Runbook]]
