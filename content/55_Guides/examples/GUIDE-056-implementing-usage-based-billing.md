---
id: GUIDE-056
type: guide
title: Implementing Usage-Based Billing
status: approved
owner: Developer Experience
created: '2024-11-25T14:55:23.528Z'
updated: '2025-04-08T15:12:39.162Z'
tags:
  - guide
  - billing-engine
summary: Implementing Usage-Based Billing
audience: customer
related_systems:
  - SYSTEM-047
  - SYSTEM-049
related_sops:
  - SOP-096
  - SOP-100
example: true
---

## Why Usage-Based Billing

Usage-based billing (UBB) charges customers based on their actual consumption rather than a flat subscription rate. For products where usage varies significantly between customers — API calls, compute minutes, storage GB, message sends — UBB aligns cost with value, reduces churn from low-usage customers, and enables high-volume customers to scale without re-negotiating plans.

Getting UBB right requires more than just counting events. You need reliable metering, correct aggregation, transparent invoice line items, and a way for customers to predict and review their costs. This guide covers the implementation path from event emission to invoice.

## Metering: Getting Events Into the System

The foundation of UBB is the metering event. Every billable action in your product must emit a usage event to the Billing Engine. Events must conform to the Usage Metering Standard:

- Required fields: `event_id` (UUID v4), `account_id`, `event_type`, `quantity`, `unit`, `occurred_at` (ISO 8601 UTC)
- Emit events idempotently — if your service retries, the same `event_id` will be deduplicated
- Target emission latency: under 5 minutes from the action occurring

Use the Billing Events SDK for your language to ensure correct schema validation before emission. Do not build a custom HTTP client to the metering endpoint — the SDK handles batching, retries, and signature signing.

## Pricing Plans for Usage

Once events are flowing, configure a usage-based pricing tier in the Billing Plan Configuration Process. Define:

- The `event_type` to meter (e.g., `api.request`, `storage.gb.day`)
- The pricing model: per-unit, tiered, or volume-based
- The billing period for aggregation (monthly is standard)

For tiered pricing (first 10,000 units at $0.01, next 90,000 at $0.008, beyond at $0.005), each tier boundary must be configured explicitly in the plan. The billing engine applies tiers to the aggregate usage for the period, not per-event.

## Invoice Line Items and Customer Visibility

On invoice generation, the Billing Engine creates one line item per usage dimension. Each line item shows the total quantity consumed, the applied rate (or tier breakdown), and the calculated charge. Customers can also query their real-time usage via the Billing API before the period closes — building a usage dashboard using this endpoint reduces billing surprises and support volume.

## Common Pitfalls

**Clock skew causing events in the wrong period**: Always use server-side timestamps in `occurred_at`, not client-side. Client clocks may be wrong by minutes or hours, placing events in the wrong billing period.

**Missing deduplication logic on retries**: If your event emission logic retries on transient errors without the same `event_id`, you will double-count usage. Always generate the `event_id` before the first attempt and reuse it on retries.

## Next Steps

- Test your metering pipeline with the Testing Billing Scenarios Guide
- Review the Billing API documentation for the usage summary endpoint to build customer-facing dashboards
- Schedule a usage metering review with the Billing Platform team before your first production billing cycle
