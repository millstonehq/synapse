---
id: ADR-0013
type: adr
title: Adopt CQRS for Inventory Queries
status: approved
owner: Staff Engineer
created: '2024-07-27T18:52:22.787Z'
updated: '2026-03-17T08:52:59.057Z'
tags:
  - adr
  - inventory-management
summary: Adopt CQRS for Inventory Queries
example: true
---

## Context

The inventory platform's Stock Level Calculator currently handles both write operations (applying stock movement events to update projections) and read operations (serving current stock level queries to downstream consumers). These two workloads have fundamentally different characteristics. Writes are latency-tolerant but correctness-critical: an event must be applied exactly once in the correct order. Reads are latency-sensitive but can tolerate brief staleness: the order service checks availability with a 5-second staleness tolerance, and the merchant dashboard is acceptable with up to 10-second staleness.

As query volume grows — the stock level dashboard, order service, and analytics pipeline now issue approximately 180,000 queries per hour at peak — the write path and read path are competing for the same PostgreSQL connection pool and I/O bandwidth. Write latency spikes during query bursts, and query latency spikes during bulk event processing windows.

Separating the write model (event projection) from the read model (optimized query views) would allow each to scale independently and be optimized for its specific access pattern.

## Decision

Adopt Command Query Responsibility Segregation (CQRS) by separating the write model from the read model in the Stock Level Calculator. The write path continues to apply events to the `stock_levels` projection table in the existing PostgreSQL instance. The read path is served from a separate Redis-backed read model that is populated asynchronously from the write model.

After each successful projection update, the Stock Level Calculator publishes the new stock level state to a Redis hash keyed by `stock:{sku_id}:{location_id}`. The read API serves queries exclusively from Redis. Redis keys have a 10-second TTL to ensure staleness is bounded; on a cache miss, the read API falls back to the PostgreSQL projection with an opportunistic cache write.

This approach is a pragmatic CQRS implementation that does not require a separate database for the read model. The Redis cache acts as the read store, and the existing PostgreSQL projection acts as the write store and fallback.

## Consequences

**Positive:**
- Read and write paths no longer contend for the same PostgreSQL resources; each scales independently
- Query P95 improves dramatically for cache hits (Redis vs PostgreSQL: ~1ms vs ~80ms)
- Write throughput is unaffected by query bursts
- Fallback to PostgreSQL on cache miss ensures no query failures during Redis degradation

**Negative:**
- Reads are eventually consistent: up to 10 seconds of staleness during normal operation
- Cache and write model can diverge during Redis restarts or failures; fallback ensures correctness but may briefly expose stale cache data
- Additional operational complexity: Redis cache must be monitored alongside PostgreSQL projection

**Neutral:**
- Existing clients do not need to change their API; the separation is internal to the Stock Level Calculator service

## Alternatives Considered

**PostgreSQL read replicas:**
- Pro: No eventual consistency; reads are synchronous with the write model
- Con: Read replicas introduce replication lag (typically 100-500ms), which approaches the same staleness bound as the cache without the latency improvement. Adding and managing read replicas increases PostgreSQL operational overhead.
- Rejected because: Does not provide the latency improvement that motivates the change, and adds infrastructure complexity without the full separation benefits.

**Dedicated read database (separate PostgreSQL instance with materialized views):**
- Pro: Full CQRS with a purpose-built read model; supports complex analytical queries
- Con: Requires maintaining a second database cluster, ETL pipeline from write model to read model, and managing consistency across two persistent stores. Significant operational overhead.
- Rejected because: Over-engineered for the current read patterns, which are simple key-value lookups. Redis provides equivalent benefits with far less operational complexity.
