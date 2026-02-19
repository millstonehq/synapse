---
id: WIKI-041
type: wiki
title: Payment Gateway - Failover Patterns
status: approved
owner: Payment Team
created: '2025-09-27T21:31:33.220Z'
updated: '2026-03-12T16:09:27.599Z'
tags:
  - wiki
  - payment-processing
summary: Payment Gateway - Failover Patterns
source_repo: https://git.example.com/acme/payment-gateway
commit_sha: 95b3e168c9767c8a550d872a4f3101b8fd143ba4
generated_at: '2025-09-24T18:52:01.424Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: gpt-4o
importance: high
example: true
---

## Overview

The payment platform uses a multi-gateway architecture with Stripe as the primary gateway and PayPal as the secondary fallback. This page documents the failover patterns, circuit breaker configuration, and operational behaviors that govern how the platform responds to gateway degradation and outages.

Understanding these patterns is essential for on-call engineers responding to gateway incidents and for engineers making changes to the gateway adapter layer.

## Gateway Architecture

The platform routes all payment operations through a layered gateway stack:

1. **PaymentGateway interface** — the abstraction layer; use cases call this interface without knowing which gateway will handle the request
2. **CircuitBreakerGateway** — wraps each adapter; tracks failures and manages the open/closed/half-open state transitions
3. **RetryingGateway** — wraps each adapter; applies exponential backoff for transient errors (excluding 429 responses)
4. **StripeAdapter / PayPalAdapter** — the concrete implementations that call the respective gateway APIs
5. **GatewayRouter** — selects between Stripe and PayPal based on circuit breaker state; falls back to PayPal when Stripe's circuit is open

## Circuit Breaker Configuration

The circuit breaker is implemented using `gobreaker/v2` (Sony's circuit breaker library). Current production configuration:

| Parameter | Stripe | PayPal |
|---|---|---|
| Failure threshold | 3 failures in 10s | 5 failures in 30s |
| Recovery timeout | 60s (half-open) | 60s (half-open) |
| Success threshold to close | 2 consecutive successes | 2 consecutive successes |
| Timeout per request | 5s | 8s |

The Stripe threshold was tightened from 5/30s to 3/10s following POSTMORTEM-005 (INC-76), where the original threshold caused 5 minutes of cascading failures before the circuit opened.

## Failover Sequence

When Stripe's circuit breaker opens:

1. The `GatewayRouter` immediately starts routing new requests to PayPal
2. Existing in-flight Stripe requests continue until they complete or time out
3. The `circuit_breaker_state` metric transitions to `open` — this triggers a PagerDuty alert
4. PayPal handles traffic during Stripe's 60-second recovery window
5. After 60 seconds, the circuit enters `half-open` state and allows 1 test request through
6. If the test request succeeds, the circuit closes and Stripe resumes handling traffic
7. If the test request fails, the circuit reopens for another 60 seconds

## Error Classification

Not all errors trigger the circuit breaker. The error classifier determines which errors count as failures:

| Error Type | Circuit Breaker Impact | Retry? |
|---|---|---|
| HTTP 5xx | Counts as failure | Yes (up to 2 attempts) |
| HTTP 429 (rate limit) | Does NOT count as failure | No — treat as rate limit, not failure |
| HTTP 4xx (except 429) | Does NOT count as failure | No — decline is not a gateway failure |
| Network timeout | Counts as failure | Yes (up to 2 attempts) |
| Context cancelled | Does NOT count as failure | No |

HTTP 429 was incorrectly classified as a transient error before INC-76. Stripe rate limiting a request is not a gateway failure — it means we are sending too many requests, which retrying only makes worse.

## Observability

Key metrics to monitor during a gateway incident:

- `circuit_breaker_state{gateway="stripe"}` — 0=closed, 1=half-open, 2=open
- `gateway_requests_total{gateway,status}` — request volume and success/failure breakdown by gateway
- `gateway_latency_seconds{gateway,quantile}` — per-gateway latency percentiles
- `stripe_429_rate` — rate of HTTP 429 responses from Stripe (key indicator of rate limit pressure)
- `gateway_failover_total` — counter of times traffic was routed to the fallback gateway

Dashboards: [Gateway Health](https://grafana.example.com/d/payments-gateway) | [Circuit Breaker State](https://grafana.example.com/d/circuit-breaker)

## Known Limitations

- **PayPal capacity**: PayPal is tested to handle 100% of traffic at sustained load. During INC-76, PayPal absorbed the burst successfully, but if both gateways are degraded simultaneously, there is no tertiary fallback.
- **Capture/void continuity**: If an authorization was created on Stripe but the circuit opens before capture, the capture must still go to Stripe (using the `gateway_ref` from the authorization). Captures cannot be moved to PayPal mid-lifecycle.
- **Idempotency key scope**: Idempotency keys are scoped per gateway. The same idempotency key submitted to both Stripe and PayPal will create two separate transactions — this does not happen in normal operation but is a known edge case if the gateway selection logic has a bug.
