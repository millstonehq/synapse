---
id: FLOW-004
type: flow
title: Subscription Renewal Flow
status: deprecated
owner: QA Lead
created: '2024-04-20T23:41:39.850Z'
updated: '2025-08-26T01:54:46.424Z'
tags:
  - flow
  - payment-processing
summary: Subscription Renewal Flow
feature_area: Payment Processing
related_prds:
  - PRD-004
example: true
---

## Steps

### Step 1: Renewal Trigger

The subscription renewal batch job runs at 02:00 UTC daily. It queries the `subscriptions` table for all active subscriptions where `current_period_end` is within the next 24 hours. For each subscription due, it creates a renewal task entry and enqueues it to the renewal processing queue. A "your subscription renews tomorrow" notification email is sent to customers at 08:00 UTC the day before renewal.

### Step 2: Charge Processing

The renewal worker picks up each renewal task. It calls the Payments API `POST /v1/payments/authorize` endpoint using the subscription's stored default payment method token, passing a unique idempotency key per renewal attempt to prevent duplicate charges. The authorize request includes `capture: immediate` to authorize and capture in a single step. Typical processing time is 1-2 seconds per renewal.

### Step 3: Success Path

On successful authorization:
- Subscription `current_period_start` and `current_period_end` are advanced by one billing cycle
- Subscription state remains `active`
- `subscription.renewed` event is published to SQS
- Customer receives a "your subscription has been renewed" email with the invoice details and next renewal date

### Step 4: Failure Path (Dunning)

On failed authorization (card declined, insufficient funds, expired card):
- `RenewalAttempt` record is created with `status: failed` and the gateway error code
- Subscription state transitions to `past_due`
- Customer receives a "payment failed" email with instructions to update their payment method
- Retry is scheduled: attempt 2 at T+1 day, attempt 3 at T+3 days, attempt 4 at T+7 days
- If all 4 attempts fail, subscription transitions to `suspended` and customer receives a final cancellation warning email

## Expected Results

- 94%+ of renewals succeed on the first attempt
- Failed renewals enter the dunning process automatically, with no manual intervention needed
- Customers receive renewal confirmation email within 5 minutes of successful charge
- Subscription `current_period_end` is always advanced atomically with the successful payment (never advanced for a failed charge)
- All renewal attempts (success and failure) are recorded in `renewal_attempts` for audit and reporting

## User Info

| Field | Value |
|-------|-------|
| Role | System (automated) / Operations staff (monitoring) |
| Permissions | Batch job uses service account with payment write permission |
| Test trigger | Use Stripe test card 4000000000000341 to simulate insufficient funds for dunning test |
| Test renewal | Set `current_period_end` to now+1h in staging DB to trigger early renewal |
| Environment | Staging |
