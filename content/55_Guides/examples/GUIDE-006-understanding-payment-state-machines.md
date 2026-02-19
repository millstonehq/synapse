---
id: GUIDE-006
type: guide
title: Understanding Payment State Machines
status: draft
owner: Engineering Team
created: '2025-07-27T21:03:43.346Z'
updated: '2025-04-15T22:32:26.134Z'
tags:
  - guide
  - payment-processing
summary: Understanding Payment State Machines
audience: internal
related_systems:
  - SYSTEM-001
  - SYSTEM-003
related_sops:
  - SOP-010
  - SOP-007
example: true
---

## Overview

Every payment in the platform has a lifecycle represented as a finite state machine. Understanding valid states and transitions is essential for debugging stuck transactions, implementing idempotent retry logic, and building correct fulfillment integrations that react to the right payment events.

The primary state machine governs `PaymentIntent` objects. Separate but related state machines govern `Refund` and `Dispute` objects.

## PaymentIntent State Machine

A `PaymentIntent` progresses through the following states:

- **`created`** — The intent has been initialized but no payment method has been attached. This is the starting state after `POST /v1/payment-intents`.
- **`requires_payment_method`** — The intent requires a payment method to be confirmed before authorization can proceed.
- **`requires_action`** — The authorization requires the customer to complete an additional step, typically 3D Secure authentication.
- **`processing`** — The authorization request has been submitted to the gateway and the platform is awaiting a response.
- **`succeeded`** — The payment has been authorized and captured. This is a terminal success state.
- **`failed`** — The payment was declined or an unrecoverable error occurred. This is a terminal failure state.
- **`canceled`** — The intent was explicitly canceled before capture. The authorization hold (if any) will be voided.

Valid transitions: `created` → `requires_payment_method` → `requires_action` (optional) → `processing` → `succeeded` or `failed`. Cancellation is allowed from any non-terminal state.

## Why State Transitions Matter

Attempting an operation in the wrong state returns a `422 Unprocessable Entity` with error code `invalid_state_transition`. This is intentional: the state machine prevents double-captures, refunds on failed payments, and other inconsistent operations.

When building a fulfillment system, only trigger fulfillment on `payment_intent.succeeded` webhook events. Do not trigger fulfillment on `processing` state — the gateway response is not yet confirmed and the payment can still fail.

## Debugging Stuck Transactions

A transaction in `processing` state for longer than 60 seconds indicates a gateway response was not received or was not processed. The platform's timeout job runs every 2 minutes and transitions `processing` payments to `failed` with error code `gateway_timeout` if no response is received.

If you observe a payment stuck in `processing` beyond 10 minutes (after the timeout job has run), this indicates a state machine bug. Follow the Investigate Stuck Transaction SOP and escalate to the payments on-call engineer.

## Refund and Dispute State Machines

Refunds have their own states: `pending` → `processing` → `succeeded` or `failed`. Disputes progress from `needs_response` → `under_review` → `won` or `lost`. Both are separate objects linked to the original `PaymentIntent` by the `payment_intent_id` field.
