---
id: ADR-0002
type: adr
title: Adopt Stripe as Primary Payment Provider
status: approved
owner: Tech Lead
created: '2025-03-15T05:12:51.362Z'
updated: '2025-03-08T21:30:29.394Z'
tags:
  - adr
  - payment-processing
summary: Adopt Stripe as Primary Payment Provider
example: true
---

## Context

The platform currently has no payment processing capability. All customer payments are handled manually — operations staff enter transactions directly into a payment gateway dashboard. This process is error-prone, does not scale, and cannot support the automated billing workflows that the product roadmap requires.

We need to select a primary payment gateway provider to integrate with. The choice affects developer experience, transaction costs, compliance obligations, reliability, and our ability to support international payments and currencies. The selected provider will handle card tokenisation, authorization, capture, refund, and webhook delivery for all platform transactions.

Key constraints: the team has limited payment domain experience, we need to go live within 10 weeks, and we cannot store raw card data (PCI scope reduction is a hard requirement). We process approximately 50,000 transactions per day at an average transaction value of $38.

## Decision

Adopt **Stripe** as the primary payment gateway, with PayPal retained as a secondary fallback gateway for resilience.

Stripe will be integrated via the `stripe-go` SDK v76 using the PaymentIntents API. All card data will be collected via Stripe Elements (client-side JavaScript), ensuring our servers never handle raw card numbers. Stripe webhook events will be consumed by the Payment Webhook Dispatcher for asynchronous state updates.

## Consequences

**Positive:**
- Stripe's developer experience and documentation are best-in-class, reducing integration time significantly
- PaymentIntents API has native support for idempotency keys, directly aligning with our idempotency requirement
- Stripe handles PCI compliance scope via Elements; we qualify for SAQ A (the simplest self-assessment)
- Stripe's uptime history is strong (99.95%+ over rolling 12 months)

**Negative:**
- Stripe's 2.9% + $0.30 per-transaction pricing is higher than interchange-plus alternatives like Adyen at our volume
- Stripe does not support all payment methods in all countries — some emerging markets will not be serviceable
- Vendor lock-in risk: migrating away from Stripe would require re-tokenising all stored payment methods

**Neutral:**
- PayPal as secondary gateway adds integration complexity but provides failover assurance
- Stripe's API versioning policy (dated versions) requires active version management as we upgrade the SDK

## Alternatives Considered

**Adyen:**
- Pro: Best per-transaction economics at scale, widest global payment method coverage, excellent uptime
- Con: Requires PCI DSS Level 1 compliance for direct integration, 3-month onboarding, and minimum monthly volume guarantees
- Rejected because: PCI Level 1 is not achievable within the 10-week timeline and the minimum volume guarantee carries financial risk at our current scale.

**Braintree (PayPal):**
- Pro: Strong US market coverage, PayPal native support, competitive pricing
- Con: Developer experience and SDK quality are significantly behind Stripe; documentation is inconsistent
- Rejected because: The inferior developer experience would slow integration and increase defect risk given the team's limited payments experience.
