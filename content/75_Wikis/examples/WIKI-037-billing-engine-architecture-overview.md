---
id: WIKI-037
type: wiki
title: Billing Engine - Architecture Overview
status: draft
owner: Billing Team
created: '2024-09-09T21:09:02.193Z'
updated: '2025-03-19T06:35:52.429Z'
tags:
  - wiki
  - billing-engine
summary: Billing Engine - Architecture Overview
source_repo: https://git.example.com/acme/billing-engine
commit_sha: 4ab903a1a5584811c4ec87511ddd74c51519fc7e
generated_at: '2026-04-11T05:54:32.876Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: gpt-4o
importance: medium
example: true
---

## Overview

The Billing Engine is the platform responsible for all revenue operations at Acme: usage metering, subscription lifecycle management, tax calculation, invoice generation, and payment event routing. It is composed of four primary microservices that communicate via event-driven interfaces, with Stripe Billing as the external payment backend.

This wiki provides an architectural overview of the full Billing Engine. For individual service details, refer to the system documentation for each component. For the original design rationale, see the ADRs linked in the related systems.

## Architecture

The Billing Engine follows an event-driven microservices architecture with clear ownership boundaries:

- **Usage Metering Service**: Ingests raw usage events from all product surfaces and produces aggregated usage records by customer and billing period. Acts as the upstream data source for invoice generation.
- **Subscription Management Service**: Owns subscription state transitions (trial → active → past_due → cancelled). Publishes state change and renewal events to the Billing Event Processor.
- **Tax Calculation Engine**: Computes applicable taxes on billable amounts using Avalara AvaTax. Caches results in Redis to minimize API call volume and meet latency targets.
- **Billing Event Processor**: Central routing hub. Consumes events from all billing services via RabbitMQ and dispatches them to downstream handlers (invoice generation, ledger entries, notifications).

## Key Components

- **Stripe Billing**: External payment backend for charge execution, payment method storage, and webhook delivery. Selected per ADR-0038.
- **Avalara AvaTax**: External tax determination API. Handles multi-jurisdiction tax logic (US sales tax, VAT, GST). Selected per ADR-0041.
- **RabbitMQ**: Internal event bus for billing domain events. Provides durable, ordered, at-least-once delivery with dead letter queue support.
- **ClickHouse**: Analytical datastore for subscription state and usage aggregation, supporting high write throughput and efficient time-range queries.
- **Invoice Generation Pipeline**: Background job triggered by the Billing Event Processor at billing period close. Reads aggregated usage and subscription data, applies proration and tax, and produces PDF and JSON invoice artifacts.

## Data Flow

Events flow through the system in a consistent pattern: usage events are ingested by the Usage Metering Service → aggregated → published to the Billing Event Processor → routed to invoice generation and ledger services → invoices are sent to Stripe for charge execution → payment status webhooks are received and processed back through the event pipeline.

The Subscription Management Service operates in parallel: it consumes scheduled renewal events from Kafka, triggers billing period close, and publishes subscription state changes that the Billing Event Processor routes to invoice generation.

## Configuration

Key configuration parameters that affect system behavior:

- `BILLING_PERIOD_CLOSE_OFFSET_MINUTES`: How many minutes after midnight UTC the billing period close job runs (default: 30)
- `PRORATION_MODE`: `day` (default) or `second` — controls granularity of mid-cycle proration calculations
- `TAX_CACHE_TTL_SECONDS`: Redis TTL for Avalara result cache (default: 3600)
- `INVOICE_GENERATION_BATCH_SIZE`: Number of subscriptions processed per invoice generation batch (default: 500)

## Dependencies

| Service | Role | Protocol |
|---------|------|----------|
| Stripe Billing API | Payment execution and webhook source | REST / webhooks |
| Avalara AvaTax API | Tax determination | REST |
| RabbitMQ 3.13 | Internal event bus | AMQP |
| Kafka 3.x | Subscription renewal scheduling | Kafka protocol |
| ClickHouse | Usage and subscription analytics store | HTTP / native |
