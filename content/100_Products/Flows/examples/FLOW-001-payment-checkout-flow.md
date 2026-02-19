---
id: FLOW-001
type: flow
title: Payment Checkout Flow
status: approved
owner: QA Lead
created: '2024-07-15T14:39:32.334Z'
updated: '2026-08-30T19:59:25.405Z'
tags:
  - flow
  - payment-processing
summary: Payment Checkout Flow
feature_area: Payment Processing
related_prds:
  - PRD-005
example: true
---

## Steps

### Step 1: Select Payment Method

User navigates to the checkout page and sees their saved payment methods. The default payment method is pre-selected. User can select a different saved card or click "Add new payment method" to enter new card details via the Stripe Elements form.

### Step 2: Review Order Summary

User reviews the order summary showing line items, subtotal, tax, and total amount. The selected payment method is shown with last four digits. User clicks "Place Order" to proceed.

### Step 3: Payment Processing

System displays a loading indicator while the payment is being authorized. The Payments API receives the authorization request, validates the idempotency key, and sends the charge to Stripe. This typically takes 1-2 seconds.

### Step 4: Confirmation

On success, user sees an order confirmation page with:
- Order number and confirmation code
- Payment amount and last four digits of the card used
- Estimated delivery date
- Link to view order details in their account

On failure, user sees an error message with:
- Clear description of the issue ("Your card was declined", "Payment processing is temporarily unavailable")
- Suggested action ("Try a different payment method", "Please try again in a few minutes")
- Link to contact support if the issue persists

## Expected Results

- Payment is authorized and captured successfully for the order total
- Order record is created and linked to the payment transaction
- Confirmation email is sent to the customer within 60 seconds
- Payment appears in the customer's transaction history immediately
- If payment fails, no order is created and the customer can retry without risk of double-charging

## User Info

| Field | Value |
|-------|-------|
| Role | Customer (authenticated) |
| Permissions | Can view own orders, manage payment methods |
| Test account | testuser@example.com |
| Test card | 4242 4242 4242 4242 (Stripe test card) |
| Environment | Staging |
