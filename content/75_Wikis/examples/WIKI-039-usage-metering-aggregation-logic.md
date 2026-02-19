---
id: WIKI-039
type: wiki
title: Usage Metering - Aggregation Logic
status: approved
owner: Billing Team
created: '2025-05-25T16:45:38.559Z'
updated: '2026-03-28T21:48:23.541Z'
tags:
  - wiki
  - billing-engine
summary: Usage Metering - Aggregation Logic
source_repo: https://git.example.com/acme/usage-metering
commit_sha: e0be3a2e61ea79d673ff772c78991ba5965f93c4
generated_at: '2025-01-16T08:09:19.737Z'
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
importance: low
example: true
---

## Overview

The Usage Metering aggregation system transforms high-volume raw usage events into queryable aggregated records by customer, metric type, and time window. Aggregation runs continuously and is the primary input for invoice line-item generation. This page documents the aggregation logic, supported functions, windowing behavior, and edge cases.

This page was auto-generated from commit `e0be3a2` of the `usage-metering` repository. See the Usage Metering Service system doc (SYSTEM-047) for operational details.

## Aggregation Windows

The aggregation engine produces three window sizes for each metric type:

- **Hourly**: Computed every 5 minutes for the trailing hour. Used for real-time usage dashboards.
- **Daily**: Computed every 30 minutes for the current calendar day (UTC). Used for daily usage reports.
- **Billing Period**: Computed continuously for the current open billing period. This is the authoritative aggregate used for invoice generation. Finalized when the billing period closes.

Each window is stored as a separate row in the `usage_aggregates` table, partitioned by `(customer_id, metric_id, window_type, window_start)`.

## Aggregation Functions

Metric types declare their aggregation function at registration time:

- **SUM**: Used for countable consumption metrics (e.g., API calls, messages sent, storage writes). The billing period aggregate is the sum of all events in the period.
- **MAX**: Used for high-water-mark metrics (e.g., peak active seats, peak storage GB). The billing period aggregate is the maximum observed value across all hourly windows.
- **COUNT**: Used for discrete event metrics (e.g., unique file uploads, unique report exports). Equivalent to SUM over event counts.
- **LAST**: Used for snapshot metrics (e.g., current seat count). The billing period aggregate is the value of the last event received before period close.

## Key Packages

### `internal/aggregator`

Core aggregation engine. Runs SQL Server 2022 windowed queries against the `usage_events` table using `OVER (PARTITION BY customer_id, metric_id ORDER BY event_time ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)` patterns.

Key entry point: `AggregationWorker.Run(ctx, window WindowType)` — continuously processes pending events and upserts aggregate rows.

### `internal/eventstore`

Manages raw event ingestion and storage. Events are written to the `usage_events` table with a composite unique constraint on `(customer_id, metric_id, event_time, idempotency_key)` to prevent duplicate ingestion.

### `internal/query`

Read API for aggregated usage data. Accepts `{customer_id, metric_id, window_type, start, end}` and returns aggregate rows. Used by the invoice pipeline and the Usage Dashboard.

## Edge Cases

- **Late-arriving events**: Events arriving after the billing period close are applied to the next period. A `late_event` flag is set on the event for audit purposes.
- **Metric deregistration**: If a metric type is deregistered mid-period, existing events continue to aggregate until period close. No new events are accepted after deregistration.
- **Customer deletion**: Aggregates are retained per data retention policy (7 years) even after customer account deletion.

## Generation Notes

Generated from commit `e0be3a2` on the `main` branch of the `usage-metering` repository. The generator analyzed SQL Server query patterns, aggregation worker logic, and the event schema to produce this overview.
