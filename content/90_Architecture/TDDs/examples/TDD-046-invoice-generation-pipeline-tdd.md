---
id: TDD-046
type: tdd
title: Invoice Generation Pipeline TDD
status: draft
owner: Tech Lead
created: '2025-07-17T16:25:32.444Z'
updated: '2025-09-22T00:43:01.773Z'
tags:
  - tdd
  - billing-engine
summary: Invoice Generation Pipeline TDD
related_adrs:
  - ADR-0038
  - ADR-0039
example: true
---

## Summary

This TDD describes the design of the Invoice Generation Pipeline — the orchestration layer responsible for assembling, calculating, and emitting invoices at the end of each billing period. The pipeline consumes subscription and usage data, applies proration, requests tax calculation via Avalara, assembles line items, and publishes finalized invoices to the Billing Event Processor for downstream charging.

The design implements billing architecture decisions documented in [[ADR-0038|ADR-0038]] (Stripe Billing as payment backend) and [[ADR-0039|ADR-0039]] (usage-based pricing model). It is designed to process up to 10,000 invoices per hour at month-end billing runs while maintaining idempotency across retries.

## Overview

- **Pipeline trigger**: A scheduled job fires on billing period end and also on-demand for mid-cycle events (upgrades, cancellations)
- **Idempotency**: Each invoice generation attempt uses a `billing_run_id + subscription_id` composite key to prevent duplicate invoices under retry
- **Separation of concerns**: Tax calculation and PDF rendering are external calls; the pipeline orchestrates but does not implement them
- **Transactional safety**: Invoice assembly is written to PostgreSQL within a single transaction before being published to RabbitMQ

## Architecture

- **Invoice Scheduler**: Cron-triggered Go process that enqueues billing run jobs to RabbitMQ for each subscription due for invoicing
- **Invoice Worker**: Consumer that processes one subscription at a time — fetches usage aggregates, calculates proration, calls Tax Calculation Engine, assembles line items, and persists the draft invoice
- **Stripe Publisher**: Finalizes the invoice in Stripe via the Invoices API (as per [[ADR-0038|ADR-0038]]) and records the Stripe invoice ID
- **Billing Event Bus**: RabbitMQ exchange that distributes `invoice.finalized` events to downstream consumers (payment charging, notifications)

## Information Model

- **BillingRun**: `id`, `subscription_id`, `period_start`, `period_end`, `status` (queued/processing/complete/failed), `idempotency_key`, `created_at`
- **InvoiceLineItem**: `id`, `invoice_id`, `description`, `pricing_type` (flat/per_unit/tiered), `quantity`, `unit_price`, `amount`, `tax_amount`
- **Invoice**: `id`, `subscription_id`, `billing_run_id`, `stripe_invoice_id`, `subtotal`, `tax_total`, `total`, `status`, `period_start`, `period_end`, `created_at`
- **TaxResult**: `invoice_id`, `jurisdiction`, `tax_rate`, `tax_amount`, `avalara_doc_id`, `cached_at`

## Interfaces

- `POST /internal/v1/billing-runs` - Enqueue a billing run for a subscription (called by scheduler)
- `GET /internal/v1/billing-runs/{id}` - Retrieve billing run status and error details
- `POST /internal/v1/invoices/{id}/retry` - Re-queue a failed billing run for retry
- `GET /internal/v1/invoices/{id}` - Retrieve finalized invoice with line items

## Files and Layout

The pipeline is implemented as a module within the Billing Engine monorepo:

```
billing-engine/
  cmd/invoice-scheduler/main.go   - Scheduler entry point
  cmd/invoice-worker/main.go      - Worker entry point
  internal/invoice/
    scheduler.go                  - Period-end detection and job enqueue
    worker.go                     - Pipeline orchestration
    assembler.go                  - Line item assembly logic
    tax_client.go                 - Tax Calculation Engine HTTP client
    stripe_publisher.go           - Stripe Invoice API adapter
  internal/model/
    invoice.go                    - Invoice, BillingRun entities
    line_item.go                  - InvoiceLineItem entity
  migrations/
    0042_invoice_tables.sql
```

## Work Plan

1. **Phase 1 - Data model and migrations (Week 1)**: Create `billing_runs`, `invoices`, `invoice_line_items` tables with indexes; implement repository layer with idempotency key enforcement
2. **Phase 2 - Pipeline core (Week 2-3)**: Implement scheduler job enqueue, worker pipeline orchestration, line item assembler; unit test all calculation paths
3. **Phase 3 - Tax integration (Week 4)**: Integrate Tax Calculation Engine client; implement Redis cache layer for tax results; test with Avalara sandbox
4. **Phase 4 - Stripe publishing (Week 5)**: Implement Stripe Invoice creation and finalization; handle Stripe error cases (payment method missing, subscription cancelled)
5. **Phase 5 - End-to-end testing and load testing (Week 6)**: Integration tests for full pipeline; load test at 10,000 invoices/hour; tune worker concurrency

## Risks and Mitigations

- **Tax service latency spikes the pipeline**: Avalara P99 latency can reach 3s; mitigate by enforcing a 5s timeout per call and falling back to cached results within the TTL
- **Stripe rate limits at month-end burst**: Stripe Billing API is rate-limited; mitigate by distributing billing run scheduling across a 4-hour window rather than all at midnight
- **Duplicate invoices on retry**: Mitigate by enforcing a unique constraint on `(subscription_id, billing_run_id)` in the invoices table and returning the existing invoice on duplicate key violation
