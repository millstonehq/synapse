---
id: ADR-0003
type: adr
title: Use Event Sourcing for Transaction Ledger
status: review
owner: Principal Engineer
created: '2025-02-27T04:34:07.135Z'
updated: '2025-08-05T06:31:59.257Z'
tags:
  - adr
  - payment-processing
summary: Use Event Sourcing for Transaction Ledger
example: true
---

## Context

The Transaction Ledger Service must maintain a complete, accurate, and auditable record of every payment lifecycle event. Financial regulations require a minimum 7-year retention of transaction records, and our reconciliation processes depend on being able to reconstruct the exact state of any payment at any point in time.

We are designing the data model for the ledger from scratch. The primary question is whether to use a mutable record model (where each payment row reflects current state) or an event-sourced model (where an append-only event log is the primary record and current state is derived from it).

The team has prior experience with both approaches. The mutable model is simpler to query but loses historical state transitions. The event-sourced model preserves all history but adds read complexity.

## Decision

Adopt **event sourcing** for the Transaction Ledger. The primary data store will be an append-only `payment_events` table. A `payments` materialised view (not a live table) will be maintained for efficient current-state queries.

Each event row captures: event type, from-state, to-state, amount, currency, gateway response payload, actor, and timestamp. State machine transitions are validated before events are written. The current payment state is always derivable by replaying events for a given payment ID.

## Consequences

**Positive:**
- Complete audit trail: every state change is permanently recorded with the original gateway response, enabling full forensic reconstruction for disputes and reconciliation
- Natural alignment with regulatory requirements for financial record retention
- Downstream consumers can subscribe to the event stream to maintain their own views without polling
- Easier to add new materialised views in the future without migrating existing data

**Negative:**
- Read queries for current state require either a materialised view or a fold over events — adds implementation complexity
- Materialised view must be kept consistent with the event log; requires careful transaction management on writes
- Event log will grow faster than a mutable table; partitioning and archival strategy needed

**Neutral:**
- Event sourcing is familiar to the principal engineer who will lead the implementation
- PostgreSQL can implement this pattern efficiently without specialised event store infrastructure

## Alternatives Considered

**Mutable record model (standard CRUD):**
- Pro: Simpler queries, standard ORM support, lower read latency
- Con: State history is lost on each update; reconstructing past state requires manual audit logging as a separate concern; does not naturally support event-driven downstream consumers
- Rejected because: Financial audit requirements effectively mandate a full history log. Building that as a separate audit table alongside a mutable primary table would result in two sources of truth and added synchronisation complexity.

**Dedicated event store (EventStoreDB):**
- Pro: Purpose-built for event sourcing, native event stream subscriptions
- Con: Introduces a new infrastructure dependency; team has no operational experience with EventStoreDB; significantly increases operational overhead for a use case that PostgreSQL handles well
- Rejected because: Operational risk outweighs the benefits at our current scale and team size.
