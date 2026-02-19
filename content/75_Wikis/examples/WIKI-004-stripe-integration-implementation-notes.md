---
id: WIKI-004
type: wiki
title: Stripe Integration - Implementation Notes
status: accepted
owner: Payment Team
created: '2025-04-29T06:30:19.970Z'
updated: '2025-06-02T13:27:02.559Z'
tags:
  - wiki
  - payment-processing
summary: Stripe Integration - Implementation Notes
source_repo: https://git.example.com/acme/stripe-integration
commit_sha: 9d3a576d920ad5b0db816f7a5bc9fead191726c9
generated_at: '2026-09-20T09:45:00.060Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: gpt-4
importance: low
example: true
---

## Overview

This page captures implementation decisions and gotchas for the Stripe integration in `internal/gateway/stripe/adapter.go`. It is intended as a reference for engineers working on the gateway layer, supplementing the official Stripe documentation with platform-specific context.

The integration uses `stripe-go` SDK v76, implementing the `PaymentGateway` interface with PaymentIntents (not the legacy Charges API).

## Architecture

The adapter translates between the platform's internal `PaymentGateway` interface and Stripe's PaymentIntents API:

- `Authorize` maps to `paymentintent.New` with `capture_method: manual`
- `Capture` maps to `paymentintent.Capture` with an explicit amount
- `Refund` maps to `refund.New` referencing the PaymentIntent's charge ID
- `Void` maps to `paymentintent.Cancel`

## Key Components

- **Idempotency keys**: All Stripe API calls include a `stripe.IdempotencyKey` set to the platform payment ID concatenated with the operation type (e.g., `pay_abc123:authorize`). This ensures that even if our service retries, Stripe will not double-charge.
- **Error translation**: Stripe `stripe.Error` types are mapped to platform error codes in `errors.go`. `card_error` subtype codes (e.g., `card_declined`, `insufficient_funds`) map to specific platform codes.
- **Amount handling**: Stripe works in minor currency units (cents). The `Money` value object's `ToStripeAmount()` method handles conversion. Currency strings are passed as lowercase ISO 4217 codes.
- **Webhook verification**: Inbound Stripe webhooks are verified using `webhook.ConstructEvent` with the signing secret. Webhooks are consumed by the Payment Webhook Dispatcher, not directly by this service.

## Configuration

| Variable | Description |
|----------|-------------|
| `STRIPE_SECRET_KEY` | `sk_live_...` for production, `sk_test_...` for test/staging |
| `STRIPE_WEBHOOK_SECRET` | Signing secret for webhook verification |
| `STRIPE_API_VERSION` | Pinned to `2024-12-18.acacia` via SDK initialization |

## Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| `github.com/stripe/stripe-go/v76` | v76.12.0 | Stripe API SDK |
| `github.com/sony/gobreaker/v2` | v2.0.0 | Circuit breaker wrapping Stripe calls |
