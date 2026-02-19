---
id: TDD-002
type: tdd
title: Transaction Retry Engine TDD
status: approved
owner: Tech Lead
created: '2025-05-23T21:30:55.344Z'
updated: '2026-05-26T19:12:13.338Z'
tags:
  - tdd
  - payment-processing
summary: Transaction Retry Engine TDD
related_adrs:
  - ADR-0002
  - ADR-0003
example: true
---

## Summary

Design a transaction retry engine that safely retries failed payment gateway operations without causing duplicate charges. The engine must classify errors as retryable or non-retryable, apply exponential backoff, enforce per-transaction retry limits, and integrate with the circuit breaker to avoid retrying into a degraded gateway. This TDD follows the gateway adapter decisions in [[ADR-0002|Adopt Stripe as Primary Payment Provider]] and the event sourcing approach in [[ADR-0003|Use Event Sourcing for Transaction Ledger]].

## Overview

The retry engine is a component within the `internal/gateway` package that wraps each `PaymentGateway` adapter. It intercepts errors from gateway calls and applies retry logic before propagating failures to the use case layer.

Key design principles:
- **Error classification**: HTTP 429 (rate limit), 5xx (server errors), and network timeouts are retryable. HTTP 4xx (except 429) and gateway-specific decline codes are non-retryable.
- **Exponential backoff with jitter**: Base delay of 100ms, maximum delay of 2s, jitter factor of 0.3 to prevent thundering herd.
- **Per-operation retry limits**: Authorization: 3 attempts. Capture/refund/void: 2 attempts (higher financial risk of duplication).
- **Idempotency propagation**: The idempotency key is forwarded on every retry attempt so that the gateway deduplicates server-side.

## Architecture

### Component Diagram

The retry engine sits between the use case layer and the gateway adapters:

- **Use Case Layer**: Calls gateway via `RetryingGateway` wrapper
- **RetryingGateway**: Intercepts errors, classifies them, applies backoff, records retry attempts in `payment_events`
- **CircuitBreaker**: Wraps `RetryingGateway`; if the circuit is open, the retrying gateway is bypassed entirely
- **Stripe/PayPal Adapters**: Underlying transport implementations

### Retry State Tracking

Each retry attempt is recorded as a `payment_event` with `event_type: "gateway_retry"` to maintain a complete audit trail. The event includes: attempt number, error code, backoff duration, and gateway response snippet.

## Information Model

### Core Entities

- **RetryPolicy**: Configuration per operation type. Fields: `max_attempts`, `base_delay_ms`, `max_delay_ms`, `jitter_factor`, `retryable_http_codes`
- **RetryAttempt**: Recorded in `payment_events` table. Fields: `attempt_number`, `error_code`, `error_message`, `backoff_applied_ms`
- **RetryResult**: Internal return type from the retry engine. Fields: `response`, `total_attempts`, `final_error`

### Configuration

```
RETRY_MAX_ATTEMPTS_AUTHORIZE=3
RETRY_MAX_ATTEMPTS_CAPTURE=2
RETRY_MAX_ATTEMPTS_REFUND=2
RETRY_BASE_DELAY_MS=100
RETRY_MAX_DELAY_MS=2000
RETRY_JITTER_FACTOR=0.3
```

## Interfaces

### RetryingGateway Interface

```go
type RetryingGateway struct {
    inner      PaymentGateway
    policy     RetryPolicy
    clock      Clock
    eventRepo  PaymentEventRepository
}

func (r *RetryingGateway) Authorize(ctx context.Context, req AuthRequest) (AuthResponse, error)
```

### Error Classifier

```go
type ErrorClass int
const (
    ErrorClassNonRetryable ErrorClass = iota // 4xx (except 429), decline codes
    ErrorClassRetryable                      // 429, 5xx, timeout, connection error
    ErrorClassFatal                          // Context cancelled, invalid request
)

func ClassifyGatewayError(err error) ErrorClass
```

## Files and Layout

```
internal/gateway/
  retry/
    policy.go          - RetryPolicy configuration and defaults
    engine.go          - RetryingGateway implementation
    classifier.go      - Error classification logic
    engine_test.go     - Unit tests with mock gateway
  stripe/adapter.go    - Stripe adapter (wrapped by retry engine)
  paypal/adapter.go    - PayPal adapter (wrapped by retry engine)
  circuitbreaker.go    - Circuit breaker wraps retry engine
```

## Work Plan

1. **Phase 1 (Week 1)**: Error classifier implementation and unit tests covering all HTTP status codes and gateway error types
2. **Phase 2 (Week 2)**: RetryPolicy configuration struct and default policies per operation type
3. **Phase 3 (Week 3)**: RetryingGateway implementation with backoff, jitter, and event recording
4. **Phase 4 (Week 4)**: Integration with circuit breaker and use case layer, integration tests against Stripe sandbox

## Risks and Mitigations

- **Risk**: Retrying a capture operation causes a double-charge if the first attempt succeeded but the response was lost. **Mitigation**: Always forward the idempotency key on retries; Stripe deduplicates on their side using this key. Capture is non-idempotent at the network layer but idempotent at the application layer.
- **Risk**: Over-aggressive retries amplify load on a degraded gateway. **Mitigation**: Exponential backoff with jitter limits retry volume. Circuit breaker prevents retries once the gateway is classified as unhealthy.
- **Risk**: Retry audit events grow the `payment_events` table faster than expected. **Mitigation**: Monitor `retry` event volume; if excessive, consider moving retry events to a separate `retry_log` table.

## Operations

- **Deployment**: Deployed as part of the payments-api service; no separate deployment unit.
- **Monitoring**: `gateway_retry_total` counter by operation type and attempt number; `gateway_retry_success_on_attempt_n` histogram to measure retry effectiveness.
- **Alerting**: Alert if `gateway_retry_total` rate exceeds 10% of total gateway calls over a 5-minute window — indicates a systemic gateway problem that retries alone cannot fix.
- **Rollback**: Retry policy configuration is environment-variable-driven; can be changed without a code deploy.
