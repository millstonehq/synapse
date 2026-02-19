---
id: ADR-0038
type: adr
title: Choose Stripe Billing as Payment Backend
status: approved
owner: Tech Lead
created: '2024-10-31T05:55:34.751Z'
updated: '2026-06-22T08:56:43.639Z'
tags:
  - adr
  - billing-engine
summary: Choose Stripe Billing as Payment Backend
example: true
---

## Context

The Billing Engine needs an external payment processing backend to handle charge execution, payment method storage, webhook delivery, and subscription billing primitives. The platform currently has no payment backend; engineers are manually creating charges via the Stripe dashboard. This is not scalable and does not support automated invoice charging.

The requirements for a payment backend are: programmatic API for charge creation and refunds, payment method tokenization (we must not store raw card data), webhook delivery for async payment status updates, support for subscription billing primitives (recurring charges, proration, trial periods), and strong compliance posture (PCI DSS Level 1 certification by provider). The platform is expected to process $500K MRR within 12 months of launch, growing to $5M MRR within 3 years.

We evaluated three candidates: Stripe Billing, Braintree (PayPal), and a self-hosted solution using Adyen.

## Decision

Adopt **Stripe Billing** as the primary payment backend for the Billing Engine.

Integration approach: The Billing Engine will use Stripe Customers, PaymentMethods, and Invoices as the canonical billing objects. Stripe Billing's subscription primitives will be used for recurring charge execution; our internal Subscription Management Service remains the source of truth for subscription state and sends commands to Stripe rather than delegating subscription lifecycle management to Stripe.

Stripe webhook events will be consumed by the Billing Event Processor and translated to internal billing domain events.

## Consequences

**Positive:**
- Best-in-class developer experience and documentation; fastest integration path
- PCI DSS Level 1 certification; we never handle raw card data
- Mature subscription billing primitives reduce implementation scope for recurring charges, proration, and trial management
- Extensive webhook coverage enables reliable async billing workflows
- Strong SLA (99.99% uptime) and global infrastructure

**Negative:**
- Vendor lock-in: migrating away from Stripe in the future would require significant rework of the billing data model
- Stripe charges 0.5% additional fee for using Billing (on top of card processing fees); estimated $25K/year at $5M MRR
- Stripe's subscription model may conflict with our internal subscription state machine for complex lifecycle scenarios; we must be disciplined about keeping our state machine as source of truth

**Neutral:**
- Stripe's test mode and sandbox environment are well-suited to our integration testing strategy
- Stripe Connect (multi-party payments) is not needed in the current scope but is available if the product evolves in that direction

## Alternatives Considered

**Braintree (PayPal):**
- Pro: Lower transaction fees, included with PayPal relationship
- Con: Developer experience significantly worse than Stripe; webhook reliability has been inconsistent based on industry reports; subscription primitives are less mature. Integration timeline would be 2x longer.
- Rejected because: Integration velocity and webhook reliability are critical for launch timelines.

**Self-hosted via Adyen:**
- Pro: Maximum control, lowest per-transaction cost at scale
- Con: Requires PCI DSS Level 1 self-certification (12-18 months, $500K+ cost); no turnkey subscription billing primitives; requires significant engineering investment for payment method storage, webhook infrastructure, and fraud detection.
- Rejected because: The engineering investment and compliance cost are disproportionate at current scale. Can be revisited if transaction volume exceeds $50M ARR.
