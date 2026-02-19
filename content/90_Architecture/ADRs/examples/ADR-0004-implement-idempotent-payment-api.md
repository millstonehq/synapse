---
id: ADR-0004
type: adr
title: Implement Idempotent Payment API
status: proposed
owner: Staff Engineer
created: '2025-02-04T01:56:35.819Z'
updated: '2025-01-02T05:33:58.610Z'
tags:
  - adr
  - payment-processing
summary: Implement Idempotent Payment API
example: true
supersedes: ADR-0005
---

## Context

Payment API mutation operations (authorize, capture, refund, void) carry financial consequences if executed more than once. Network failures, client-side timeouts, and retry logic in upstream services can all cause the same request to reach our API multiple times. Without idempotency guarantees, these scenarios can result in double charges, double refunds, or unexpected payment state transitions.

This is a common problem in distributed payment systems. The industry standard approach is to require clients to provide an idempotency key with each mutation request and for the server to guarantee that the same key will always return the same result, regardless of how many times it is submitted.

We need to decide on the idempotency mechanism: whether to implement server-side idempotency, and if so, how to store and validate keys.

## Decision

Implement **server-side idempotency** for all payment mutation endpoints. Clients must include an `Idempotency-Key` header (UUID v4 format) with every request to `POST /v1/payments/authorize`, `POST /v1/payments/{id}/capture`, `POST /v1/payments/{id}/refund`, and `POST /v1/payments/{id}/void`.

The server will store idempotency keys in Redis with a 7-day TTL, keyed by `client_id:idempotency_key`. On receiving a request, the server checks for an existing record. If found, it returns the cached response. If not found, it processes the request and stores the result before responding. A unique constraint on `(client_id, idempotency_key)` in PostgreSQL provides a durable fallback if Redis is unavailable.

## Consequences

**Positive:**
- Eliminates duplicate charges and double refunds caused by client retries
- Clients can safely retry any mutation request without risk of unintended side effects
- Aligns with Stripe's own idempotency key model, which is familiar to developers
- Redis storage provides sub-millisecond lookup latency for the common case

**Negative:**
- Clients must generate and manage idempotency keys — adds SDK/client implementation burden
- Idempotency key storage requires Redis and a database fallback, adding infrastructure complexity
- Keys with different request bodies for the same idempotency key must return a `409 Conflict` — this edge case requires careful handling and clear error messages

**Neutral:**
- The 7-day TTL is a trade-off; longer TTLs reduce duplicate risk but increase storage costs

## Alternatives Considered

**Request fingerprinting (server-derives key from request body):**
- Pro: No client changes required; server detects duplicates automatically
- Con: Fingerprinting collisions are possible; legitimate identical requests (same customer, same amount) would be incorrectly treated as duplicates; difficult to tune correctly
- Rejected because: The false-positive rate for legitimate identical requests is unacceptable in a financial context.

**No idempotency (at-most-once delivery):**
- Pro: Simplest implementation; no additional storage required
- Con: Any network failure or retry causes a duplicate charge. This is unacceptable for a payment API.
- Rejected because: The financial and customer-trust risk of duplicate charges far outweighs the implementation cost of idempotency.
