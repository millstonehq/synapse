---
id: PRD-001
type: prd
title: Instant Payment Confirmation PRD
status: deprecated
owner: Head of Product
created: '2025-12-01T13:56:13.795Z'
updated: '2026-02-06T08:36:33.496Z'
tags:
  - prd
  - payment-processing
summary: Instant Payment Confirmation PRD
related_tdds:
  - TDD-003
  - TDD-005
example: true
related_standards:
  - STANDARD-004
---

## Summary

Deliver instant payment confirmation to customers at checkout. Currently, customers see a loading spinner for 3-5 seconds while the payment processes, then receive a confirmation email 30-60 seconds later. This creates uncertainty and drives support tickets ("did my payment go through?"). The feature reduces the perceived checkout time to under 1 second and delivers confirmation within 5 seconds of order placement. This PRD covers the full-stack changes required: optimistic UI confirmation, real-time push notification infrastructure, and backend webhook processing improvements. Related TDDs: [[TDD-003|Payment Webhook Processing Pipeline TDD]] and [[TDD-005|Payment Analytics Dashboard TDD]].

## Goals

- Reduce customer support tickets about payment confirmation by 40%
- Deliver payment confirmation email within 5 seconds of successful authorization (down from 30-60 seconds)
- Show optimistic confirmation UI to customers within 1 second of clicking "Place Order"
- Reduce checkout abandonment rate by providing immediate status feedback on failures

## In Scope

- Optimistic UI confirmation after order placement (show success immediately, revert on failure)
- Real-time WebSocket push for final payment status from the Payments API
- Sub-5-second confirmation email delivery via improved webhook-to-notification pipeline
- Improved payment failure messages with actionable guidance

## Out of Scope

- Redesign of the checkout UI beyond the confirmation step
- SMS/push notification channels (handled by Notification Service separately)
- Refund confirmation improvements (separate initiative)
- Changes to authorization hold duration (currently 24 hours)

## Users and Flows

**Customers**: Complete checkout and immediately see confirmation. If payment fails, they see an actionable error message within 2 seconds rather than a timeout.

**Operations staff**: No change to existing workflows. Benefit from reduced "did my payment go through?" support tickets.

**Email systems**: Confirmation emails are now triggered by the Payments API webhook pipeline rather than a polling job.

## Requirements

- Display an optimistic order confirmation screen within 1 second of "Place Order" click for 95% of successful payments
- Push real-time payment status update via WebSocket within 3 seconds of gateway response
- Send confirmation email within 5 seconds of authorization for 95th percentile
- If authorization fails, display a specific error message (declined, insufficient funds, processing error) within 2 seconds
- Revert optimistic confirmation and show failure state if payment fails after optimistic display
- Log all confirmation delivery times for SLA tracking

## KPIs

- **Confirmation delivery**: P95 email delivery < 5s (from current ~45s baseline)
- **Optimistic confirmation accuracy**: < 0.5% of optimistic confirmations subsequently reverted due to payment failure
- **Support ticket reduction**: 40% reduction in "payment confirmation" support tickets within 30 days of launch
- **Checkout abandonment**: 5% reduction in abandonment rate on the confirmation step

## Information Architecture

- This PRD defines the product requirements
- Technical implementation design in [[TDD-003|Payment Webhook Processing Pipeline TDD]] and [[TDD-005|Payment Analytics Dashboard TDD]]
- Existing runbooks cover payment failure recovery and do not need updating

## Data Model

No new entities. Changes to existing entities:
- `payments` table: new `confirmation_sent_at` timestamp column (nullable) to track when confirmation was dispatched
- `webhook_events` table: existing table tracks processing latency for SLA reporting

## Non-Functional

- Optimistic UI must not cause PCI scope issues: no card data is displayed or stored in the optimistic state
- WebSocket connection must be authenticated (JWT)
- Confirmation email latency SLA must be measurable from existing webhook processing metrics

## Constraints

- WebSocket infrastructure must use existing API gateway — no new WebSocket-specific infrastructure
- Confirmation email content and template are owned by the CX team; this PRD does not change email content, only delivery speed
- Budget: 1 engineer for 6 weeks

## Risks

- **Optimistic confirmation reversion** confuses customers if payment fails after the confirmation screen appears. Mitigation: reversion rate target of < 0.5%; clear failure messaging if reversion occurs; no optimistic confirmation for card types with high decline rates.
- **WebSocket connection drops** could miss the final status push. Mitigation: client polls as fallback every 3 seconds for 30 seconds if no WebSocket update is received.
- **Email provider latency** outside our control. Mitigation: measure and report external email provider latency separately from internal pipeline latency.

## Milestones

### M1: Backend Pipeline (Week 1-3)

#### Deliverables

- Webhook processing pipeline latency improved to < 2s median (from current ~30s)
- `confirmation_sent_at` column and tracking instrumentation
- Email triggered directly by webhook pipeline, not polling job

#### Acceptance Criteria

- P95 email delivery < 5s in staging environment with simulated Stripe webhooks
- Confirmation latency metrics visible in analytics dashboard

### M2: Real-Time Push (Week 4-5)

#### Deliverables

- WebSocket endpoint publishing payment status updates
- Client-side WebSocket integration in checkout flow
- Optimistic confirmation UI with revert capability

#### Acceptance Criteria

- P95 real-time status update delivered within 3 seconds in staging
- Reversion path tested with simulated payment failure after optimistic display

### M3: Production Launch (Week 6)

#### Deliverables

- 10% canary rollout, measuring confirmation latency and reversion rate
- Full rollout if reversion rate < 0.5% and confirmation P95 < 5s

#### Acceptance Criteria

- P95 confirmation email < 5s in production
- No increase in checkout abandonment rate during canary
- Support ticket monitoring shows downward trend within 2 weeks
