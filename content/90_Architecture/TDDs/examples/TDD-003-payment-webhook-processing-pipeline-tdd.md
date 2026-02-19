---
id: TDD-003
type: tdd
title: Payment Webhook Processing Pipeline TDD
status: draft
owner: Principal Engineer
created: '2024-06-21T06:09:22.471Z'
updated: '2026-09-18T04:04:14.797Z'
tags:
  - tdd
  - payment-processing
summary: Payment Webhook Processing Pipeline TDD
related_adrs:
  - ADR-0003
  - ADR-0005
example: true
---

## Summary

Design a webhook processing pipeline that reliably ingests, validates, deduplicates, and processes asynchronous payment lifecycle events from Stripe and PayPal. The pipeline must handle burst volumes (up to 14,000 events in 20 minutes during gateway backfills), guarantee at-least-once processing, and emit structured events to the internal SQS topic for downstream consumers. This TDD supports the event-sourcing approach in [[ADR-0003|Use Event Sourcing for Transaction Ledger]] and the PostgreSQL data store decision in [[ADR-0005|Choose PostgreSQL for Payment Data Store]].

## Overview

The webhook processing pipeline is implemented as a Python 3.12 service (the Payment Webhook Dispatcher) that consumes from an SQS FIFO queue. Stripe and PayPal deliver webhook events to the `/webhooks/stripe` and `/webhooks/paypal` HTTPS endpoints respectively, which immediately enqueue them to SQS after signature verification. The dispatcher workers then process events asynchronously.

Key design principles:
- **Signature verification first**: HMAC-SHA256 signature validation occurs at the HTTP ingestion layer before any processing. Invalid signatures return 400 with no side effects.
- **Deduplication via event ID**: Each gateway event has a unique ID. The dispatcher stores processed event IDs in Redis with a 72-hour TTL. Duplicate deliveries are ACKed without reprocessing.
- **Ordered processing per payment**: SQS FIFO with `payment_id` as the message group key ensures events for a single payment are processed in delivery order.
- **Dead letter queue**: After 3 failed processing attempts, events are moved to the DLQ. DLQ events trigger a PagerDuty alert for manual investigation.

## Architecture

### Component Diagram

The pipeline has three stages:

- **Ingestion Layer**: HTTP endpoint validates gateway signature, enqueues raw event to SQS FIFO, returns 200 immediately
- **Processing Layer**: Dispatcher workers poll SQS FIFO, deduplicate via Redis, translate gateway event to internal domain event, update payment state in PostgreSQL
- **Fanout Layer**: Dispatcher publishes internal payment events to SQS Standard for downstream consumers (notifications, analytics, ledger)

### Event Type Mapping

- `payment_intent.succeeded` (Stripe) / `PAYMENT.CAPTURE.COMPLETED` (PayPal) → `payment.captured`
- `payment_intent.payment_failed` (Stripe) / `PAYMENT.CAPTURE.DENIED` (PayPal) → `payment.failed`
- `charge.refunded` (Stripe) / `PAYMENT.CAPTURE.REFUNDED` (PayPal) → `payment.refunded`
- `charge.dispute.created` (Stripe) / `CUSTOMER.DISPUTE.CREATED` (PayPal) → `payment.disputed`

## Information Model

### Core Entities

- **WebhookEvent**: Persisted after successful processing. Fields: `id`, `gateway`, `gateway_event_id`, `event_type`, `payment_id`, `raw_payload`, `processed_at`
- **WebhookDeadLetter**: Events that exceeded retry limit. Fields: `id`, `gateway_event_id`, `failure_reason`, `attempt_count`, `last_attempted_at`

### Database Schema

- `webhook_events` table: unique constraint on `(gateway, gateway_event_id)` for deduplication; index on `payment_id` for reconciliation queries
- `webhook_dead_letters` table: used by on-call for manual investigation and replay

## Interfaces

### Ingestion HTTP Handler

- `POST /webhooks/stripe` - Stripe webhook delivery endpoint (header: `Stripe-Signature`)
- `POST /webhooks/paypal` - PayPal webhook delivery endpoint (header: `PayPal-Transmission-Sig`)

### SQS Message Schema

```json
{
  "gateway": "stripe",
  "gateway_event_id": "evt_1234",
  "event_type": "payment_intent.succeeded",
  "payment_id": "pay_abc123",
  "raw_payload": "...",
  "received_at": "2025-03-15T10:32:00Z"
}
```

## Files and Layout

```
cmd/dispatcher/main.py         - Entry point, worker pool startup
dispatcher/
  ingestion/
    stripe_handler.py          - Stripe signature verification + enqueue
    paypal_handler.py          - PayPal signature verification + enqueue
  processing/
    worker.py                  - SQS consumer, deduplication, state update
    event_translator.py        - Gateway event → internal domain event
    deduplicator.py            - Redis-based event ID deduplication
  fanout/
    publisher.py               - Publish internal events to downstream SQS
tests/
  test_deduplicator.py
  test_event_translator.py
  test_worker.py
```

## Work Plan

1. **Phase 1 (Week 1-2)**: Ingestion layer — HMAC signature verification for Stripe, SQS FIFO enqueue, integration tests against Stripe test webhooks
2. **Phase 2 (Week 2-3)**: Deduplication layer — Redis event ID store, TTL management, unit tests for concurrent duplicate delivery
3. **Phase 3 (Week 3-4)**: Processing layer — event translator, payment state update, PostgreSQL transaction wrapping event record + state change
4. **Phase 4 (Week 4)**: PayPal ingestion, fanout publisher, DLQ alerting, load test simulating 14,000-event burst

## Risks and Mitigations

- **Risk**: Burst volume (gateway backfill) overwhelms dispatcher workers. **Mitigation**: SQS FIFO queue acts as a buffer. Auto-scale worker count on SQS queue depth metric. Tested to 14,000 events/20 minutes in load testing.
- **Risk**: Signature verification secret rotation causes dropped webhooks during the rotation window. **Mitigation**: Stripe supports dual-secret validation for 72 hours during rotation. Implement dual-secret support in the handler.
- **Risk**: Deduplication TTL shorter than gateway retry window causes reprocessing of legitimate duplicates. **Mitigation**: 72-hour TTL exceeds Stripe's 72-hour webhook retry window by design.

## Operations

- **Deployment**: ECS Fargate task with 2-8 worker replicas auto-scaled on SQS queue depth.
- **Monitoring**: `webhook_processed_total` by gateway and event type; `webhook_dedup_hit_total` to track duplicate rate; `dlq_depth` alerts at > 10 messages.
- **Alerting**: DLQ depth > 10 triggers PagerDuty. Processing lag > 5 minutes on the main queue triggers a warning alert.
- **Rollback**: New worker image deployed via ECS rolling update. Previous task definition retained for immediate rollback.
