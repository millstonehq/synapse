---
id: PRD-002
type: prd
title: Multi-Currency Checkout PRD
status: approved
owner: Product Manager
created: '2025-10-30T18:59:03.555Z'
updated: '2026-08-09T01:09:09.952Z'
tags:
  - prd
  - payment-processing
summary: Multi-Currency Checkout PRD
related_tdds:
  - TDD-004
  - TDD-001
example: true
related_standards:
  - STANDARD-001
---

## Summary

Enable customers to pay in their local currency at checkout. The platform currently only accepts USD, which forces international customers to pay foreign transaction fees and see unfamiliar amounts. Multi-currency checkout will increase conversion rates for non-US customers and expand our addressable market to 30 additional currencies. The feature requires changes to the checkout UI (currency selector), the Payments API (currency field on authorization), and the reconciliation reports (settlement in USD). Related TDDs: [[TDD-004|Multi-Currency Support TDD]] and [[TDD-001|Payment Gateway Abstraction Layer TDD]].

## Goals

- Enable checkout in 30 currencies, expanding addressable market to customers in the EU, UK, Canada, Australia, and Asia-Pacific
- Increase checkout conversion rate for non-US customers by reducing currency confusion and foreign transaction fees
- Store settlement amounts in USD for consistent financial reporting across all transactions
- Provide accurate FX rate display at checkout so customers know the USD equivalent before confirming

## In Scope

- Currency selector on checkout page (30 supported ISO 4217 currencies)
- FX rate display at checkout: "€150 EUR = ~$162 USD at today's rate"
- Payments API `currency` field support on authorize endpoint
- Settlement amount storage (USD equivalent at authorization time)
- Updated transaction history showing original currency and settlement amount
- Reconciliation reports updated to include per-currency breakdown

## Out of Scope

- Dynamic currency conversion (DCC) — charging in USD regardless of displayed currency
- Cryptocurrency payments
- Currency management for refunds that exceed settlement (negative FX delta handling — v2)
- Automatic currency detection from browser locale (defaults to USD; customer selects)

## Users and Flows

**International customers**: Select their local currency from a dropdown at checkout. See the total amount in their currency with an FX rate disclosure. After completing payment, transaction history shows both their currency and the USD settlement amount.

**Finance team**: Reconciliation reports now include an additional currency column. All revenue reporting remains in USD using settlement amounts.

**Operations staff**: Transaction search and detail views show the original currency and FX rate applied.

## Requirements

- Accept `currency` field (ISO 4217 3-letter code) on the authorize endpoint; default to USD if omitted
- Validate currency against the supported currency allowlist; return 422 for unsupported currencies
- Display current FX rate on checkout for non-USD currencies, refreshed every 5 minutes
- Store `settlement_amount` (USD) and `fx_rate` on payment record at authorization time
- Process and store amounts in minor units for zero-decimal currencies (JPY, KRW)
- Refund in the original transaction currency

## KPIs

- **Conversion rate uplift**: 8% increase in checkout completion rate for non-US IP addresses within 60 days of launch
- **International GMV**: 15% of total GMV from non-USD transactions within 90 days
- **FX accuracy**: Displayed FX rate within 1% of actual settlement rate in 99% of transactions
- **Availability**: Multi-currency checkout adds < 100ms to P95 authorize latency (FX rate served from cache)

## Information Architecture

- Technical design: [[TDD-004|Multi-Currency Support TDD]]
- Gateway abstraction impacts: [[TDD-001|Payment Gateway Abstraction Layer TDD]]
- Financial reporting impacts: documented in reconciliation runbook

## Data Model

New fields on existing `payments` table:
- `currency` (char(3), not null, default 'USD')
- `settlement_amount` (int8, nullable) — USD minor units
- `settlement_currency` (char(3), default 'USD')
- `fx_rate` (numeric(18,8), nullable) — rate applied at authorization

No new tables; FX rates cached in Redis only (not persisted to DB).

## Non-Functional

- FX rate must be displayed within 500ms of currency selection
- Payment processing latency increase must be < 100ms at P95 (FX rate served from Redis cache)
- FX rate disclosure must comply with Stripe's currency presentation guidelines
- No change to PCI scope — currency selection does not involve card data

## Constraints

- FX rate provider: Fixer.io API; 5-minute cache acceptable
- Must not break existing USD-only checkout for US customers
- Finance team must validate reconciliation report changes before full rollout
- Budget: 2 engineers for 8 weeks

## Risks

- **FX rate provider outage** blocks non-USD checkout. Mitigation: serve stale cache for up to 30 minutes with disclosure; fall back to USD-only checkout if cache expired.
- **Customer confusion about FX rates** leads to disputes. Mitigation: clear disclosure at checkout and in transaction history showing the rate applied.
- **Zero-decimal currency bugs** cause amount errors. Mitigation: integration test suite covering JPY, KRW, and other zero-decimal currencies in Stripe sandbox.

## Milestones

### M1: Backend Currency Support (Week 1-4)

#### Deliverables

- Payments API currency field, FX rate cache, settlement amount storage
- Currency allowlist validation
- Reconciliation report updated for multi-currency

#### Acceptance Criteria

- Can authorize a EUR payment in staging; settlement amount stored in USD
- JPY test payment stores correct minor-unit amount (no decimal)
- Finance team sign-off on updated reconciliation report

### M2: Checkout UI (Week 5-7)

#### Deliverables

- Currency selector on checkout page
- FX rate display with 5-minute refresh
- Transaction history shows original currency and FX rate

#### Acceptance Criteria

- Currency selector shows 30 currencies with correct formatting
- FX rate displayed within 500ms of currency selection
- UAT sign-off from product and finance

### M3: Launch (Week 8)

#### Deliverables

- 10% canary to non-US customers, monitoring conversion rate and FX accuracy
- Full rollout on finance sign-off

#### Acceptance Criteria

- No increase in payment failure rate during canary
- P95 authorize latency increase < 100ms
- FX rate accuracy > 99% within 1% of settlement rate
