---
id: TDD-050
type: tdd
title: Billing Webhook Processor TDD
status: review
owner: Principal Engineer
created: '2024-11-12T16:14:59.171Z'
updated: '2026-03-08T20:52:12.224Z'
tags:
  - tdd
  - billing-engine
summary: Billing Webhook Processor TDD
related_adrs:
  - ADR-0041
  - ADR-0040
example: true
---

## Summary

This TDD describes the design of the Billing Webhook Processor — the component responsible for receiving, verifying, and processing asynchronous webhook events from Stripe. Stripe webhooks are the mechanism through which Stripe notifies the Billing Engine of payment outcomes (charge succeeded/failed), subscription state changes, and dispute events. The processor must translate these external events into internal domain events and update the double-entry financial ledger as specified in [[ADR-0041|ADR-0041]] (Avalara tax compliance) and [[ADR-0040|ADR-0040]] (double-entry bookkeeping) for applicable events such as payment confirmations and refunds.

The processor must handle webhook delivery guarantees: Stripe delivers webhooks at-least-once and retries for up to 3 days on non-2xx responses. The processor must therefore be idempotent on all event types.

## Overview

- **Signature verification**: Every incoming webhook payload is verified against the Stripe-Signature header using the endpoint's signing secret before any processing occurs
- **Idempotent processing**: Events are keyed by Stripe event ID; duplicate delivery of the same event ID is a no-op returning HTTP 200
- **Async processing**: The HTTP endpoint acknowledges receipt with 200 immediately and enqueues the event for background processing; this prevents Stripe from treating slow downstream processing as a failure
- **Ledger integration**: Payment confirmation and refund events trigger double-entry ledger entries per [[ADR-0040|ADR-0040]]

## Architecture

- **WebhookReceiver**: Thin HTTP handler that verifies signature, stores the raw event payload to the `webhook_events` table, and enqueues the event ID to RabbitMQ — returns 200 immediately
- **WebhookWorker**: RabbitMQ consumer that retrieves the full event payload, routes it to the appropriate event handler, and marks the event as processed on success
- **EventRouter**: Dispatches events to typed handlers based on `event.type` (e.g., `invoice.payment_succeeded`, `charge.refunded`, `customer.subscription.deleted`)
- **LedgerEntryWriter**: Called by payment-related event handlers to write balanced debit/credit entries to the financial ledger

## Information Model

- **WebhookEvent**: `id`, `stripe_event_id`, `event_type`, `payload` (JSON), `status` (received/processing/processed/failed), `processing_attempts`, `received_at`, `processed_at`
- **WebhookProcessingError**: `webhook_event_id`, `error_message`, `stack_trace`, `occurred_at` (for dead letter analysis)
- **LedgerEntry**: `id`, `webhook_event_id`, `account_type`, `debit_cents`, `credit_cents`, `currency`, `description`, `created_at`

## Interfaces

- `POST /webhooks/stripe` - Stripe webhook delivery endpoint (public, signature-verified)
- `GET /internal/v1/webhook-events` - List webhook events with filtering by type and status (admin/ops use)
- `POST /internal/v1/webhook-events/{id}/retry` - Re-queue a failed webhook event for reprocessing

## Files and Layout

```
billing-event-processor/
  internal/webhook/
    receiver.go            - HTTP handler: signature verify, store, enqueue
    worker.go              - RabbitMQ consumer, event routing
    router.go              - Event type to handler dispatch
    handlers/
      invoice_paid.go      - invoice.payment_succeeded handler
      charge_refunded.go   - charge.refunded handler
      subscription_del.go  - customer.subscription.deleted handler
    ledger_writer.go       - Double-entry ledger entry creation
  internal/model/
    webhook_event.go
  migrations/
    0025_webhook_events.sql
```

## Work Plan

1. **Phase 1 - Receiver and storage (Week 1)**: Implement HTTP endpoint with Stripe signature verification; persist raw event to `webhook_events` table; unit test with Stripe test payloads
2. **Phase 2 - Async worker and routing (Week 2)**: Implement RabbitMQ consumer; implement event router; verify idempotency for duplicate event IDs; integration test with RabbitMQ test container
3. **Phase 3 - Payment and refund handlers (Week 3)**: Implement `invoice.payment_succeeded` and `charge.refunded` handlers with ledger entry creation; verify ledger balance invariant after each handler
4. **Phase 4 - Subscription event handlers (Week 4)**: Implement subscription deletion and update handlers; test against subscription state machine integration
5. **Phase 5 - Dead letter handling and observability (Week 5)**: Implement failed event DLQ; add metrics for event processing lag, handler error rate, and DLQ depth; set up alerting rules

## Risks and Mitigations

- **Webhook replay attack**: A malicious actor replaying old webhook payloads could trigger duplicate ledger entries; mitigate by verifying the Stripe-Signature timestamp is within 5 minutes of current time, rejecting stale events
- **Handler failure after ledger write**: If the handler writes ledger entries but then fails before marking the event as processed, replay will attempt to write ledger entries again; mitigate by wrapping ledger write and event status update in a single database transaction
- **Stripe event schema changes**: Stripe occasionally adds fields to webhook payloads; mitigate by using lenient JSON deserialization and only accessing explicitly needed fields rather than strict schema validation
