---
id: ADR-0010
type: adr
title: Use Event Sourcing for Stock Movements
status: approved
owner: Principal Engineer
created: '2024-01-04T00:49:14.961Z'
updated: '2026-11-13T08:00:39.785Z'
tags:
  - adr
  - inventory-management
summary: Use Event Sourcing for Stock Movements
example: true
---

## Context

The inventory platform needs to maintain accurate, auditable stock levels across multiple warehouses. The initial design stored only the current stock quantity per SKU per location, updated in place by each stock movement. This approach has significant operational shortcomings that have become apparent as the platform scales.

First, there is no audit trail. When a stock level appears incorrect, there is no way to determine what series of movements produced it or identify where an error was introduced. Correcting discrepancies requires manual intervention without confidence that the correction is complete. Second, the system cannot answer historical questions such as "what was the on-hand quantity for SKU X at Warehouse Y on January 15?" These queries are essential for reconciliation, financial reporting, and dispute resolution with warehouse partners. Third, adding new downstream consumers (analytics, forecasting, reorder systems) requires those consumers to periodically poll for changed stock levels rather than reacting to a reliable event stream.

The team considered continuing with the current in-place update model, enhanced with a change log table appended to on each write. However, this hybrid approach adds complexity without providing the same guarantees as a true event-sourced model.

## Decision

Adopt event sourcing as the storage model for all stock movements. Each stock movement — receipt, pick, transfer, adjustment, reservation, release — is recorded as an immutable event with a signed quantity delta, a timestamp, an idempotency key, and metadata describing the source (warehouse, order, cycle count). The current stock level for any SKU at any location is always a derived projection computed by replaying the event log from the last snapshot.

A snapshot mechanism captures the current projection state periodically (every 1,000 events per partition by default) to bound replay time on service restart. The event log is the system of record; snapshots are a performance optimization only.

## Consequences

**Positive:**
- Full audit trail for every stock movement; any discrepancy can be traced to its root event
- Point-in-time reconstruction enabled by replaying the event log to any point
- New consumers can subscribe to the event stream without modifying the core service
- Corrections are transparent: a corrective event is appended rather than silently overwriting a value

**Negative:**
- Current stock level requires a projection layer; direct SQL queries on a single table are no longer possible
- Snapshot management adds operational complexity (when to snapshot, storage cost for growing event log)
- Event ordering must be enforced per partition; out-of-order delivery requires reordering logic

**Neutral:**
- Event retention costs scale linearly with movement volume; 90-day default retention requires active monitoring

## Alternatives Considered

**In-place update with append-only change log:**
- Pro: Simpler architecture; current stock readable in a single table
- Con: Change log is a second-class citizen; queries and replay logic are more complex than a pure event-sourced model
- Rejected because: The hybrid approach provides neither the simplicity of in-place updates nor the full benefits of event sourcing

**Temporal tables (bi-temporal history):**
- Pro: SQL-native; no application-layer projection
- Con: Does not provide a publishable event stream for downstream consumers; temporal queries require non-standard SQL syntax
- Rejected because: Does not solve the event fan-out requirement and ties us to PostgreSQL-specific temporal table features
