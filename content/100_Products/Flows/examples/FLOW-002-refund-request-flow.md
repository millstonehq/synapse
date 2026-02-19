---
id: FLOW-002
type: flow
title: Refund Request Flow
status: approved
owner: QA Engineer
created: '2025-04-11T14:42:13.466Z'
updated: '2025-03-19T11:24:00.106Z'
tags:
  - flow
  - payment-processing
summary: Refund Request Flow
feature_area: Payment Processing
related_prds:
  - PRD-003
example: true
---

## Steps

### Step 1: Locate the Order

Customer navigates to their order history and finds the order they want to refund. Order history is filtered to show orders that are eligible for refund (in `captured` or `settled` state, within the 90-day refund window). Customer clicks "Request Refund" on the order.

### Step 2: Select Refund Amount and Reason

Customer selects whether to refund the full order total or a partial amount. For partial refunds, a numeric input allows them to enter the refund amount (must be between $1 and the original captured amount). Customer selects a reason from the dropdown: "Item not as described", "Item not received", "Wrong item sent", "Changed mind", or "Other".

### Step 3: Submit Refund Request

Customer reviews the refund summary: order number, original amount, refund amount, reason. Customer clicks "Submit Refund". System calls the Payments API refund endpoint with an idempotency key generated client-side. Typical processing time is 1-2 seconds.

### Step 4: Confirmation

On success, customer sees a refund confirmation with:
- Refund confirmation number
- Refund amount and expected return date (3-5 business days for card refunds)
- Original order number for reference

On failure, customer sees an error message with:
- "Your refund could not be processed. Please contact support." with a support ticket link
- The refund is not retried automatically; customer must initiate again or contact support

## Expected Results

- Refund is created in `refund_pending` state and transitions to `refunded` when confirmed by gateway
- Customer receives refund confirmation email within 60 seconds
- Refund appears in customer transaction history with the original order reference
- If gateway declines the refund (e.g., card no longer valid), the support team is notified automatically
- The refunded amount is credited to the original payment method within 3-5 business days

## User Info

| Field | Value |
|-------|-------|
| Role | Customer (authenticated) |
| Permissions | Can view own orders, request refunds within 90 days |
| Test account | testuser@example.com |
| Test order | Any captured order in staging; use Stripe test card ending 4242 |
| Environment | Staging |
