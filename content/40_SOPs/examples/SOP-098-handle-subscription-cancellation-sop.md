---
id: SOP-098
type: sop
title: Handle Subscription Cancellation SOP
status: accepted
owner: SRE Lead
created: '2024-08-25T07:02:52.130Z'
updated: '2025-07-17T06:43:14.376Z'
tags:
  - sop
  - billing-engine
summary: Handle Subscription Cancellation SOP
related_process: PROCESS-057
related_systems:
  - SYSTEM-047
example: true
---

## Preconditions

- A subscription cancellation request has been received and is documented with: account ID, cancellation effective date, and cancellation reason
- The cancellation has been approved per the contract terms (support team or account management has confirmed)
- Any outstanding invoices for the account have been reviewed; unpaid invoices must be resolved before cancellation unless waived by Finance

## Materials/Access

- Write access to the subscription management module in the billing admin console (role: `billing-account-manager`)
- The cancellation request ticket ID
- Access to the customer account in the billing admin console
- Access to billing event stream to confirm cancellation events

## Procedure

1. Open the cancellation request ticket and confirm the account ID, effective cancellation date, and the handling for any remaining billing period (pro-ration, charge through end of period, or immediate termination with credit).
2. Log in to the billing admin console and navigate to the customer account.
3. Review the account's active subscription, pending invoices, and current billing period end date.
4. If there are outstanding unpaid invoices, confirm with Finance Operations whether they should be collected or waived before proceeding.
5. Navigate to **Subscriptions > Cancel** and set the cancellation type (immediate or end-of-period) per the approved request.
6. If the cancellation includes a pro-ration credit for the unused billing period, review the credit amount in the cancellation preview and confirm it matches the calculated value.
7. Submit the cancellation. The subscription status will change to `CANCELLING` or `CANCELLED` depending on the effective date.
8. Confirm a `billing.subscription.cancelled` event is published to the billing event bus for the account.
9. Update the cancellation request ticket with the subscription cancellation record ID and close the ticket.

## Validation

- Subscription status in the billing admin console is `CANCELLED` or shows a future cancellation date matching the request
- No new invoice generation attempts will be made for billing periods after the cancellation effective date
- Pro-ration credit (if applicable) is reflected in the account's credit balance
- `billing.subscription.cancelled` event is present in the event bus
- Finance Operations has been notified if the cancellation affects an account above the $10,000 annual value threshold

## Rollback

1. If a cancellation was submitted in error, navigate to the subscription in the billing admin console.
2. Click **Reinstate Subscription** (available only if the cancellation effective date has not passed).
3. Confirm the subscription returns to `ACTIVE` status with the original billing plan and next invoice date.
4. If a pro-ration credit was issued, void the credit per the Process Billing Credit SOP rollback procedure.
5. Update the cancellation ticket with the reinstatement record and notify the requester.
