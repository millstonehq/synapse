---
id: FLOW-003
type: flow
title: Chargeback Dispute Flow
status: draft
owner: QA Lead
created: '2024-01-22T15:14:29.830Z'
updated: '2025-09-21T23:46:12.351Z'
tags:
  - flow
  - payment-processing
summary: Chargeback Dispute Flow
feature_area: Payment Processing
related_prds:
  - PRD-004
example: true
---

## Steps

### Step 1: Dispute Notification Received

Stripe delivers a `charge.dispute.created` webhook event to the Payment Webhook Dispatcher. The dispatcher records the dispute in the `payment_events` table as a `payment.disputed` event and updates the payment state from `settled` to `disputed`. An automatic notification is sent to the #payments-disputes Slack channel with the dispute ID, amount, and reason code.

### Step 2: Operations Team Review

Operations staff receive the Slack notification and open the dispute in the Stripe dashboard within 24 hours (the response deadline for most dispute types is 7 days). They review the dispute reason (unauthorized, product not received, product not as described, credit not processed, general). They retrieve the following evidence from internal systems: order record, delivery confirmation, product photos, and customer communication history.

### Step 3: Evidence Submission

Operations staff submit evidence via the Stripe dashboard or Stripe Evidence API before the deadline. Required evidence includes: customer IP address at order time, order receipt, fulfillment tracking number (for physical goods), or service delivery logs (for digital goods). Evidence is submitted using the internal dispute evidence template.

### Step 4: Resolution

Stripe notifies via webhook within 60-120 days of the decision:
- `charge.dispute.won`: Funds returned to merchant. Payment state updated to `dispute_won`. Customer account flagged for review if this is their first win.
- `charge.dispute.lost`: Dispute amount plus chargeback fee (~$15) deducted. Payment state updated to `dispute_lost`. Finance team notified for reconciliation.

## Expected Results

- All `charge.dispute.created` webhooks are received and processed within 5 minutes
- Operations team is notified within 5 minutes of any new dispute
- Evidence is submitted before the gateway deadline for 100% of disputes
- Dispute outcome is recorded in the `payment_events` table for audit purposes
- Finance team receives weekly dispute summary report for reconciliation

## User Info

| Field | Value |
|-------|-------|
| Role | Operations staff (authenticated employee) |
| Permissions | Can view payment details and dispute records; can submit evidence |
| Test trigger | Use Stripe test card 4000000000000259 to trigger a dispute in staging |
| Test dispute reason | Fraudulent (most common reason code to test) |
| Environment | Staging |
