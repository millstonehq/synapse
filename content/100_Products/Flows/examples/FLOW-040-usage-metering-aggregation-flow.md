---
id: FLOW-040
type: flow
title: Usage Metering Aggregation Flow
status: deprecated
owner: QA Engineer
created: '2024-03-02T12:45:39.800Z'
updated: '2026-02-09T11:45:25.775Z'
tags:
  - flow
  - billing-engine
summary: Usage Metering Aggregation Flow
feature_area: Billing Engine
related_prds:
  - PRD-049
example: true
---

## Steps

### Step 1: Usage Event Ingestion

Product services emit usage events to the Usage Metering Service ingest API (`POST /v1/usage/events`) as actions occur in real time. Each event includes a `customer_id`, `metric_name` (e.g., `api_calls`, `active_seats`, `records_processed`), `quantity`, `event_time`, and an `idempotency_key`. The ingest API validates the idempotency key against the `usage_events` table and rejects duplicates with a 200 response (idempotent no-op). Valid events are persisted to the SQL Server `usage_events` table and the API returns HTTP 202 to the caller. This flow supports the Billing Admin Console ([[PRD-049|PRD-049]]) usage visibility features.

### Step 2: Hourly Partial Aggregation

Every hour, the Hourly Aggregator worker queries the `usage_events` table for all events with `event_time` in the completed hour. For each `(customer_id, metric_name, hour)` tuple, it computes partial aggregates: SUM of quantities, MAX quantity, COUNT of events, and LAST value by event_time. The resulting partial aggregate row is upserted into the `usage_hourly_aggregates` table. The upsert is idempotent — re-running the hourly aggregation for the same hour produces the same result.

### Step 3: Dashboard Refresh (Near-Real-Time Path)

The Usage Dashboard queries the aggregation API (`GET /v1/usage/customers/{id}/current`) to display current-period usage. The API reads from the `usage_hourly_aggregates` table, sums all completed hours in the current billing period, and adds a partial estimate for the in-progress current hour using the raw `usage_events` inserted since the last hourly aggregation ran. The result is cached in Redis with a 15-minute TTL. Dashboard staleness is bounded to 2 hours in the worst case (hourly aggregation lag + cache TTL).

### Step 4: Billing Period Finalization

When the Invoice Pipeline requests final billable quantities for a closing billing period, the aggregation API applies the metric-specific aggregation function across all hourly partial aggregates for the period: SUM for API calls and records (consumable), MAX for active seats (capacity), and LAST for storage GB (snapshot). The final billing period aggregate is written to `billing_period_aggregates` and locked as immutable. Any usage events for this period that arrive after the 30-minute late acceptance window are rejected.

## Expected Results

- All usage events are persisted within 1 second of receipt by the ingest API
- Hourly partial aggregates are computed and available within 5 minutes of the hour ending
- Dashboard usage data is no more than 2 hours stale
- Final billing period aggregates are accurate to within the 30-minute late event window
- Duplicate events (same idempotency key) are silently deduplicated with no effect on aggregate values

## User Info

| Field | Value |
|-------|-------|
| Role | Product service (emitting events) / Billing Engine (reading aggregates) |
| Permissions | Internal service-to-service; write requires usage:ingest scope, read requires usage:read scope |
| Test environment | Staging Usage Metering Service with SQL Server test instance |
| Test metric | `api_calls` metric with test customer `test-usage-001` |
| Environment | Staging |
