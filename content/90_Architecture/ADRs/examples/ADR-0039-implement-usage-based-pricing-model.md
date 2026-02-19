---
id: ADR-0039
type: adr
title: Implement Usage-Based Pricing Model
status: draft
owner: Principal Engineer
created: '2024-08-27T11:34:40.030Z'
updated: '2026-02-25T18:45:14.397Z'
tags:
  - adr
  - billing-engine
summary: Implement Usage-Based Pricing Model
example: true
---

## Context

The Billing Engine currently supports only flat-rate subscription plans (a fixed monthly fee per plan tier). As the product has matured, we have identified that a significant portion of enterprise customers have usage patterns that are poorly served by flat-rate pricing: some customers use the product very lightly (overpaying) while others use it heavily (generating more value than they pay for). Both situations create churn pressure.

Product and Sales have requested the ability to offer usage-based pricing alongside or instead of flat-rate plans. The primary metric candidates are: API calls, active seats, data storage (GB), and processed records. Different customer segments prefer different metrics; enterprise customers strongly prefer seat-based pricing while SMB customers prefer API call or record-based pricing.

Implementing usage-based pricing requires: accurate, tamper-evident usage metering at scale; aggregation logic that maps raw events to billable quantities; proration handling for mid-cycle plan changes; and transparent usage visibility for customers.

## Decision

Implement a **usage-based pricing model** as a first-class billing primitive in the Billing Engine, supported by the Usage Metering Service for event collection and aggregation.

The model will support three pricing structures that can be combined per plan:

1. **Flat rate**: A fixed monthly fee component (can be $0)
2. **Per-unit metered**: A rate per unit of a metered metric (e.g., $0.001 per API call)
3. **Tiered metered**: Volume-based tiered pricing where the per-unit rate decreases above defined thresholds

Usage quantities will be aggregated over the billing period using the SUM function for consumable metrics and MAX for capacity metrics. Invoice line items will itemize each pricing component separately.

## Consequences

**Positive:**
- Pricing can be aligned with the value customers receive, reducing churn from over/underpayment
- Opens new revenue opportunities in enterprise segments that demand consumption-based pricing
- Transparent usage data improves customer trust and reduces billing disputes

**Negative:**
- Revenue becomes variable and harder to forecast; monthly revenue will fluctuate with usage patterns
- Requires accurate, high-throughput usage metering infrastructure that does not currently exist — significant build investment
- Customer success and support must be trained on explaining usage-based bills, which are more complex than flat-rate

**Neutral:**
- Existing flat-rate plans will continue to be supported; usage-based pricing is additive, not a replacement
- Stripe Billing supports metered billing natively, which reduces the integration complexity

## Alternatives Considered

**Tiered flat-rate pricing only (no metered component):**
- Pro: Simpler to implement, predictable revenue, easier for customers to understand
- Con: Does not solve the core problem — customers are still paying based on a tier threshold rather than actual usage. Light users still overpay, heavy users still underpay within a tier.
- Rejected because: Does not address the product-market fit issue identified by Sales for enterprise accounts.

**Full delegation of usage billing to Stripe Metered Billing:**
- Pro: Minimal internal infrastructure needed; Stripe handles aggregation and invoicing
- Con: Stripe Metered Billing has limited aggregation flexibility (SUM only); does not support MAX or custom aggregation functions. Puts customer usage data entirely in Stripe, limiting our visibility and analytics.
- Rejected because: Our usage patterns require MAX aggregation for seat-based metrics, which Stripe does not support natively. We also need usage data in our analytics systems.
