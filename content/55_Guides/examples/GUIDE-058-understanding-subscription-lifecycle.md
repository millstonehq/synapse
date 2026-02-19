---
id: GUIDE-058
type: guide
title: Understanding Subscription Lifecycle
status: approved
owner: Developer Experience
created: '2024-11-05T04:02:23.702Z'
updated: '2025-05-08T07:49:47.947Z'
tags:
  - guide
  - billing-engine
summary: Understanding Subscription Lifecycle
audience: customer
related_systems:
  - SYSTEM-047
  - SYSTEM-049
related_sops:
  - SOP-093
  - SOP-092
example: true
---

## Why Subscription Lifecycle Matters

A subscription in the Billing Engine is not just a record — it is a state machine that drives billing behavior. Understanding the lifecycle states and the transitions between them is essential for building features that interact with billing (upgrade flows, cancellation flows, trial management) and for diagnosing unexpected billing behavior when customers report issues.

This guide walks through every lifecycle state, what triggers transitions between them, and what billing actions occur at each stage.

## Subscription States

A subscription moves through these states during its lifetime:

- **TRIALING**: The account is in a free trial period. No invoices are generated. Usage events are recorded but not billed. The trial end date is set at subscription creation.
- **ACTIVE**: The subscription is live and billing is enabled. Invoices are generated at the end of each billing period. Usage is metered and accumulated.
- **PAST_DUE**: A payment attempt for a generated invoice has failed. Billing continues (invoices are still generated) but the dunning workflow is active. The subscription remains accessible to the customer but may have feature restrictions.
- **PAUSED**: Billing is suspended at the customer's request or by an internal hold. No invoices are generated during the pause period. Pause duration may be limited by plan rules.
- **CANCELLING**: A cancellation has been scheduled but has not yet taken effect. The subscription remains `ACTIVE` for billing purposes until the cancellation date. The customer retains access.
- **CANCELLED**: The subscription has ended. No further billing occurs. Historical invoices remain accessible. Account data is retained per the retention policy.

## Key Lifecycle Events

The Billing Engine publishes events for every state transition. Downstream services (product access control, customer notifications, analytics) subscribe to these events to react appropriately:

- `billing.subscription.trial_ending_soon` — emitted 7 days before trial end
- `billing.subscription.activated` — trial-to-active transition
- `billing.subscription.payment_failed` — payment failure, triggers PAST_DUE
- `billing.subscription.cancelled` — cancellation effective
- `billing.subscription.reactivated` — cancelled or paused subscription restored to active

## Pro-ration and Mid-Cycle Changes

When a customer upgrades or downgrades their plan mid-cycle, pro-ration ensures they are charged fairly. An upgrade generates a pro-rated charge for the remainder of the billing period at the new rate. A downgrade generates a pro-rated credit for the unused days on the old plan. Both are reflected as line items on the next invoice.

## Common Questions

**What happens to usage events during PAUSED state?** Events are still accepted and stored, but they are not aggregated for billing until the subscription returns to `ACTIVE`. If the pause expires without renewal, accumulated events are cleared.

**Can a CANCELLED subscription be reactivated?** Yes, within 30 days of cancellation. After 30 days the account data may be archived and reactivation requires customer support intervention.

## Next Steps

- Use the Billing API `/v1/accounts/{id}/subscription` endpoint to query current state in real time
- Review the Handle Subscription Cancellation SOP if you need to execute a manual cancellation
