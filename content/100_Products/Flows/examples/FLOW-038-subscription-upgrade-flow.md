---
id: FLOW-038
type: flow
title: Subscription Upgrade Flow
status: approved
owner: QA Lead
created: '2024-03-09T21:19:42.169Z'
updated: '2025-07-16T23:44:33.266Z'
tags:
  - flow
  - billing-engine
summary: Subscription Upgrade Flow
feature_area: Billing Engine
related_prds:
  - PRD-047
example: true
---

## Steps

### Step 1: Customer Selects New Plan

The customer navigates to the plan selection page (accessible from the Self-Service Billing Portal, [[PRD-047|PRD-047]]) and selects a higher-tier plan. Before confirming, the portal calls the Proration Calculator preview endpoint to calculate the upgrade proration: the remaining days in the current billing period are used to compute a credit for the unused portion of the current plan and a charge for the equivalent days on the new plan.

### Step 2: Proration Preview and Confirmation

The portal displays an itemized proration summary showing the credit amount for the old plan, the charge for the new plan prorated to the current period end, and the net amount due immediately or credited to the next invoice. The customer reviews the amounts and confirms the upgrade. The confirmation step requires the customer to check a box acknowledging the prorated charge.

### Step 3: Subscription State Transition

On confirmation, the portal API calls the Subscription Management Service to execute the `upgrade_requested` transition. The state machine validates the transition is allowed from the current state (must be `active`), acquires the Redis distributed lock for the subscription, and updates the plan ID and new pricing in the subscription record. The state transition event `subscription.plan_changed` is published to RabbitMQ.

### Step 4: Stripe Sync and Proration Invoice

The Stripe Subscription Adapter updates the Stripe subscription to the new price ID effective immediately. Stripe generates an automatic proration invoice for the remaining period. Simultaneously, the internal Invoice Pipeline creates a prorated invoice line item in the internal ledger with the debit and credit amounts from the Proration Calculator (as computed in Step 1). The two invoice records are reconciled via the Stripe invoice ID.

### Step 5: Confirmation Email

A subscription upgrade confirmation email is sent to the customer's billing contact within 5 minutes, summarizing the new plan name, effective date, prorated charge amount, and the date of the next full-period invoice.

## Expected Results

- The customer's subscription is immediately updated to the new plan upon confirmation
- A prorated charge or credit is calculated and applied to the current billing period
- The Stripe subscription record is updated synchronously within the same request flow
- An internal ledger entry is created reflecting the plan change with balanced debit/credit entries
- A confirmation email is sent within 5 minutes of the upgrade completing

## User Info

| Field | Value |
|-------|-------|
| Role | Account admin (authenticated, billing:write permission) |
| Permissions | Can manage subscription, view billing history |
| Test account | test-upgrade-account@example.com (staging) |
| Test subscription | sub_test_active_starter plan |
| Environment | Staging (Stripe test mode) |
