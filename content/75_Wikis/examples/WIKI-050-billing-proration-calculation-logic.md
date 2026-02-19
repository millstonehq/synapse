---
id: WIKI-050
type: wiki
title: Billing Proration - Calculation Logic
status: draft
owner: Billing Team
created: '2024-02-07T02:28:22.886Z'
updated: '2026-08-31T15:29:30.632Z'
tags:
  - wiki
  - billing-engine
summary: Billing Proration - Calculation Logic
source_repo: https://git.example.com/acme/billing-proration
commit_sha: a6b5bd233d882f7253f412cdebfd8f43ee0c20e0
generated_at: '2025-11-15T22:19:32.727Z'
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
importance: medium
example: true
---

## Overview

Proration in the Billing Engine refers to the calculation of partial-period charges and credits that arise when a subscription plan changes mid-billing-period. When a customer upgrades or downgrades a plan, or adds/removes a metered component, they should pay only for the days they were on each plan within the billing period. The Proration Calculator implements the day-accurate proration logic used throughout the Billing Engine.

This page documents the calculation methodology, the edge cases handled by the implementation, and how proration results are represented in the double-entry financial ledger.

## Calculation Methodology

Proration is calculated at day granularity. The number of days remaining in the current billing period from the effective date (inclusive) is divided by the total number of days in the billing period. This ratio is the proration factor.

```
proration_factor = days_remaining / days_in_period
```

Where:
- `days_remaining` = (`period_end` - `effective_date`).days + 1 (inclusive of both endpoints)
- `days_in_period` = (`period_end` - `period_start`).days + 1

The credit for the old plan (unused days) is:

```
credit = round_down(old_plan_price_cents * proration_factor)
```

The debit for the new plan (remaining days) is:

```
debit = new_plan_price_cents - round_down(new_plan_price_cents * (1 - proration_factor))
```

Importantly, the debit is computed as the complement of the new plan's unused days rather than as `new_price * proration_factor`. This ensures that `credit + debit` always equals the expected net charge when the two amounts are combined on the invoice — preventing penny-rounding artifacts.

## Proration Factor Examples

| Period | Effective Date | Days Remaining | Days in Period | Proration Factor |
|--------|---------------|---------------|----------------|-----------------|
| Jan 1 - Jan 31 | Jan 16 | 16 | 31 | 0.516 |
| Feb 1 - Feb 28 | Feb 14 | 15 | 28 | 0.536 |
| Mar 1 - Mar 31 | Mar 31 | 1 | 31 | 0.032 |
| Apr 1 - Apr 30 | Apr 1 | 30 | 30 | 1.000 |

## Edge Cases

- **Same-day plan change**: If `effective_date` equals `period_start`, the proration factor is 1.0 and the full new plan price is charged (no proration credit — the customer was on the old plan for zero days of the new period). This is the standard case for upgrades at renewal.
- **Plan change on period_end**: The proration factor is 1/days_in_period (minimum). A credit for one day of the old plan and a charge for one day of the new plan are issued.
- **Leap year February**: The `PeriodDateMath` module uses calendar-aware date arithmetic. February in a leap year has 29 days; the proration factor is computed correctly.
- **Annual plans prorating to monthly**: The proration calculation always uses the billing period of the subscription, not a monthly assumption. For an annual subscription, `days_in_period` may be 365 or 366.

## Ledger Representation

Every proration result produces two balanced ledger entries per the double-entry bookkeeping pattern:

**For an upgrade (debit > credit, net charge to customer):**
- Debit: Accounts Receivable (`+debit_amount`)
- Credit: Revenue (`+debit_amount`)
- Credit: Accounts Receivable (`+credit_amount`)
- Debit: Revenue (`+credit_amount`) — reversal of old plan revenue for unused days

The sum of all debits equals the sum of all credits. The net effect on Revenue is `debit_amount - credit_amount` (the incremental revenue from the upgrade for the remaining period).

## Known Limitations

- Proration is computed at the plan level, not the component level. For plans with mixed flat-rate and metered components, the proration credit applies to the flat-rate component only; metered charges are calculated from actual usage and are not prorated.
- Proration for mid-period quantity changes (e.g., adding seats mid-period) uses the same day-accurate calculation but is applied per-seat-change event rather than per-plan-change event.
