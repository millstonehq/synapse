---
id: ADR-0011
type: adr
title: Choose DynamoDB for Inventory Hot Path
status: approved
owner: Staff Engineer
created: '2024-08-16T17:39:56.828Z'
updated: '2026-09-03T04:37:02.140Z'
tags:
  - adr
  - inventory-management
summary: Choose DynamoDB for Inventory Hot Path
example: true
---

## Context

The inventory platform's "hot path" encompasses all operations that must respond within the order checkout flow: availability checks, stock reservations, and reservation releases. These operations are called synchronously by the order service during checkout and must meet a P99 latency budget of under 20ms to avoid degrading the checkout experience.

Current throughput requirements are 500 reservation operations per second at peak, with projections reaching 2,000/s within 18 months as the merchant base grows. The existing PostgreSQL-based implementation handles the current load adequately but shows latency spikes above the 20ms budget at peak because advisory locks on heavily-contested SKUs create queue buildup. PostgreSQL's single-leader replication model also limits horizontal read scale.

The team needs a data store for the hot-path reservation state that provides single-digit millisecond latency at any scale, automatic horizontal scaling without operational intervention, and strong per-item consistency for the read-modify-write pattern that reservations require.

## Decision

Use DynamoDB as the primary data store for the inventory hot path. Stock availability and reservation state will be stored in a DynamoDB table partitioned by `sku_id` and sorted by `location_id`. Reservations will use DynamoDB's conditional write expressions (`ConditionExpression: available_qty >= :requested`) to ensure atomicity without application-layer locking. The stock level projection maintained by the Stock Level Calculator will continue to write to PostgreSQL for query flexibility; DynamoDB holds only the hot-path reservation state.

The DynamoDB table will use on-demand capacity mode to handle traffic spikes without manual provisioning, with a cost alerting threshold at $3,000/month.

## Consequences

**Positive:**
- Single-digit millisecond P99 latency for reservation operations at any throughput level
- Automatic horizontal scaling eliminates capacity planning for the hot path
- Conditional writes provide atomic reservation without application-layer distributed locks
- No connection pool to manage; SDK handles connection reuse internally

**Negative:**
- DynamoDB's limited query model requires all access patterns to be designed upfront; ad-hoc queries require DynamoDB Streams → S3 export for analytics
- On-demand pricing can be significantly more expensive than provisioned capacity at steady high throughput; must monitor and switch to provisioned capacity if spend exceeds projections
- Operational team needs to learn DynamoDB concepts (GSIs, partition key design, conditional expressions)

**Neutral:**
- Stock state is split across two stores: DynamoDB (reservation hot path) and PostgreSQL (full projection); reconciliation between the two must be maintained

## Alternatives Considered

**Redis (ElastiCache):**
- Pro: Sub-millisecond latency, familiar to the team, supports Lua scripts for atomic operations
- Con: In-memory only; persistence requires AOF/RDB with durability trade-offs. Cluster failover can cause a brief cold-cache period (as demonstrated in the Oct 14 cache stampede incident). Not designed as a primary data store.
- Rejected because: Durability and cold-start risk are unacceptable for reservation state. A Redis failure during a flash sale could cause oversells.

**PostgreSQL with optimistic locking:**
- Pro: No new technology; existing expertise; full query flexibility
- Con: Advisory lock contention is the current problem; optimistic locking shifts to application-layer retry loops under high contention, which increases latency variance. Does not scale reads horizontally without read replicas and application routing complexity.
- Rejected because: Does not address the P99 latency spike problem at peak traffic and does not provide the scaling headroom for 18-month growth projections.
