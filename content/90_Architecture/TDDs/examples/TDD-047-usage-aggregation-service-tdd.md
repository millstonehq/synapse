---
id: TDD-047
type: tdd
title: Usage Aggregation Service TDD
status: accepted
owner: Senior Engineer
created: '2025-05-29T12:30:27.063Z'
updated: '2025-06-29T03:14:38.704Z'
tags:
  - tdd
  - billing-engine
summary: Usage Aggregation Service TDD
related_adrs:
  - ADR-0038
  - ADR-0039
example: true
---

## Summary

This TDD describes the design of the Usage Aggregation Service — the component within the Usage Metering Service responsible for transforming raw usage events into billable quantities for each customer's billing period. Aggregation must produce accurate, tamper-evident quantities that feed directly into invoice line item calculation as required by [[ADR-0039|ADR-0039]] (usage-based pricing model) and are charged via Stripe Billing as decided in [[ADR-0038|ADR-0038]].

The service runs two aggregation modes: a continuous near-real-time aggregation that keeps customer usage dashboards current, and a billing-period aggregation that produces final billable quantities when an invoice run is triggered. Final quantities are immutable once the invoice is finalized.

## Overview

- **Aggregation functions**: Supports SUM (consumable metrics like API calls and records processed), MAX (capacity metrics like active seats), COUNT (distinct events), and LAST (snapshot metrics like storage GB at period end)
- **Two-phase aggregation**: Hourly partial aggregates are materialized continuously; billing-period final aggregates are computed on-demand from partial aggregates to avoid reprocessing all raw events
- **Immutability on finalization**: Once a billing run is finalized for a period, the aggregation record for that period is locked and cannot be modified
- **Late event handling**: Events arriving up to 30 minutes after the billing window closes are accepted and trigger aggregate recalculation; events older than 30 minutes are rejected with a 422 response

## Architecture

- **Raw Event Store**: SQL Server table `usage_events` with partitioning by `customer_id` and `event_date`; raw events are never mutated after insert
- **Hourly Aggregator**: Scheduled worker that groups raw events by `(customer_id, metric_name, hour)` and upserts partial aggregate rows into `usage_hourly_aggregates`
- **Billing Period Aggregator**: On-demand service called by the Invoice Pipeline; reads hourly partial aggregates and applies the metric-specific function (SUM/MAX/COUNT/LAST) to produce a single billable quantity per metric per period
- **Aggregation API**: REST API that exposes current-period usage for customer dashboards and returns final billable quantities for invoice generation

## Information Model

- **UsageEvent**: `id`, `customer_id`, `metric_name`, `quantity`, `event_time`, `source`, `idempotency_key`, `received_at`
- **UsageHourlyAggregate**: `customer_id`, `metric_name`, `hour`, `partial_sum`, `partial_max`, `partial_count`, `last_value`, `event_count`, `computed_at`
- **BillingPeriodAggregate**: `id`, `customer_id`, `metric_name`, `period_start`, `period_end`, `aggregation_function`, `billable_quantity`, `finalized_at`

## Interfaces

- `POST /v1/usage/events` - Ingest a single usage event (called by product services)
- `POST /v1/usage/events/batch` - Ingest a batch of up to 1,000 events
- `GET /v1/usage/customers/{id}/current` - Current-period usage by metric for customer dashboard
- `GET /v1/usage/customers/{id}/period` - Final billable quantities for a closed billing period (called by Invoice Pipeline)

## Files and Layout

```
usage-metering-service/
  cmd/api/main.go                - Ingest API entry point
  cmd/aggregator/main.go         - Hourly aggregator worker
  internal/aggregation/
    hourly.go                    - Hourly partial aggregate logic
    billing_period.go            - Billing-period final aggregate logic
    functions.go                 - SUM / MAX / COUNT / LAST implementations
  internal/store/
    event_store.go               - Raw event persistence (SQL Server)
    aggregate_store.go           - Aggregate table read/write
  migrations/
    0018_usage_aggregates.sql
```

## Work Plan

1. **Phase 1 - Event store and ingest API (Week 1-2)**: Design `usage_events` table schema with partitioning; implement ingest API with idempotency key enforcement; unit test duplicate rejection
2. **Phase 2 - Hourly aggregator (Week 3)**: Implement scheduled worker; implement SUM/MAX/COUNT/LAST aggregation functions; property-based tests for aggregation correctness
3. **Phase 3 - Billing period aggregator (Week 4)**: Implement on-demand billing period aggregation from hourly partials; implement immutability lock on finalization
4. **Phase 4 - Late event handling (Week 5)**: Implement 30-minute late acceptance window; implement aggregate recalculation on late event arrival; test recalculation correctness
5. **Phase 5 - Load and accuracy testing (Week 6)**: Load test at 50,000 events/minute; validate aggregate accuracy against hand-calculated results for all four aggregation functions

## Risks and Mitigations

- **Aggregate drift from late events**: If events arrive after the 30-minute window, they are silently dropped and the finalized billing quantity may be understated; mitigate by logging all rejected late events and alerting if late rejection rate exceeds 0.1%
- **Hourly aggregator falling behind during spikes**: If the aggregator cannot keep up, dashboard usage data becomes stale; mitigate by running multiple aggregator replicas with partition-based sharding
- **Billing period aggregate does not match raw event sum**: Property-based tests must verify that aggregating hourly partials produces the same result as aggregating raw events directly for the SUM function
