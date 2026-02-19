---
id: TDD-011
type: tdd
title: Real-Time Stock Level Service TDD
status: deprecated
owner: Principal Engineer
created: '2025-12-19T02:25:39.244Z'
updated: '2025-12-29T10:54:15.540Z'
tags:
  - tdd
  - inventory-management
summary: Real-Time Stock Level Service TDD
related_adrs:
  - ADR-0010
  - ADR-0013
example: true
---

## Summary

Design a real-time stock level service that maintains accurate on-hand, reserved, and available quantity projections per SKU per warehouse location. The service must process stock movement events with sub-2-second lag, serve availability queries at P95 < 100ms, and support point-in-time reconstruction via event replay. This design implements the event sourcing approach decided in [[ADR-0010|ADR-0010]] and the CQRS read model pattern from [[ADR-0013|ADR-0013]].

The service is the authoritative source for all stock quantity data consumed by the order management system, merchant dashboard, and reorder automation.

## Overview

- **Event-sourced write model**: Stock levels are derived projections, never stored directly. All mutations flow through an immutable event log.
- **CQRS read model**: Availability queries are served from a Redis cache populated asynchronously from the write projection, providing sub-10ms latency.
- **Optimistic concurrency**: Concurrent writes to the same SKU/location partition use version-based optimistic locking to prevent lost updates.
- **Idempotent processing**: Events carry an idempotency key; duplicate deliveries are detected and discarded using the `last_event_seq` per partition.
- **Snapshot-based recovery**: Periodic snapshots bound replay time to < 30 seconds on cold start.

## Architecture

- **Event Consumer**: RabbitMQ consumer workers subscribe to stock movement topics. Workers are assigned to partitions to ensure ordered processing per `(sku_id, location_id)`.
- **Calculation Engine**: Applies event deltas to PostgreSQL projections using optimistic locking. On conflict, retries with exponential backoff (base 10ms, max 500ms, 5 attempts).
- **Read Cache Writer**: After each successful projection update, publishes the new stock state to Redis (`stock:{sku_id}:{location_id}`, TTL 10 seconds).
- **Query API**: HTTP service that reads from Redis with PostgreSQL fallback. Stateless; scales horizontally.
- **Snapshot Job**: Scheduled job that writes current projection state to the snapshot store every 1,000 events per partition.

## Information Model

- **StockLevel**: `sku_id`, `location_id`, `on_hand_qty`, `reserved_qty`, `available_qty` (derived: on_hand - reserved), `version`, `last_event_seq`, `snapshot_at`
- **StockEvent**: `event_id`, `event_type`, `sku_id`, `location_id`, `delta`, `sequence_number`, `occurred_at`, `source`, `idempotency_key`
- **StockSnapshot**: `sku_id`, `location_id`, `on_hand_qty`, `reserved_qty`, `version`, `snapshotted_at`, `event_seq_at_snapshot`

## Interfaces

- `GET /v1/stock/{sku_id}/{location_id}` - Current stock levels (from Redis cache)
- `GET /v1/stock/{sku_id}` - Aggregated stock across all locations for a SKU
- `POST /v1/stock/bulk-check` - Batch availability check for up to 100 SKUs
- `GET /v1/stock/{sku_id}/{location_id}/history?at={timestamp}` - Point-in-time stock level via event replay

## Files and Layout

```
cmd/calculator/main.go         - Entry point, dependency injection
internal/
  consumer/                    - RabbitMQ consumer workers, partition assignment
  engine/                      - Calculation engine, optimistic locking, retry logic
  snapshot/                    - Snapshot writer and reader
  cache/                       - Redis cache writer and read-through logic
  query/                       - HTTP query API handlers
  model/                       - StockLevel, StockEvent, StockSnapshot entities
  repository/                  - PostgreSQL repositories
migrations/                    - Database migration files
```

## Work Plan

1. **Phase 1 - Data model and persistence (Week 1-2)**: StockLevel and StockEvent schemas, PostgreSQL repositories, optimistic locking implementation
2. **Phase 2 - Event consumer (Week 3-4)**: RabbitMQ consumer, partition assignment, idempotency checking, calculation engine with retry logic
3. **Phase 3 - CQRS read model (Week 5)**: Redis cache writer, query API with fallback, bulk check endpoint
4. **Phase 4 - Snapshot system (Week 6)**: Snapshot writer job, cold-start replay from snapshot, snapshot storage management
5. **Phase 5 - Point-in-time query (Week 7)**: Historical query endpoint, event replay logic, time-bounded replay performance
6. **Phase 6 - Load testing and hardening (Week 8)**: 2x peak throughput load test, latency validation, runbook and alerting

## Risks and Mitigations

- **Risk: Hot partition write contention under flash sale traffic**: Mitigation: Load test at 10x normal throughput for top 10 SKUs; tune retry backoff based on observed conflict rates
- **Risk: Redis cold-start after restart causes query latency spike**: Mitigation: Implement predictive cache warm-up on startup for top 1,000 SKUs by query frequency
- **Risk: Event replay time exceeds 30s target for large SKU catalogs**: Mitigation: Tune snapshot frequency; benchmark replay time at different snapshot intervals
