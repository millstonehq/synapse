---
id: TDD-049
type: tdd
title: Proration Calculator TDD
status: approved
owner: Principal Engineer
created: '2024-07-23T07:48:04.236Z'
updated: '2025-10-10T16:32:41.098Z'
tags:
  - tdd
  - billing-engine
summary: Proration Calculator TDD
related_adrs:
  - ADR-0040
  - ADR-0038
example: true
---

## Summary

This TDD describes the design of the Proration Calculator — a pure computation module within the Billing Engine responsible for determining the credit and charge amounts when a subscription changes mid-billing-period. The calculator must produce exact cent-precision results that are compliant with the double-entry bookkeeping pattern described in [[ADR-0040|ADR-0040]] and are formatted as Stripe invoice line items compatible with [[ADR-0038|ADR-0038]].

Proration arises when a customer upgrades or downgrades a plan, adds or removes seats, or cancels mid-cycle. The calculator receives the plan change event and emits a set of ledger-ready credit and debit line items that the Invoice Pipeline incorporates into the next invoice.

## Overview

- **Day-accurate proration**: Proration is calculated at day granularity (not second granularity) — the number of days remaining in the current period divided by the total days in the period
- **No rounding accumulation**: All intermediate calculations use integer arithmetic in cents; rounding happens once at the final step
- **Symmetry**: An upgrade proration debit plus its corresponding cancel credit always sums to the full period price of the original plan — no value is created or destroyed
- **Ledger compatibility**: Every proration output includes a debit entry and a credit entry of equal absolute value, satisfying the double-entry invariant from [[ADR-0040|ADR-0040]]

## Architecture

- **ProrationCalculator**: Pure function — takes a `PlanChangeEvent` (old plan, new plan, effective date, period start/end) and returns a `ProrationResult` with credit and debit line items
- **PeriodDateMath**: Helper that computes day counts correctly across month boundaries, leap years, and period-end edge cases
- **ProrationLineItemFactory**: Converts raw credit/debit amounts into `InvoiceLineItem` structs with the correct descriptions for customer-facing invoices
- **ProrationLedgerEntries**: Converts raw credit/debit amounts into double-entry ledger entries for the internal financial ledger

## Information Model

- **PlanChangeEvent**: `subscription_id`, `old_plan_id`, `new_plan_id`, `old_price_cents`, `new_price_cents`, `effective_date`, `period_start`, `period_end`
- **ProrationResult**: `subscription_id`, `credit_amount_cents`, `debit_amount_cents`, `days_remaining`, `days_in_period`, `proration_factor` (decimal for audit trail), `line_items: []InvoiceLineItem`, `ledger_entries: []LedgerEntry`
- **LedgerEntry**: `account_type` (accounts_receivable / deferred_revenue / revenue), `debit_cents`, `credit_cents`, `memo`

## Interfaces

- `ProrationCalculator.Calculate(event PlanChangeEvent) ProrationResult` - Primary calculation interface (pure function, no I/O)
- `POST /internal/v1/proration/preview` - HTTP endpoint for admin console to preview proration before applying a plan change
- `GET /internal/v1/proration/{subscription_id}/history` - Return historical proration calculations for a subscription

## Files and Layout

```
billing-engine/
  internal/proration/
    calculator.go           - Core ProrationCalculator pure function
    date_math.go            - Period day-count arithmetic
    line_item_factory.go    - Invoice line item construction
    ledger_entries.go       - Double-entry ledger entry construction
    calculator_test.go      - Table-driven tests covering ~50 proration scenarios
  internal/handler/
    proration_handler.go    - Preview and history HTTP endpoints
```

## Work Plan

1. **Phase 1 - Core calculator (Week 1)**: Implement `PeriodDateMath` and `ProrationCalculator`; build a table-driven test suite covering upgrades, downgrades, same-day changes, period-end changes, leap year months, and 28/29/30/31-day months
2. **Phase 2 - Ledger entry construction (Week 2)**: Implement `ProrationLedgerEntries` producing balanced double-entry pairs; verify all test cases produce zero-sum ledger entries
3. **Phase 3 - Line item factory (Week 3)**: Implement `ProrationLineItemFactory` with customer-facing description strings; verify line item amounts match Stripe's own proration for equivalent scenarios
4. **Phase 4 - HTTP endpoints (Week 4)**: Implement preview and history endpoints; integration test preview endpoint with a real plan change workflow

## Risks and Mitigations

- **Off-by-one in day count**: Month boundaries and period-end coinciding with effective date produce edge cases; mitigate with 50+ table-driven test cases covering all calendar boundary scenarios
- **Ledger entry imbalance**: Rounding on credit and debit independently can produce a 1-cent imbalance; mitigate by computing credit first and deriving debit as `total - credit` to guarantee balance
- **Stripe proration divergence**: Stripe calculates its own proration for Stripe-managed invoices; if our proration differs from Stripe's by more than $0.01 it creates reconciliation issues; mitigate by running daily comparison tests against Stripe sandbox
