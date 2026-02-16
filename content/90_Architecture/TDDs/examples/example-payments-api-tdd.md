---
id: payments-api-tdd
type: tdd
title: Payments API - Technical Design
status: approved
owner: Principal Engineer
created: '2025-10-18T00:00:00.000Z'
updated: '2025-10-18T00:00:00.000Z'
tags:
  - tdd
  - payments
  - architecture
summary: >-
  Detailed technical design for the Payments API service. USE A TDD when
  you are DESIGNING something that will be built - a new service, major
  feature, or significant refactor. TDDs answer "how will we build X?"
  with architecture, data models, interfaces, implementation plan, and
  risk analysis. They are forward-looking design documents that become
  historical records once the system is built. Compare: an ADR captures
  a single decision; a TDD captures the full design. A System doc
  describes what exists; a TDD describes what will exist. A PRD defines
  what the product needs; a TDD defines how engineering will deliver it.
related_adrs:
  - ADR-0001
example: true
---

## Summary

Design a payment processing service that handles authorization, capture, and refunds with idempotency, automatic retries, and gateway failover. The service must support 200 TPS at peak, maintain 99.9% availability, and integrate with Stripe (primary) and PayPal (secondary) gateways.

This TDD implements the payment processing requirements from the [[example-payments-api-prd|Payments API PRD]] and follows the gateway adapter pattern decided in [[example-choose-quartz-4-adr|ADR-0001]].

## Overview

The Payments API is a Go microservice deployed on Kubernetes that provides RESTful endpoints for payment operations. It uses a hexagonal architecture to isolate business logic from gateway-specific implementations, enabling easy addition of new payment providers.

Key design principles:
- **Idempotency**: Every mutation endpoint accepts an idempotency key to prevent duplicate charges
- **State machine**: Payment lifecycle is modeled as a state machine with explicit transitions and audit logging
- **Circuit breaker**: Gateway calls are wrapped in circuit breakers to enable automatic failover
- **Event sourcing**: All payment state changes are published as events for downstream consumers

## Architecture

### Component Diagram

The service has four layers:

- **HTTP Handler Layer**: Validates requests, enforces authentication, applies rate limiting, routes to use cases
- **Use Case Layer**: Orchestrates business logic, enforces state machine transitions, manages idempotency
- **Gateway Adapter Layer**: Implements the `PaymentGateway` interface for each provider (Stripe, PayPal), handles retries and circuit breaking
- **Repository Layer**: Manages persistence via PostgreSQL, handles optimistic locking on state transitions

### State Machine

Payment states and valid transitions:

- `pending` → `authorized` (successful auth) or `failed` (auth declined)
- `authorized` → `captured` (capture request) or `voided` (void request) or `expired` (24h timeout)
- `captured` → `settled` (settlement batch) or `refund_pending` (refund request)
- `refund_pending` → `refunded` (refund confirmed) or `refund_failed` (refund declined)

## Information Model

### Core Entities

- **Payment**: The primary entity. Fields: `id`, `idempotency_key`, `amount`, `currency`, `state`, `gateway`, `gateway_ref`, `customer_id`, `metadata`, `created_at`, `updated_at`
- **PaymentEvent**: Immutable audit log. Fields: `id`, `payment_id`, `event_type`, `from_state`, `to_state`, `gateway_response`, `created_at`
- **PaymentMethod**: Tokenized payment instruments. Fields: `id`, `customer_id`, `type`, `token`, `last_four`, `expiry`, `is_default`, `created_at`

### Database Schema

- `payments` table with unique constraint on `idempotency_key`, index on `customer_id` and `state`
- `payment_events` table with foreign key to `payments`, index on `payment_id` and `created_at`
- `payment_methods` table with unique constraint on `(customer_id, token)`, index on `customer_id`

## Interfaces

### Public API

- `POST /v1/payments/authorize` - Create and authorize a payment
- `POST /v1/payments/{id}/capture` - Capture an authorized payment
- `POST /v1/payments/{id}/refund` - Refund a captured payment
- `POST /v1/payments/{id}/void` - Void an authorized payment
- `GET /v1/payments/{id}` - Get payment details and event history
- `GET /v1/payments?customer_id={id}` - List payments for a customer

### Internal Interface (Gateway Adapter)

```go
type PaymentGateway interface {
    Authorize(ctx context.Context, req AuthRequest) (AuthResponse, error)
    Capture(ctx context.Context, ref string, amount Money) (CaptureResponse, error)
    Refund(ctx context.Context, ref string, amount Money) (RefundResponse, error)
    Void(ctx context.Context, ref string) (VoidResponse, error)
}
```

## Files and Layout

```
cmd/payments/main.go          - Entry point, dependency injection
internal/
  handler/                     - HTTP handlers, request/response types
  usecase/                     - Business logic, state machine
  gateway/
    stripe/                    - Stripe adapter implementation
    paypal/                    - PayPal adapter implementation
  repository/                  - PostgreSQL repositories
  model/                       - Domain entities, value objects
  event/                       - Event publishing (SQS)
migrations/                    - Database migration files
deploy/
  helm/                        - Kubernetes Helm chart
  terraform/                   - Infrastructure as code
```

## Work Plan

1. **Phase 1 - Foundation (Week 1-2)**: Database schema, entity models, repository layer, basic HTTP server scaffold
2. **Phase 2 - Core Logic (Week 3-4)**: State machine implementation, authorization/capture/refund use cases, idempotency enforcement
3. **Phase 3 - Gateway Integration (Week 5-6)**: Stripe adapter, circuit breaker wrapper, integration tests against Stripe test mode
4. **Phase 4 - Resilience (Week 7)**: PayPal adapter, failover logic, retry policies, load testing
5. **Phase 5 - Observability (Week 8)**: Structured logging, metrics (Prometheus), distributed tracing, alerting rules
6. **Phase 6 - Hardening (Week 9-10)**: Security audit, penetration testing, documentation, production readiness review

## Risks and Mitigations

- **Risk**: Gateway API changes break our adapters. **Mitigation**: Pin gateway SDK versions, run integration tests nightly against sandbox environments, subscribe to provider changelogs.
- **Risk**: Idempotency key collisions across clients. **Mitigation**: Use UUID v4 for idempotency keys with a unique constraint. Return 409 Conflict if a different request reuses a key.
- **Risk**: State machine race conditions under concurrent requests. **Mitigation**: Use PostgreSQL `SELECT FOR UPDATE` on payment rows during state transitions. Return 409 if the payment is already in a terminal state.
- **Risk**: Circuit breaker opens too aggressively, causing unnecessary failover. **Mitigation**: Tune thresholds based on baseline error rates. Start conservative (10 failures in 60s) and adjust after observing production traffic.

## Operations

- **Deployment**: Blue-green via ArgoCD. Health check endpoint at `/healthz` checks DB and Redis connectivity.
- **Monitoring**: Grafana dashboards for request rate, error rate, latency percentiles, gateway success rates, circuit breaker state.
- **Alerting**: PagerDuty alerts for error rate > 1% (5min window), P95 latency > 1s (5min window), circuit breaker open.
- **Rollback**: Automated via ArgoCD if health checks fail. Database migrations are backward-compatible (additive only in production).
