---
id: GUIDE-070
type: guide
title: Implementing Custom Billing Plans Guide
status: review
owner: Engineering Team
created: '2025-10-15T18:50:38.653Z'
updated: '2025-12-06T22:58:31.949Z'
tags:
  - guide
  - billing-engine
summary: Implementing Custom Billing Plans Guide
audience: customer
related_systems:
  - SYSTEM-049
  - SYSTEM-047
related_sops:
  - SOP-099
  - SOP-094
example: true
---

## Why This Matters

The Billing Engine supports three pricing primitives: flat-rate, per-unit metered, and tiered metered. Most customer plans use a combination of these. Implementing a custom billing plan — one that does not fit a standard template — requires understanding how pricing is modeled in the Billing Engine, how usage is metered and aggregated, and how plan configuration interacts with the invoice generation pipeline.

This guide is for engineers implementing new plan types or configuring non-standard pricing for a customer deal. It covers the plan data model, how to configure metered components, and how to validate that a new plan produces correct invoices before it reaches production. See [[SYSTEM-049|Tax Calculation Engine]] for tax configuration and [[SYSTEM-047|Usage Metering Service]] for metering setup.

## Prerequisites

Before implementing a custom billing plan, ensure:

- You have access to the billing-engine repository and staging environment
- The Sales or Account Management team has provided a written pricing specification (unit of measure, tier thresholds, flat fee amounts)
- Finance has approved the pricing structure for revenue recognition compliance
- You have reviewed the plan's tax category with Finance (some metered services are subject to different tax rules)

## Plan Data Model

A billing plan is represented as a `Plan` object with one or more `PricingComponent` objects. Each component specifies:

- `pricing_type`: one of `flat_rate`, `per_unit`, or `tiered`
- `metric_name`: the usage metric this component bills on (required for `per_unit` and `tiered`; null for `flat_rate`)
- `unit_price_cents`: the price per unit for `per_unit` components
- `tiers`: an ordered list of `(up_to, unit_price_cents)` pairs for `tiered` components
- `aggregation_function`: the function used to compute billable quantity from raw events (`SUM`, `MAX`, `COUNT`, or `LAST`)

A plan is created via the internal Plan Management API:

```
POST /internal/v1/plans
{
  "name": "Enterprise Seats + API Calls",
  "components": [
    { "pricing_type": "flat_rate", "amount_cents": 50000 },
    { "pricing_type": "per_unit", "metric_name": "active_seats", "unit_price_cents": 1500, "aggregation_function": "MAX" },
    { "pricing_type": "tiered", "metric_name": "api_calls", "aggregation_function": "SUM",
      "tiers": [{ "up_to": 100000, "unit_price_cents": 1 }, { "up_to": null, "unit_price_cents": 0 }] }
  ]
}
```

## Configuring Metered Components

For metered components, you must ensure the Usage Metering Service is collecting the correct metric. The `metric_name` in the plan component must exactly match the `metric_name` field in the usage events emitted by the product service.

Check that events are arriving correctly in staging:

```
GET /v1/usage/customers/{test_customer_id}/current
```

Verify the metric name and quantity look correct for your test activity.

For `MAX` aggregation (seat-based metrics), ensure the product service emits a "high watermark" event at least once per day that reflects the current peak seat count. The aggregation service uses `MAX` over all events in the period — if no event is emitted on a given day, that day is excluded from the MAX calculation.

## Validating Invoice Output

Before assigning a new plan to any real customer, validate the invoice output in staging:

1. Create a test subscription on the new plan using the staging environment
2. Emit representative usage events via `POST /v1/usage/events` for the test customer
3. Trigger a manual billing run: `POST /internal/v1/billing-runs` with the test subscription ID
4. Review the generated invoice line items against the pricing specification
5. Verify tax calculation is correct by checking the Avalara audit trail in the Tax Calculation Engine

## Common Questions

### "The tiered pricing isn't calculating correctly — the top tier price is applying from the first unit."

Tiers are applied cumulatively in the order they are defined. The first tier applies to units 0 through `up_to` (inclusive). If your tiers are defined incorrectly (e.g., `up_to: 0` for the first tier), all usage will fall into the subsequent tier. Verify tier thresholds match the pricing specification exactly.

### "Usage is showing zero on the invoice but I can see events in the event store."

The most common cause is a `metric_name` mismatch between the plan component and the usage events. Check that `metric_name` in the plan component exactly matches the string value in the emitted events (case-sensitive). Also verify the events are within the billing period window — events outside the period's `period_start` to `period_end` are excluded from billing.

## Next Steps

- Review the [[SYSTEM-047|Usage Metering Service]] system doc for metering architecture and supported aggregation functions
- Review the [[SYSTEM-049|Tax Calculation Engine]] system doc for tax category configuration with Avalara
