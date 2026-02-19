---
id: GUIDE-004
type: guide
title: Payment Webhook Development Guide
status: approved
owner: Developer Experience
created: '2025-06-29T14:56:19.975Z'
updated: '2026-03-26T23:03:24.289Z'
tags:
  - guide
  - payment-processing
summary: Payment Webhook Development Guide
audience: internal
related_systems:
  - SYSTEM-001
  - SYSTEM-005
related_sops:
  - SOP-003
  - SOP-001
example: true
---

## Why Webhooks Matter

Payment events are asynchronous. When a customer completes a purchase, the platform emits webhook events to notify your systems of payment lifecycle changes: `payment_intent.succeeded`, `payment_intent.payment_failed`, `refund.created`, `dispute.created`, and others. Without webhook processing, your systems must poll for payment status updates, which is inefficient and introduces latency in fulfillment workflows.

Webhooks are delivered with at-least-once semantics, meaning your handler must be idempotent — processing the same event twice must produce the same outcome as processing it once.

## Verifying Webhook Signatures

Every webhook delivery includes an `X-Payment-Signature` header containing an HMAC-SHA256 signature of the request body, signed with your endpoint's shared secret. You must verify this signature before processing any event.

```
// Example signature verification (Node.js)
const crypto = require('crypto');
const expectedSig = crypto
  .createHmac('sha256', process.env.WEBHOOK_SECRET)
  .update(rawRequestBody)
  .digest('hex');
if (expectedSig !== req.headers['x-payment-signature']) {
  return res.status(401).send('Invalid signature');
}
```

Always compute the HMAC from the raw request body bytes before JSON parsing. Parsing and re-serializing the body can change whitespace and invalidate the signature check.

## Building an Idempotent Handler

Your webhook handler should follow this pattern:

1. Verify the signature (reject immediately if invalid).
2. Check your database for the event ID (`event.id` field): if already processed, return HTTP 200 immediately without re-executing business logic.
3. Execute business logic (update order status, trigger fulfillment, send customer email).
4. Record the event ID as processed in your database within the same transaction as the business logic update.
5. Return HTTP 200. Any non-2xx response or timeout causes the platform to retry the delivery.

Keep your handler fast: respond within 30 seconds. For time-consuming operations, enqueue the work and return 200 immediately.

## Handling Retries and Failures

The platform retries unacknowledged deliveries with exponential backoff for up to 72 hours. To avoid processing a backlog of old events after a handler outage:

- Use the event `created` timestamp to decide whether to process or skip stale events
- Implement a dead-letter mechanism for events that fail processing after multiple retries
- Monitor webhook delivery success rates in the merchant dashboard

## Testing Your Webhook Handler

Use the sandbox webhook simulator in the developer portal to replay specific event types to your local or staging endpoint. Ensure your handler correctly processes all required event types and returns 200 within the timeout. Test both the happy path and error scenarios where your business logic fails after the event is received.
