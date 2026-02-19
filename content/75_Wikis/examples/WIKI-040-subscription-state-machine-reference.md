---
id: WIKI-040
type: wiki
title: Subscription State Machine - Reference
status: approved
owner: Billing Team
created: '2025-04-26T07:20:26.211Z'
updated: '2026-11-17T16:10:28.394Z'
tags:
  - wiki
  - billing-engine
summary: Subscription State Machine - Reference
source_repo: https://git.example.com/acme/subscription-state-machine
commit_sha: 3fcd39e1b46ab3cc4c29c47f9dca3a69d3a99eb8
generated_at: '2026-12-01T00:31:54.406Z'
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
importance: low
example: true
---

## Overview

The Subscription State Machine defines all valid states a subscription can be in and the transitions between them. It is implemented in the Subscription Management Service and is the authoritative model for subscription lifecycle behavior across the Billing Engine. This reference documents all states, valid transitions, triggering events, and the side effects each transition produces.

This page was auto-generated from commit `3fcd39e` of the `subscription-state-machine` repository. For the original design, see TDD-048.

## States

| State | Description |
|-------|-------------|
| `trialing` | Subscription is in a free trial period. No billing occurs. Usage metering is active. |
| `active` | Subscription is in good standing. Billing is active; invoices are generated at period close. |
| `past_due` | A renewal invoice was generated but payment has not been received within the grace period. |
| `unpaid` | Payment has not been received after the full dunning sequence. Service access may be restricted. |
| `cancelled` | Subscription has been terminated. Final invoice issued if balance exists. No further billing. |
| `paused` | Billing is suspended at customer request. Usage metering continues. Resumes on specified date. |

## State Transitions

### `trialing` → `active`
- **Trigger**: Trial period end date reached, or customer manually converts
- **Actions**: Schedule first billing period; publish `subscription.activated` event

### `active` → `past_due`
- **Trigger**: Renewal invoice payment fails (Stripe webhook: `invoice.payment_failed`)
- **Actions**: Begin dunning sequence; publish `subscription.past_due` event; notify customer

### `past_due` → `active`
- **Trigger**: Payment received during grace period (Stripe webhook: `invoice.payment_succeeded`)
- **Actions**: Cancel dunning sequence; publish `subscription.reactivated` event

### `past_due` → `unpaid`
- **Trigger**: Grace period expires (default: 14 days) without payment
- **Actions**: Restrict service access per tenant configuration; publish `subscription.unpaid` event

### `unpaid` → `cancelled`
- **Trigger**: Maximum dunning attempts exhausted (configurable, default: 3)
- **Actions**: Finalize and issue terminal invoice; publish `subscription.cancelled` event

### `active` → `cancelled`
- **Trigger**: Customer-initiated cancellation request
- **Actions**: Set cancellation effective date (end of current period or immediate); publish `subscription.cancellation_scheduled` or `subscription.cancelled`

### `active` → `paused`
- **Trigger**: Customer-initiated pause request (requires feature flag: `subscription_pause_enabled`)
- **Actions**: Suspend billing period; publish `subscription.paused` event

### `paused` → `active`
- **Trigger**: Pause end date reached or customer resumes manually
- **Actions**: Resume billing period from pause date; publish `subscription.resumed` event

## Key Packages

### `statemachine/transitions`

Contains the transition table and guards. Each transition is defined as a `Transition` struct with `FromState`, `ToState`, `Event`, `Guard`, and `Actions` fields. Guards are pure functions with no side effects; all side effects are in Actions.

### `statemachine/events`

Defines the domain event types published on each transition. All events include `subscription_id`, `customer_id`, `from_state`, `to_state`, `timestamp`, and optional `metadata`.

## Generation Notes

Generated from commit `3fcd39e` on the `main` branch of the `subscription-state-machine` repository. Transition table is derived directly from the Go source code.
