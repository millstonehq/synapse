---
id: WIKI-002
type: wiki
title: Transaction State Machine - Deep Dive
status: draft
owner: Payment Team
created: '2025-09-06T17:09:53.956Z'
updated: '2025-11-12T15:26:52.628Z'
tags:
  - wiki
  - payment-processing
summary: Transaction State Machine - Deep Dive
source_repo: https://git.example.com/acme/transaction-state-machine
commit_sha: 74844010b5119d53281a0388a1e34b6828467316
generated_at: '2025-08-04T05:32:42.138Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: claude-3-sonnet
importance: high
example: true
---

## Overview

The transaction state machine governs every legal transition in the payment lifecycle. All state changes are validated against a strict transition table before any database write or gateway call is made. Attempting an invalid transition (e.g., capturing an already-captured payment) returns a `409 Conflict` response immediately.

This page documents the states, transitions, and implementation details of the state machine as it exists in `internal/model/payment.go` and `internal/usecase/payment_usecase.go`.

## States

- **`pending`** - Payment created, no authorization attempted yet.
- **`authorized`** - Funds held by the gateway. Capture or void must occur within 24 hours.
- **`captured`** - Funds captured from the customer's card. Awaiting settlement.
- **`settled`** - Gateway has settled the funds to the merchant account.
- **`voided`** - Authorization released before capture. No funds moved.
- **`failed`** - Authorization was declined by the gateway or issuing bank.
- **`refund_pending`** - Refund initiated, awaiting gateway confirmation.
- **`refunded`** - Refund confirmed by the gateway.
- **`refund_failed`** - Refund was declined or errored.

## Transitions

| From | Event | To | Notes |
|------|-------|-----|-------|
| `pending` | Auth success | `authorized` | |
| `pending` | Auth declined | `failed` | Terminal state |
| `authorized` | Capture request | `captured` | Partial capture supported |
| `authorized` | Void request | `voided` | Terminal state |
| `authorized` | 24h timeout | `expired` | Background job |
| `captured` | Settlement batch | `settled` | Async, from gateway webhook |
| `captured` | Refund request | `refund_pending` | |
| `refund_pending` | Refund confirmed | `refunded` | Terminal state |
| `refund_pending` | Refund declined | `refund_failed` | |

## Implementation

The `Payment.CanTransitionTo(state)` method in `internal/model/payment.go` encodes the transition table as a map. The `PaymentUseCase` calls `CanTransitionTo` before every mutation, returning `ErrInvalidTransition` if the transition is not permitted. This error surfaces as a `409 Conflict` to callers.

Database writes and event inserts are wrapped in a single PostgreSQL transaction. The payment row is locked with `SELECT FOR UPDATE` before the state is updated, preventing concurrent requests from making conflicting transitions.

## Key Packages

- `internal/model/payment.go` - State constants, `CanTransitionTo`, `Payment` struct
- `internal/usecase/payment_usecase.go` - Transition orchestration, idempotency, event publishing
- `internal/repository/payment_repository.go` - `SELECT FOR UPDATE` locking, state update queries

## Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| `github.com/jackc/pgx/v5` | v5.5.1 | PostgreSQL driver with transaction support |
| `github.com/redis/go-redis/v9` | v9.3.0 | Idempotency key cache |
| `github.com/aws/aws-sdk-go-v2` | v1.24.0 | SQS event publishing post-transition |

`cmd/payments/main.go` initializes the application using manual dependency injection (no DI framework). The startup sequence:

1. Load configuration from environment variables
2. Initialize PostgreSQL connection pool (max 60 connections)
3. Initialize Redis client
4. Create repository instances
5. Create gateway adapters (Stripe primary, PayPal secondary)
6. Wrap gateways in circuit breaker middleware
7. Create use case instances with injected dependencies
8. Register HTTP handlers and middleware (auth, rate limiting, logging)
9. Start HTTP server on `:8080` with graceful shutdown on SIGTERM

## Key Packages

### `internal/handler`

HTTP request handlers using Go's standard `net/http` package. Each handler:
- Validates the request body using struct tags
- Extracts the JWT claims from the request context (set by auth middleware)
- Calls the appropriate use case method
- Returns JSON responses with appropriate status codes

Key handlers: `AuthorizeHandler`, `CaptureHandler`, `RefundHandler`, `VoidHandler`, `GetPaymentHandler`, `ListPaymentsHandler`.

### `internal/usecase`

Business logic layer. The `PaymentUseCase` struct orchestrates:
- Idempotency key checking (returns cached response if key exists)
- Payment state machine validation (rejects invalid transitions)
- Gateway calls via the `PaymentGateway` interface
- Event publishing to SQS after successful state transitions
- Transaction management (database transaction wraps state change + event insert)

### `internal/gateway`

Gateway adapter implementations behind the `PaymentGateway` interface:

```go
type PaymentGateway interface {
    Authorize(ctx context.Context, req AuthRequest) (AuthResponse, error)
    Capture(ctx context.Context, ref string, amount Money) (CaptureResponse, error)
    Refund(ctx context.Context, ref string, amount Money) (RefundResponse, error)
    Void(ctx context.Context, ref string) (VoidResponse, error)
}
```

- `stripe/adapter.go` - Stripe integration using `stripe-go` SDK v76
- `paypal/adapter.go` - PayPal integration using REST API v2

Both adapters are wrapped by `gateway/circuitbreaker.go` which implements the circuit breaker pattern (closed -> open after 5 failures in 30s, half-open after 60s recovery).

### `internal/repository`

PostgreSQL repositories using `pgx` v5 connection pool:
- `PaymentRepository` - CRUD operations on the `payments` table with `SELECT FOR UPDATE` on state transitions
- `PaymentEventRepository` - Append-only inserts into `payment_events`
- `PaymentMethodRepository` - Tokenized payment method storage

### `internal/model`

Domain entities and value objects:
- `Payment` struct with state machine methods (`CanCapture()`, `CanRefund()`, etc.)
- `PaymentEvent` immutable audit record
- `Money` value object (amount + currency) with arithmetic methods
- State constants and transition validation

## Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| `github.com/jackc/pgx/v5` | v5.5.1 | PostgreSQL driver and connection pool |
| `github.com/redis/go-redis/v9` | v9.3.0 | Redis client for caching |
| `github.com/stripe/stripe-go/v76` | v76.12.0 | Stripe API SDK |
| `github.com/aws/aws-sdk-go-v2` | v1.24.0 | SQS event publishing |
| `github.com/sony/gobreaker/v2` | v2.0.0 | Circuit breaker implementation |
| `golang.org/x/time` | v0.5.0 | Rate limiting (token bucket) |

## Generation Notes

Generated from commit `a1b2c3d` on the `main` branch. The generator analyzed Go source files, extracted package structure, interface definitions, and struct fields to produce this overview. Manual review is recommended for accuracy.
