---
id: REFERENCE-020
type: reference
title: Stripe Billing API Reference
status: published
owner: Platform Team
created: '2025-12-17T21:32:44.434Z'
updated: '2026-05-16T12:33:20.805Z'
tags:
  - reference
  - billing-engine
summary: Stripe Billing API Reference
upstream_url: https://docs.example.com/stripe-billing-api-reference
last_synced: '2025-09-09T19:59:15.421Z'
attribution: IETF
license: CC BY-SA 4.0
category: tutorial
example: true
---

## Overview

The Stripe Billing API is the primary payment backend for the Billing Engine, as documented in ADR-0038. This reference summarizes the key Stripe Billing API objects and endpoints used by the Billing Engine, with notes on how each is used in our specific integration pattern. It is not a substitute for the Stripe official documentation; refer to `docs.stripe.com` for the authoritative API reference.

Our integration uses the Stripe Python SDK (stripe-python v7.x). All API calls are made from the Billing Engine's server-side components; no Stripe API keys are exposed to client-side code.

## Core Objects

### Customer

The Stripe Customer object (`cus_*`) represents a billing entity. Each of our accounts corresponds to one Stripe Customer.

**How we use it**: The Subscription Management Service creates a Stripe Customer when a new account activates. The Stripe Customer ID is stored on our internal `accounts` table and is the foreign key used in all Stripe API calls for that account. We do not use Stripe Customer as the source of truth for account data — our internal account record is canonical.

**Key fields we use**: `id`, `email`, `default_source`, `metadata` (stores our internal account_id for cross-reference)

### PaymentMethod and PaymentIntent

PaymentMethod (`pm_*`) represents a tokenized payment instrument. We use Stripe Elements (client-side) to collect and tokenize card details; the resulting `pm_*` token is attached to the Stripe Customer server-side. We never handle raw card data.

**How we use it**: When a customer adds a payment method via the Self-Service Billing Portal, the portal frontend uses Stripe Elements to create a `pm_*` token, which it sends to our backend. Our backend calls `stripe.PaymentMethods.attach()` to associate it with the Customer and `stripe.Customers.modify(invoice_settings.default_payment_method=pm_id)` to set it as the default.

### Subscription

The Stripe Subscription (`sub_*`) represents a recurring billing agreement. Our internal Subscription Management Service is the source of truth for subscription state; the Stripe Subscription is a downstream reflection of our internal state.

**How we use it**: We create and cancel Stripe Subscriptions in sync with our internal subscription state machine transitions. We do not use Stripe Subscription webhooks to drive our internal state — we push state changes to Stripe, not the reverse. The Stripe Subscription is used for recurring charge execution only.

**Key fields we use**: `id`, `status`, `current_period_start`, `current_period_end`, `items` (maps to our plan line items), `default_payment_method`

### Invoice and InvoiceItem

The Stripe Invoice (`in_*`) represents a charge document. Stripe creates invoices automatically for subscription renewals; we also create invoices manually for one-off charges and proration adjustments.

**How we use it**: For each billing period, after our internal Invoice Generation Pipeline assembles and finalizes the invoice, we call `stripe.Invoices.create()` with our line items and immediately finalize it with `stripe.Invoices.finalize_invoice()`. The resulting Stripe Invoice ID is stored on our internal invoice record for reconciliation.

## Key Webhook Events

The Billing Webhook Processor handles the following Stripe webhook event types:

- `invoice.payment_succeeded` — charge was collected; triggers revenue recognition ledger entries
- `invoice.payment_failed` — charge failed; triggers dunning workflow
- `customer.subscription.deleted` — subscription cancelled in Stripe; used for reconciliation only (we own cancellations)
- `charge.refunded` — refund confirmed by Stripe; triggers refund ledger entries
- `payment_method.detached` — payment method removed; update internal record

## Rate Limits and Error Handling

Stripe enforces rate limits per API key. In live mode, the default limit is 100 read requests/second and 100 write requests/second. Month-end invoice generation can approach these limits.

- Month-end burst mitigation: billing runs are distributed across a 4-hour window (not all at midnight)
- Idempotency keys: all Stripe API calls that create objects use idempotency keys (`Idempotency-Key` header) to prevent duplicates on retry
- Retry policy: transient errors (429 rate limit, 500/502/503 server errors) are retried with exponential backoff; 3 retries max
- Circuit breaker: if Stripe error rate exceeds 20% in a 60-second window, the Billing Engine stops processing new invoice runs and alerts on-call

## Sync Notes

This reference reflects the Stripe Billing API as of the Stripe API version pinned in the Billing Engine (`stripe-python` SDK v7.x, API version `2024-04-10`). Review and update when the Stripe SDK or API version is upgraded. The Stripe changelog is at `stripe.com/docs/upgrades`.
