---
id: ADR-0012
type: adr
title: Implement Optimistic Locking for Stock Updates
status: accepted
owner: Principal Engineer
created: '2024-08-14T18:48:10.143Z'
updated: '2026-02-02T03:22:14.749Z'
tags:
  - adr
  - inventory-management
summary: Implement Optimistic Locking for Stock Updates
example: true
---

## Context

The Stock Level Calculator applies stock movement events to the `stock_levels` projection table in PostgreSQL. Under normal operation, events for a given `(sku_id, location_id)` partition arrive serially and are applied without conflict. However, under certain conditions — service restarts, parallel consumer workers, and event replay operations — concurrent writes to the same partition can occur.

Without concurrency control, concurrent writes risk two failure modes: (1) a lost update where two workers read the same base quantity, apply their respective deltas, and write back different final values — one overwriting the other's change; or (2) out-of-order application of events producing an incorrect projection state. Both failure modes result in stock level inaccuracy that is difficult to detect and costly to remediate.

The Stock Level Calculator processes approximately 15,000 events per day across 850,000 active SKU/location combinations. Hot partitions (high-velocity SKUs in busy warehouses) can receive 50-100 events per hour. A locking strategy must prevent write conflicts without creating throughput bottlenecks on these hot partitions.

## Decision

Implement optimistic locking on the `stock_levels` table using a `version` column. Each row includes a monotonically increasing `version` integer. The update pattern is:

```sql
UPDATE stock_levels
SET on_hand_qty = :new_qty, version = version + 1, last_event_seq = :seq
WHERE sku_id = :sku_id AND location_id = :location_id AND version = :expected_version
```

If the update affects 0 rows (another worker incremented the version first), the worker re-reads the current row and retries. Retries use exponential backoff with jitter (base 10ms, max 500ms, 5 attempts). After 5 failed retries the event is dead-lettered for manual review.

Additionally, the `last_event_seq` column tracks the sequence number of the last applied event per partition. Incoming events with a sequence number ≤ `last_event_seq` are discarded as duplicates.

## Consequences

**Positive:**
- No database-level locks held; writers that don't conflict incur no additional latency
- Version column provides a natural conflict detection mechanism without coordination between workers
- Sequence tracking eliminates duplicate application of events during replay or redelivery

**Negative:**
- Hot partitions under heavy write contention will experience retry overhead; workers must be designed for fast, idempotent retries
- Dead-lettered events after 5 retries require manual investigation; operational procedures needed
- Adds a `version` column and retry loop complexity to the calculation engine

**Neutral:**
- Retry frequency is low in practice: observed conflict rate is < 0.1% of updates in current load testing at 2x peak throughput

## Alternatives Considered

**Pessimistic locking (SELECT FOR UPDATE):**
- Pro: Guarantees serialization without retries; no lost update risk
- Con: Holds row-level locks for the duration of the write transaction. Under high concurrency on hot partitions, lock queue buildup increases P95 latency significantly. This was the previous approach and was responsible for the latency issues that prompted this review.
- Rejected because: Lock contention was the problem being solved; pessimistic locking perpetuates it.

**Single-writer-per-partition (partition ownership):**
- Pro: No concurrency conflict at all within a partition; each partition has exactly one writer
- Con: Requires a partition assignment and rebalancing mechanism (similar to Kafka consumer groups). Adds operational complexity. Worker failures require partition reassignment with potential reprocessing gaps.
- Rejected because: Adds significant infrastructure complexity. Optimistic locking provides adequate conflict prevention at current and projected throughput levels without ownership coordination.
