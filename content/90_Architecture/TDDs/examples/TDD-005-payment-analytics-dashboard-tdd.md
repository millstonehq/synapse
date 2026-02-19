---
id: TDD-005
type: tdd
title: Payment Analytics Dashboard TDD
status: approved
owner: Principal Engineer
created: '2025-02-18T19:16:22.617Z'
updated: '2025-12-22T17:12:01.030Z'
tags:
  - tdd
  - payment-processing
summary: Payment Analytics Dashboard TDD
related_adrs:
  - ADR-0004
  - ADR-0003
example: true
---

## Summary

Design a payment analytics dashboard that provides the finance and payments engineering teams with real-time and historical visibility into transaction volume, success rates, revenue, and gateway performance. The dashboard reads from a dedicated analytics replica to avoid impacting the primary payment database. It must load the overview page within 3 seconds for the last 30 days of data at current volume (~1.5M transactions/month). This TDD depends on the event sourcing design in [[ADR-0003|Use Event Sourcing for Transaction Ledger]] and the idempotency implementation in [[ADR-0004|Implement Idempotent Payment API]].

## Overview

The analytics dashboard is a React single-page application backed by a dedicated read API that queries the PostgreSQL analytics replica. Pre-aggregated summary tables are maintained by a nightly batch job to support fast queries on rolling time windows.

Key design principles:
- **Replica reads**: All analytics queries run on the PostgreSQL read replica, never on the primary. Connection pool is separate from the transactional pool.
- **Pre-aggregation**: Nightly batch job materializes daily summary rows into `payment_daily_stats` and `gateway_daily_stats`. Point-in-time queries join pre-aggregated data with same-day raw data for recency.
- **Finance-first metrics**: Primary metrics are revenue-centric (GMV, refund rate, chargeback rate). Engineering metrics (latency, error rate) are secondary and sourced from Grafana, not this dashboard.
- **Role-based access**: Finance users see revenue and refund data. Engineering users see gateway performance. Neither group has access to raw customer PII.

## Architecture

### Component Diagram

- **React SPA**: Deployed to S3/CloudFront, authenticated via JWT. Calls analytics API endpoints.
- **Analytics API**: Go service on Kubernetes, read-only. Queries analytics replica. Returns pre-aggregated JSON.
- **PostgreSQL Analytics Replica**: Streaming replica of the primary. Connection pool max 20 (analytics is read-only, low concurrency).
- **Nightly Batch Aggregator**: AWS Lambda, runs at 02:00 UTC. Populates `payment_daily_stats` and `gateway_daily_stats`.

### Dashboard Panels

- **GMV (last 30 days)**: Source `payment_daily_stats` + same-day raw, refreshed every 5 min
- **Authorization success rate**: Source `gateway_daily_stats`, refreshed every 5 min
- **Refund rate by day**: Source `payment_daily_stats`, refreshed every 5 min
- **Gateway comparison**: Source `gateway_daily_stats`, refreshed every 5 min
- **Fraud rate trend**: Source `payment_daily_stats`, refreshed every 1 hour

## Information Model

### Core Entities

- **PaymentDailyStats**: Pre-aggregated summary. Fields: `date`, `total_authorizations`, `successful_authorizations`, `total_gmv_usd`, `total_refunds`, `refund_amount_usd`, `fraud_count`
- **GatewayDailyStats**: Gateway performance summary. Fields: `date`, `gateway`, `authorizations`, `successes`, `failures`, `avg_latency_ms`, `p95_latency_ms`

### Database Schema

- `payment_daily_stats`: primary key `date`; populated by nightly batch
- `gateway_daily_stats`: composite primary key `(date, gateway)`; populated by nightly batch
- Both tables are on the analytics replica only (not replicated back)

## Interfaces

### Analytics API

- `GET /v1/analytics/summary?from=DATE&to=DATE` — GMV, authorization rate, refund rate for date range
- `GET /v1/analytics/gateways?from=DATE&to=DATE` — Gateway performance comparison
- `GET /v1/analytics/fraud?from=DATE&to=DATE` — Fraud rate trends (finance role only)

## Files and Layout

```
cmd/analytics-api/main.go      - Entry point
internal/
  analytics/
    handler.go                 - HTTP handlers for analytics endpoints
    repository.go              - Read-only PostgreSQL queries
    aggregator.go              - Nightly batch aggregation logic (also used by Lambda)
dashboard/
  src/
    App.tsx                    - Main dashboard layout
    panels/                    - Individual chart components
    api/                       - Analytics API client
```

## Work Plan

1. **Phase 1 (Week 1-2)**: Analytics replica connection pool, `payment_daily_stats` schema, nightly batch aggregator Lambda
2. **Phase 2 (Week 3)**: Analytics API endpoints with query performance validation (< 500ms for 30-day queries)
3. **Phase 3 (Week 4-5)**: React SPA with GMV, success rate, and refund rate panels
4. **Phase 4 (Week 6)**: Role-based access control, fraud rate panel, finance team UAT

## Risks and Mitigations

- **Risk**: Analytics queries on the read replica cause replica lag, delaying data freshness. **Mitigation**: Analytics replica is separate from the application read replica. Lag is acceptable up to 5 minutes; dashboard shows last-updated timestamp.
- **Risk**: Nightly batch failure leaves `payment_daily_stats` stale. **Mitigation**: Batch monitors output row count and alerts if it produces no rows. Dashboard falls back to real-time queries with a performance warning banner.
- **Risk**: PII exposure through analytics filters (e.g., filtering by customer email). **Mitigation**: Analytics API accepts only date ranges and dimension values (gateway, currency). No customer ID or email filtering is exposed.

## Operations

- **Deployment**: Analytics API deployed alongside payments-api in the same Kubernetes namespace, separate deployment.
- **Monitoring**: Analytics API request latency; batch job execution time and row count; replica lag metric.
- **Alerting**: Alert if nightly batch produces < 1000 rows for a date that is not today; alert if replica lag exceeds 10 minutes.
- **Rollback**: React SPA is versioned in S3; previous version can be restored by updating the CloudFront origin path.
