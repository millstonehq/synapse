---
id: PRD-005
type: prd
title: One-Click Payment PRD
status: accepted
owner: Senior PM
created: '2024-11-14T12:43:55.534Z'
updated: '2026-10-02T17:20:24.120Z'
tags:
  - prd
  - payment-processing
summary: One-Click Payment PRD
related_tdds:
  - TDD-002
  - TDD-004
example: true
related_standards:
  - STANDARD-003
---

## Summary

Reduce checkout friction for returning customers by enabling one-click payment using their stored default payment method. Currently, all customers must confirm their payment method on every purchase. One-click checkout skips the payment form for customers who have a verified default payment method on file, reducing checkout to a single confirmation click. Related TDDs: [[TDD-002|Transaction Retry Engine TDD]] and [[TDD-004|Multi-Currency Support TDD]].

## Goals

- Reduce checkout completion time for returning customers from ~45 seconds to < 10 seconds
- Increase repeat purchase conversion rate by 12% among customers with saved payment methods
- Maintain fraud and chargeback rates at current levels (no increase from streamlined flow)
- Reduce checkout abandonment by 8% for customers with stored payment methods

## In Scope

- One-click payment flow for customers with a verified default payment method
- "Pay Now" button on product pages and cart (skips checkout form)
- Order review modal before payment: shows default card last four, total, and shipping address
- Opt-in control: customers can disable one-click checkout from account settings
- Fraud velocity checks: one-click purchases subject to the same fraud scoring as regular checkout

## Out of Scope

- Guest checkout acceleration (one-click requires a stored payment method)
- One-click for non-card payment methods (bank transfers, PayPal balance — v2)
- Physical device integration (NFC tap-to-pay — separate initiative)
- One-click for subscriptions (handled by subscription billing platform)

## Users and Flows

**Returning customers with saved payment method**: See a "Pay Now" button. Clicking it opens a 5-second confirmation modal showing the order summary and default card. Confirming submits payment immediately. No card entry required.

**New customers or customers without saved cards**: Standard checkout flow unchanged. One-click is invisible to these users.

**Customers who opt out**: Standard checkout flow restored. Setting persisted in customer account preferences.

## Requirements

- Display "Pay Now" button only to authenticated customers with a verified default payment method
- Show a confirmation modal with: order total, default card last four, estimated delivery date, and a 5-second auto-dismiss countdown
- Submit payment using the default stored payment method via the existing Payments API
- Apply the same fraud velocity rules as standard checkout (no bypass)
- Allow customers to switch to the standard checkout flow from the one-click confirmation modal
- Record `checkout_type: one_click` on payment records for analytics

## KPIs

- **Conversion uplift**: 12% increase in repeat purchase completion rate for eligible customers
- **Checkout time**: Mean checkout completion time < 10 seconds for one-click flow (from 45-second baseline)
- **Fraud rate**: Chargeback rate among one-click transactions within 10% of standard checkout rate
- **Opt-out rate**: < 5% of eligible customers disable one-click within 30 days of launch

## Information Architecture

- This PRD defines one-click payment product requirements
- Technical design for stored payment method handling in [[TDD-002|Transaction Retry Engine TDD]]
- Multi-currency considerations for one-click in [[TDD-004|Multi-Currency Support TDD]]

## Data Model

New fields on existing `payment_methods` table:
- `is_default` (boolean, already exists)
- `one_click_eligible` (boolean, default false) — set to true after successful purchase without 3DS challenge

New field on `payments` table:
- `checkout_type` (enum: 'standard', 'one_click')

## Non-Functional

- One-click confirmation modal must load within 500ms
- Payment submission from one-click must complete within the same P95 SLA as standard checkout (< 2s)
- One-click flow must be compatible with strong customer authentication (SCA) requirements; if SCA challenge is required, fall back to standard checkout automatically
- Must not expose full card number at any point in the flow

## Constraints

- SCA fallback is mandatory for EU customers where card issuers require 3DS — one-click cannot bypass 3DS
- One-click is only available for saved card tokens; not for PayPal or bank transfer methods
- Budget: 2 engineers for 6 weeks

## Risks

- **SCA/3DS challenges** will force some one-click attempts to fall back to standard checkout, reducing the conversion uplift for EU customers. Mitigation: track SCA fallback rate by region; set realistic conversion targets for EU separately.
- **Accidental purchases** from customers who click "Pay Now" without reading the modal. Mitigation: 5-second auto-dismiss countdown with prominent cancel button; full refund policy for accidental one-click purchases.
- **Fraud velocity increase** if one-click reduces friction for fraudsters with stolen cards. Mitigation: enhanced fraud velocity check for one-click orders; flag accounts with multiple one-click orders in a short window.

## Milestones

### M1: Backend One-Click API (Week 1-3)

#### Deliverables

- `one_click_eligible` flag on payment methods
- `checkout_type` field on payment records
- One-click authorize endpoint (same as standard, different eligibility check)
- Fraud velocity check integration

#### Acceptance Criteria

- One-click payment processes correctly for eligible payment methods in staging
- Ineligible customers (no saved card, 3DS required) receive appropriate error

### M2: UI Implementation (Week 4-5)

#### Deliverables

- "Pay Now" button on product pages for eligible customers
- Confirmation modal with countdown and fallback to standard checkout
- Opt-out setting in account preferences

#### Acceptance Criteria

- One-click flow completes in < 10 seconds end-to-end in user testing
- Standard checkout flow unchanged for ineligible customers
- Opt-out correctly persists and suppresses the button

### M3: Launch (Week 6)

#### Deliverables

- 10% A/B test: eligible customers randomly split between one-click and standard checkout
- Monitor conversion rate, fraud rate, and opt-out rate for 2 weeks

#### Acceptance Criteria

- Statistically significant conversion uplift in A/B test (p < 0.05)
- Fraud rate within 10% of control group
- Full rollout to all eligible customers
