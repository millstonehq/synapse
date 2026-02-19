---
id: WIKI-038
type: wiki
title: Invoice Generation - Pipeline Details
status: approved
owner: Billing Team
created: '2025-12-10T00:38:05.048Z'
updated: '2026-12-05T05:20:15.176Z'
tags:
  - wiki
  - billing-engine
summary: Invoice Generation - Pipeline Details
source_repo: https://git.example.com/acme/invoice-generation
commit_sha: 0d42feb53d829a3b7d2e5665c44dfb7990b905b1
generated_at: '2026-09-23T01:11:43.821Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: gpt-4
importance: high
example: true
---

## Overview

The invoice generation pipeline produces customer invoices at the end of each billing period. It is triggered by the Billing Event Processor upon receipt of a `billing_period.closed` event and runs as a batch job that processes subscriptions in configurable batch sizes. Each pipeline run reads usage aggregates, applies proration, calculates taxes, and produces a finalized invoice in both JSON and PDF formats.

This page was auto-generated from the `billing-engine` repository. For the original design, see the Invoice Generation Pipeline TDD (TDD-046).

## Pipeline Stages

The invoice generation pipeline executes the following stages in sequence for each subscription batch:

1. **Trigger**: Billing Event Processor emits `billing_period.closed` event with `{customer_id, billing_period_start, billing_period_end}`.
2. **Usage Fetch**: Pipeline queries the Usage Metering Service aggregation API for all metric types for the customer and period.
3. **Proration Calculation**: For subscriptions with mid-cycle changes (upgrades, downgrades, cancellations), the proration calculator computes the credited and charged amounts for each plan segment.
4. **Tax Calculation**: Line items are submitted to the Tax Calculation Engine, which returns per-jurisdiction tax amounts via Avalara.
5. **Invoice Assembly**: Line items, proration adjustments, and tax amounts are combined into the invoice data model.
6. **PDF Rendering**: The invoice is rendered to PDF using a templating engine, with customer branding applied from the tenant configuration.
7. **Storage and Delivery**: The finalized JSON and PDF artifacts are stored in S3, a database record is created, and a `invoice.finalized` event is published for downstream delivery (email, Stripe charge trigger).

## Key Packages

### `invoice/pipeline`

Orchestrates the full pipeline run. Handles batch partitioning and coordinates stage execution with error isolation — a failure for one subscription does not abort the batch.

Key types: `PipelineRunner`, `InvoiceBatch`, `StageResult`.

### `invoice/proration`

Implements day-based and second-based proration algorithms. Reads the subscription change log for the billing period and computes credit/charge line items for each plan segment.

Key function: `CalculateProration(changes []PlanChange, period BillingPeriod, mode ProrationMode) []LineItem`

### `invoice/tax`

Thin adapter over the Tax Calculation Engine REST API. Maps invoice line items to Avalara transaction lines and maps Avalara responses back to invoice tax lines.

### `invoice/renderer`

Generates PDF invoices using Go templates and a headless PDF library. Template selection is based on tenant configuration; a default template is used when no custom template is configured.

## Dependencies

| Component | Version | Purpose |
|-----------|---------|---------|
| Usage Metering Service | Internal | Provides aggregated usage quantities |
| Tax Calculation Engine | Internal | Provides per-jurisdiction tax amounts |
| Avalara AvaTax | v2 REST API | Underlying tax determination (via Tax Calculation Engine) |
| S3 | AWS SDK v2 | Invoice artifact storage |
| PostgreSQL | 16 | Invoice records and audit trail |

## Generation Notes

Generated from commit `0d42feb` on the `main` branch of the `invoice-generation` repository. Manual review is recommended for accuracy, particularly for the proration and tax adapter logic.
