---
id: ADR-0005
type: adr
title: Choose PostgreSQL for Payment Data Store
status: deprecated
owner: Principal Engineer
created: '2025-01-14T18:53:58.480Z'
updated: '2026-05-06T08:52:47.149Z'
tags:
  - adr
  - payment-processing
summary: Choose PostgreSQL for Payment Data Store
example: true
---

## Context

The payment platform requires a relational data store for its core transactional data: payments, payment events, and payment methods. The data store must support ACID transactions, row-level locking for concurrent state machine transitions, and complex queries for reconciliation and reporting.

Key requirements for the data store: strong consistency guarantees for financial transactions, efficient support for the event-sourced `payment_events` table (append-only, high write volume), `SELECT FOR UPDATE` for optimistic locking during state transitions, and table partitioning for the large `payment_events` table as it grows. The team has strong PostgreSQL expertise and existing PostgreSQL infrastructure. We process approximately 50,000 transactions per day at peak.

## Decision

Use **PostgreSQL 16** as the primary data store for all payment platform data.

The payments schema will include: `payments` (primary transaction table), `payment_events` (append-only event log, partitioned by month), and `payment_methods` (tokenized card data). The `payment_events` table uses range partitioning on `created_at` to support efficient archival and query performance. All state machine transitions use `SELECT FOR UPDATE` with serializable transaction isolation to prevent race conditions. Connection pooling is managed by PgBouncer in transaction mode with a pool size of 60 per pod.

## Consequences

**Positive:**
- Full ACID compliance ensures financial data integrity under concurrent operations
- `SELECT FOR UPDATE` provides row-level locking for state machine transitions without application-level distributed locks
- Native table partitioning on `payment_events` supports the 7-year retention requirement without impacting query performance
- PostgreSQL's `pg_stat_activity` and `pg_locks` views enable real-time diagnosis of connection pool saturation and lock contention
- Strong team expertise reduces operational risk and onboarding time

**Negative:**
- Schema migrations must be carefully managed — additive-only migrations in production rule out some refactoring options
- The `payment_events` table will grow at approximately 150,000 rows per day; partition management and archival must be operationalized
- Horizontal write scaling requires sharding, which is not currently needed but limits future growth path

**Neutral:**
- PgBouncer adds a deployment component but is already in use across other services
- PostgreSQL 16 is the current LTS version; the next major upgrade window will occur in approximately 3 years

## Alternatives Considered

**MySQL 8.0:**
- Pro: Mature ecosystem, strong replication support, lower memory footprint per connection
- Con: Row-level locking semantics differ subtly from PostgreSQL in edge cases involving `SELECT FOR UPDATE SKIP LOCKED`; the team has no MySQL operational experience; JSON query support is less capable than PostgreSQL's `jsonb` type, which we use for `gateway_response` storage
- Rejected because: Team expertise gap and inferior `jsonb` support would slow development and increase operational risk.

**MongoDB:**
- Pro: Flexible schema, good horizontal scalability, native document model for `gateway_response` payloads
- Con: Multi-document ACID transactions were only added in v4.0 and carry significant performance overhead; the payment state machine relies on atomic reads and writes across the `payments` and `payment_events` tables in a single transaction, which is natural in PostgreSQL but costly in MongoDB
- Rejected because: Financial transaction integrity requires strong multi-row ACID guarantees that PostgreSQL provides natively and MongoDB cannot match without significant performance cost.
