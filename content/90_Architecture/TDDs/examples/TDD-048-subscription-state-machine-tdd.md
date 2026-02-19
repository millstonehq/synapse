---
id: TDD-048
type: tdd
title: Subscription State Machine TDD
status: draft
owner: Tech Lead
created: '2024-08-14T06:13:51.570Z'
updated: '2025-09-27T05:28:17.449Z'
tags:
  - tdd
  - billing-engine
summary: Subscription State Machine TDD
related_adrs:
  - ADR-0039
  - ADR-0038
example: true
---

## Summary

This TDD describes the formal design of the subscription state machine implemented in the Subscription Management Service. The state machine is the authoritative source of truth for subscription lifecycle in the Billing Engine and governs all state transitions, their preconditions, side effects, and the events emitted to downstream consumers. The design follows [[ADR-0039|ADR-0039]] (usage-based pricing model) and [[ADR-0038|ADR-0038]] (Stripe Billing as payment backend) — Stripe Billing subscription objects are kept in sync as a consequence of state transitions, not as the driver of them.

The state machine must enforce that all transitions are valid, that side effects (Stripe sync, event publish, proration trigger) are executed transactionally, and that concurrent transition requests for the same subscription are serialized safely.

## Overview

- **Source of truth**: The internal state machine is authoritative; Stripe subscription state is derived from internal events, not the inverse
- **Enumerated states**: `trialing`, `active`, `past_due`, `unpaid`, `paused`, `cancelled` — all transitions are explicitly enumerated; no implicit state changes
- **Serialization**: Transitions use a distributed lock (`redis-lock:subscription:{id}`) with a 5-second TTL to prevent concurrent transition races
- **Side effect ordering**: Database state update → Stripe sync → event publish (if Stripe sync fails, the transaction rolls back; if event publish fails, it is retried via dead letter queue)

## Architecture

- **SubscriptionStateMachine**: Core domain object implementing `Transition(event)` with guard conditions and side-effect registration per transition
- **StripeSubscriptionAdapter**: Translates internal state change events to Stripe API calls (`pause_collection`, `cancel_at_period_end`, `resume`, etc.)
- **SubscriptionEventPublisher**: Publishes `subscription.state_changed` events to RabbitMQ for downstream consumers (invoice pipeline, notifications, analytics)
- **RenewalScheduler**: Periodic job that identifies subscriptions where `current_period_end` has elapsed and triggers the `renewal_due` event to start the next billing period

## Information Model

- **Subscription**: `id`, `customer_id`, `plan_id`, `state`, `trial_start`, `trial_end`, `current_period_start`, `current_period_end`, `stripe_subscription_id`, `cancelled_at`, `created_at`, `updated_at`
- **SubscriptionStateEvent**: `id`, `subscription_id`, `from_state`, `to_state`, `trigger_event`, `actor`, `metadata`, `created_at` (immutable audit log)
- **SubscriptionTransition**: `allowed_from_states: []`, `to_state`, `guard_fn`, `side_effects: []` (compile-time configuration, not stored)

## Interfaces

- `POST /v1/subscriptions` - Create a new subscription (begins in `trialing` or `active`)
- `POST /v1/subscriptions/{id}/cancel` - Trigger `cancel_requested` event
- `POST /v1/subscriptions/{id}/pause` - Trigger `pause_requested` event (requires `active` state)
- `POST /v1/subscriptions/{id}/resume` - Trigger `resume_requested` event (requires `paused` state)
- `GET /v1/subscriptions/{id}/history` - Return the full state event history for a subscription

## Files and Layout

```
subscription-management-service/
  internal/subscription/
    state_machine.go         - Transition table, guard conditions, side effects
    transitions.go           - All allowed transition definitions
    stripe_adapter.go        - Stripe sync side effect implementation
    event_publisher.go       - RabbitMQ event publish side effect
    renewal_scheduler.go     - Period-end renewal trigger
  internal/model/
    subscription.go          - Subscription entity
    state_event.go           - SubscriptionStateEvent audit record
  migrations/
    0031_subscriptions.sql
    0032_subscription_state_events.sql
```

## Work Plan

1. **Phase 1 - State machine core (Week 1-2)**: Define all states, events, and transition table; implement guard conditions; write exhaustive unit tests for all valid and invalid transitions
2. **Phase 2 - Persistence and locking (Week 3)**: Implement repository with `SELECT FOR UPDATE`; implement Redis distributed lock for concurrent transition protection; test lock contention under load
3. **Phase 3 - Stripe sync (Week 4)**: Implement Stripe adapter for each state change; test against Stripe test mode; handle Stripe API errors with rollback
4. **Phase 4 - Event publishing (Week 5)**: Implement RabbitMQ event publisher; implement dead letter queue retry for failed publishes; integration test full transition flow end-to-end
5. **Phase 5 - Renewal scheduler (Week 6)**: Implement period-end detection and renewal trigger; test edge cases (trial expiry, pause during trial, immediate cancellation)

## Risks and Mitigations

- **Stripe sync divergence**: If Stripe sync fails after the database update, the internal state and Stripe state diverge; mitigate by implementing a reconciliation job that compares internal state against Stripe state daily and alerts on discrepancy
- **Concurrent transition deadlock**: Two simultaneous transition requests could deadlock on the subscription row; mitigate by using a Redis lock (non-blocking, with immediate 409 on contention) rather than database row locks
- **Renewal scheduler missing subscriptions at scale**: As subscription count grows, the scheduler must page through large result sets; mitigate by using cursor-based pagination and a per-partition scan with dedicated worker shards
