---
id: FLOW-037
type: flow
title: Invoice Generation Flow
status: approved
owner: QA Lead
created: '2024-11-19T13:10:37.602Z'
updated: '2025-05-02T05:42:41.876Z'
tags:
  - flow
  - billing-engine
summary: Invoice Generation Flow
feature_area: Billing Engine
related_prds:
  - PRD-046
example: true
---

## Steps

### Step 1: Billing Run Trigger

At the end of a customer's billing period, the Invoice Scheduler detects that a subscription's `current_period_end` has elapsed and enqueues a billing run job to RabbitMQ. The job payload includes the subscription ID, billing period start/end dates, and a unique billing run ID used as the idempotency key. For manual invoice generation triggered by an admin (via the Billing Admin Console, [[PRD-046|PRD-046]]), the trigger is an API call to the billing run endpoint.

### Step 2: Usage Aggregation and Proration Fetch

The Invoice Worker picks up the billing run job and begins assembling the invoice. For subscriptions with usage-based components, it calls the Usage Aggregation Service to retrieve the final billable quantities for each metered metric for the closed period. For subscriptions where a plan change occurred during the period, it calls the Proration Calculator to retrieve the credit and debit line items for the partial-period charges and credits.

### Step 3: Tax Calculation

The Invoice Worker calls the Tax Calculation Engine with the assembled pre-tax line items and the customer's billing address. The Tax Calculation Engine calls the Avalara AvaTax v2 API to determine applicable tax rates and amounts for each jurisdiction. The result is cached in Redis with a 1-hour TTL per the Avalara integration architecture. The tax amounts are appended to each line item.

### Step 4: Invoice Assembly and Persistence

The Invoice Worker assembles the complete invoice with all line items, tax amounts, subtotal, and total. The invoice is written to PostgreSQL within a single database transaction that also updates the billing run status to `complete`. A PDF version is generated and stored in S3. The invoice is simultaneously created in Stripe as a finalized Stripe Invoice object and the Stripe Invoice ID is recorded on the internal invoice record.

### Step 5: Payment Charge

The finalized `invoice.finalized` event is published to RabbitMQ. The Billing Event Processor consumes the event and initiates the charge attempt against the customer's default payment method via Stripe Billing. Stripe sends a webhook (`invoice.payment_succeeded` or `invoice.payment_failed`) when the charge completes. The Billing Webhook Processor updates the invoice payment status accordingly.

## Expected Results

- A complete, tax-accurate invoice is created with itemized line items for flat-rate, metered, and proration components
- The invoice is persisted in both the internal database and Stripe with matching amounts
- A PDF invoice is available for download from S3 within 30 seconds of billing run completion
- The customer's payment method is charged automatically within 60 seconds of invoice finalization
- An invoice email is sent to the customer's billing contact within 5 minutes of successful payment

## User Info

| Field | Value |
|-------|-------|
| Role | Billing Engine (automated) / Admin (manual trigger) |
| Permissions | Internal service-to-service; Admin requires billing:write role |
| Test account | test-subscription-001 (staging Stripe test mode) |
| Test payment | Stripe test card 4242 4242 4242 4242 |
| Environment | Staging (Stripe test mode, Avalara sandbox) |
