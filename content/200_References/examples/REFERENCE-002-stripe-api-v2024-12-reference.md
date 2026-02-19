---
id: REFERENCE-002
type: reference
title: Stripe API v2024-12 Reference
status: draft
owner: Platform Team
created: '2025-07-23T14:47:51.280Z'
updated: '2026-08-02T19:49:19.903Z'
tags:
  - reference
  - payment-processing
summary: Stripe API v2024-12 Reference
upstream_url: https://docs.example.com/stripe-api-v2024-12-reference
last_synced: '2026-01-17T00:53:17.624Z'
attribution: ISO
license: CC BY-SA 4.0
category: other
example: true
---

## Overview

The Stripe API version `2024-12-18.acacia` (referred to as `2024-12` in our configuration) is the API version pinned in the `stripe-go` SDK v76 used by the Payments API. This reference documents the key API behaviors, breaking changes from the previous pinned version (`2023-10-16`), and Stripe-specific behaviors that affect our implementation.

Our implementation uses Stripe's API version pinned in the `stripe-go` SDK header. Stripe's versioning policy means API responses are shaped according to the version set in the SDK, not the account's default version. We upgrade SDK versions (and thus API versions) as part of our quarterly dependency update cycle.

## PaymentIntents API (Our Primary Integration)

The PaymentIntents API is the primary Stripe integration point for the Payments API. All authorization, capture, and refund operations go through PaymentIntents.

### Create PaymentIntent (Authorization)

- **Endpoint**: `POST /v1/payment_intents`
- **Key fields we set**: `amount` (minor units), `currency` (ISO 4217), `payment_method` (stored token), `confirm: true`, `capture_method: manual` (authorize-only), `idempotency_key` (via `Idempotency-Key` header)
- **Status after success**: `requires_capture`
- **Important behavior**: Setting `capture_method: manual` creates an authorization hold without capturing. The hold expires after 7 days for most cards (some card brands allow up to 30 days).

### Capture PaymentIntent

- **Endpoint**: `POST /v1/payment_intents/{id}/capture`
- **Key fields**: `amount_to_capture` (optional; defaults to the full authorized amount)
- **Idempotent**: Yes — the same capture request with the same idempotency key returns the same result
- **Status after success**: `succeeded`

### Refund

- **Endpoint**: `POST /v1/refunds`
- **Key fields**: `payment_intent` (our reference), `amount` (partial refund amount in minor units; omit for full refund)
- **Status**: `succeeded` (synchronous for most cards) or `pending` (some ACH / bank transfers)

### PaymentIntent States (2024-12 version)

- `requires_payment_method` → `requires_confirmation` → `requires_action` → `processing` → `requires_capture` → `succeeded`
- Terminal failure states: `canceled`, `payment_failed`

## Idempotency Keys

Stripe accepts an `Idempotency-Key` header on any POST request. Stripe stores the result for 24 hours and returns the identical response for any subsequent request with the same key.

**Our implementation**: We generate a UUID v4 idempotency key per operation and store it on the `payments` record. On retry, the same key is forwarded. Stripe's 24-hour window is shorter than our 7-day Redis TTL — if a retry occurs after 24 hours, Stripe processes it as a new request. This is acceptable because we use `SELECT FOR UPDATE` to prevent duplicate state transitions on our side.

## Webhook Events We Process

| Event | Trigger | Our Handler |
|---|---|---|
| `payment_intent.succeeded` | Capture completed | Update payment to `captured` |
| `payment_intent.payment_failed` | Authorization declined | Update payment to `failed` |
| `charge.refunded` | Refund processed | Update payment to `refunded` |
| `charge.dispute.created` | Chargeback filed | Update payment to `disputed`, alert ops |
| `charge.dispute.won` | Dispute won | Update payment to `dispute_won` |
| `charge.dispute.lost` | Dispute lost | Update payment to `dispute_lost`, alert finance |

## Rate Limits

Stripe enforces rate limits per API key. In `2024-12`, the live mode limits are:

- Standard rate limit: 100 requests/second
- Read-only endpoints: 100 requests/second
- Write endpoints (PaymentIntents, Refunds): 100 requests/second
- `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers are returned on every response

**Our handling**: HTTP 429 responses are classified as non-retryable by the retry engine (see POSTMORTEM-005 for the root cause of the INC-76 incident). We parse `X-RateLimit-Remaining` to proactively back off when approaching the limit.

## Changes from 2023-10-16 to 2024-12

- `PaymentIntent.amount_details` field added to show breakdowns for tip and surcharge amounts (not used by us currently)
- `Charge.payment_method_details.card.network_token` field added for network tokenization tracking
- Deprecated `Charge.source` in favor of `PaymentMethod` — we already use PaymentMethod, no change required
- Webhook signatures now support SHA-256 (previously SHA-256 was optional; now recommended)

## Sync Notes

This reference covers the Stripe API `2024-12-18.acacia` version as used by `stripe-go` v76. Re-sync when upgrading the `stripe-go` SDK. Key changes to review: new PaymentIntent states, new webhook event types, and rate limit header changes.
