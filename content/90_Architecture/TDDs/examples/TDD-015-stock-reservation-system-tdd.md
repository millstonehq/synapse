---
id: TDD-015
type: tdd
title: Stock Reservation System TDD
status: approved
owner: Principal Engineer
created: '2025-10-03T06:24:02.103Z'
updated: '2026-10-18T13:23:33.139Z'
tags:
  - tdd
  - inventory-management
summary: Stock Reservation System TDD
related_adrs:
  - ADR-0012
  - ADR-0013
example: true
---

## Summary

Design the stock reservation system that soft-locks inventory for pending orders, preventing oversell without physically removing stock from available counts until the order is confirmed and fulfilled. The system must support atomic reservations under high concurrency, automatic reservation expiry, and partial release on order amendments. This design implements the optimistic locking approach from [[ADR-0012|ADR-0012]] and uses the CQRS read model from [[ADR-0013|ADR-0013]] to serve availability checks.

Reservations are the critical path through the order checkout flow and must meet a P99 latency budget of under 20ms.

## Overview

- **Atomic reservations via conditional writes**: Reservations use a conditional SQL update that decrements `available_qty` and fails if `available_qty < requested_qty`, preventing oversell without application-layer locks.
- **Short-lived reservations with TTL**: Each reservation carries a configurable TTL (default 15 minutes for checkout, 24 hours for B2B orders). Expired reservations are released automatically by a background job.
- **Reservation ledger**: All reservation events (created, confirmed, released, expired) are recorded in an immutable ledger for auditability.
- **Idempotent reservation creation**: Reservation requests carry an `order_id` + `order_version` idempotency key; duplicate requests return the existing reservation without creating a new one.
- **Multi-location reservation**: For orders that can be fulfilled from multiple locations, the system supports splitting a reservation across locations based on availability.

## Architecture

- **Reservation API**: HTTP service receiving reservation, confirmation, and release requests from the order service.
- **Reservation Engine**: Executes conditional SQL updates using optimistic locking per [[ADR-0012|ADR-0012]]. For DynamoDB hot-path availability checks per [[ADR-0011|ADR-0011]], the engine reads from DynamoDB and writes back atomically using conditional expressions.
- **Expiry Job**: Scheduled job that scans for reservations past their TTL and releases them, restoring `available_qty`.
- **Reservation Ledger**: Append-only PostgreSQL table recording all reservation lifecycle events for audit.
- **Availability Query**: Reads available stock from the CQRS Redis cache per [[ADR-0013|ADR-0013]] before attempting a reservation, reducing unnecessary database writes for unavailable items.

## Information Model

- **Reservation**: `reservation_id`, `order_id`, `order_version`, `sku_id`, `location_id`, `reserved_qty`, `status` (active|confirmed|released|expired), `ttl_expires_at`, `created_at`, `updated_at`
- **ReservationLedgerEntry**: `entry_id`, `reservation_id`, `event_type`, `qty`, `actor`, `occurred_at`, `metadata`
- **ReservationResult**: `reservation_id`, `status`, `sku_id`, `location_id`, `reserved_qty`, `expires_at`, `created` (bool: true if new, false if idempotent return)

## Interfaces

- `POST /v1/reservations` - Create reservation (idempotent by order_id + order_version)
- `POST /v1/reservations/{id}/confirm` - Confirm reservation (order placed; extends TTL or locks permanently)
- `DELETE /v1/reservations/{id}` - Release reservation (order cancelled or amended)
- `GET /v1/reservations/{id}` - Get reservation status
- `GET /v1/reservations?order_id={id}` - List all reservations for an order

## Files and Layout

```
cmd/reservation-api/main.go   - Entry point
internal/
  engine/                     - Reservation engine, conditional writes, retry logic
  expiry/                     - TTL expiry job, batch release logic
  ledger/                     - Reservation ledger writer and query
  availability/               - Pre-reservation availability check (Redis read model)
  handler/                    - HTTP handlers
  model/                      - Reservation, LedgerEntry domain models
  repository/                 - PostgreSQL and DynamoDB repositories
migrations/                   - Schema migrations
```

## Work Plan

1. **Phase 1 - Data model and reservation table (Week 1-2)**: Schema design, optimistic locking implementation, idempotency key handling
2. **Phase 2 - Core reservation operations (Week 3-4)**: Create, confirm, release endpoints; conditional write engine; integration tests for concurrent reservation race conditions
3. **Phase 3 - Availability pre-check (Week 5)**: Redis read model integration for pre-reservation availability check; reduces write attempts for unavailable items by estimated 40%
4. **Phase 4 - Expiry job and ledger (Week 6)**: TTL expiry background job, reservation ledger, replay safety for expiry idempotency
5. **Phase 5 - Multi-location reservation (Week 7)**: Split reservation logic, location preference algorithm, partial fulfillment handling
6. **Phase 6 - Load test at 500 concurrent reservations (Week 8)**: Validate P99 < 20ms; validate zero oversells at peak concurrency

## Risks and Mitigations

- **Risk: Conditional write retry loop under extreme flash sale concurrency causes P99 latency to exceed 20ms budget**: Mitigation: Load test at 2,000 concurrent reservation requests on top 5 SKUs; tune retry backoff; consider DynamoDB for the hottest SKUs per [[ADR-0011|ADR-0011]]
- **Risk: Expiry job releases reservations for orders still in payment processing**: Mitigation: Payment service extends reservation TTL on checkout start; default TTL of 15 minutes is conservative
- **Risk: Idempotency key collisions if order_version is not incremented on amendments**: Mitigation: Order service contract requires incrementing order_version on any amendment; validate at API boundary
