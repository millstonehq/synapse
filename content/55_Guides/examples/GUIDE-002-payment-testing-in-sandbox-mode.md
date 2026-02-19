---
id: GUIDE-002
type: guide
title: Payment Testing in Sandbox Mode
status: review
owner: Developer Experience
created: '2025-07-29T20:24:32.192Z'
updated: '2026-08-13T21:37:16.073Z'
tags:
  - guide
  - payment-processing
summary: Payment Testing in Sandbox Mode
audience: partner
related_systems:
  - SYSTEM-001
  - SYSTEM-003
related_sops:
  - SOP-002
  - SOP-009
example: true
---

## Overview

The sandbox environment is an isolated replica of the production payment platform that uses simulated gateway responses instead of real payment networks. You can test every payment scenario — success, decline, timeout, refund, chargeback — without moving real money or affecting production data.

Sandbox credentials are separate from production credentials. Your sandbox API key will be rejected by the production environment and vice versa. This isolation is intentional.

## Sandbox Test Cards

Use the following card numbers to simulate specific payment outcomes in the sandbox. All test cards use any future expiry date and any 3-digit CVV.

- `4111111111111111` — Visa, successful authorization and capture
- `5500000000000004` — Mastercard, successful authorization and capture
- `4000000000000002` — Generic decline (do_not_honor)
- `4000000000009995` — Insufficient funds decline
- `4000000000000069` — Expired card decline
- `4000002760003184` — 3D Secure required; complete authentication to succeed
- `4000000000000259` — Simulates a dispute filed after capture

## Testing Key Payment Flows

Before going live, your integration must successfully handle each of these scenarios in the sandbox:

**Authorization and capture:** Create a payment intent, confirm with a success test card, verify `status: succeeded` and that the amount matches.

**Declined payment:** Confirm with a decline test card, verify your integration surfaces an appropriate error message to the customer without exposing raw error codes.

**3D Secure flow:** Use the 3DS test card, verify your integration correctly handles the `requires_action` response and redirects to the authentication page.

**Refund:** Issue a full and partial refund via `POST /v1/refunds`, verify the refund status transitions to `succeeded` and the original payment shows `amount_refunded`.

**Idempotency:** Replay the same payment intent creation request twice with the same idempotency key; verify the second request returns the original response without creating a new charge.

**Webhook delivery:** Verify your webhook endpoint receives `payment_intent.succeeded` and `payment_intent.payment_failed` events and responds with HTTP 200 within 30 seconds.

## Common Testing Mistakes

- **Testing with production credentials**: Production API keys are rejected in sandbox, but accidentally using production test data in production is a real risk. Always confirm which environment your API key targets before running tests.
- **Ignoring 3DS flows**: 3DS handling is mandatory in production. If you skip testing 3DS in sandbox, your integration will fail for a significant share of production transactions.
- **Not testing webhook failures**: Your webhook handler should be idempotent. Test by replaying the same event multiple times to confirm your handler does not create duplicate records.

## Next Steps

- Complete all required test scenarios and document results in your integration checklist
- Share your sandbox test results with your account manager for pre-launch review
- Review the going-live checklist in the merchant portal before requesting a production API key
