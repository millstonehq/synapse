---
id: TDD-004
type: tdd
title: Multi-Currency Support TDD
status: accepted
owner: Senior Engineer
created: '2025-07-28T01:43:33.450Z'
updated: '2025-01-24T22:22:39.221Z'
tags:
  - tdd
  - payment-processing
summary: Multi-Currency Support TDD
related_adrs:
  - ADR-0004
  - ADR-0003
example: true
---

## Summary

Design the multi-currency support layer that enables the payment platform to accept, process, and report on payments in currencies other than USD. The platform must support the 30 most commonly used ISO 4217 currencies, integrate with an FX rate provider for settlement currency conversion, store original and converted amounts separately for audit purposes, and correctly handle zero-decimal currencies (JPY, KRW). This TDD relates to decisions in [[ADR-0004|Implement Idempotent Payment API]] and [[ADR-0003|Use Event Sourcing for Transaction Ledger]].

## Overview

Multi-currency support is delivered as an extension to the existing `Money` value object and a new `CurrencyService` that manages FX rate caching. The payment schema gains two new fields (`settlement_amount`, `settlement_currency`) to record the USD equivalent at time of authorization, required for financial reconciliation.

Key design principles:
- **Immutable rates at authorization time**: The FX rate applied at authorization is stored on the payment record and never updated, even if the rate changes before capture.
- **Five-minute rate cache**: FX rates are cached in Redis with a 5-minute TTL. Brief provider outages do not block payments.
- **Zero-decimal currency handling**: Currencies like JPY store amounts as whole integers (¥1500, not ¥15.00). The `Money` value object enforces this based on ISO 4217 decimal place definitions.
- **Currency allowlist**: Only the 30 supported currencies are accepted at the API layer. Unknown currencies return 422 Unprocessable Entity.

## Architecture

### Component Diagram

The currency layer adds a new `CurrencyService` component:

- **HTTP Handler Layer**: Validates `currency` field against the supported currency list
- **CurrencyService**: Fetches FX rates from the provider, caches in Redis, exposes `Convert(from, to, amount)` and `GetRate(from, to)` methods
- **Use Case Layer**: Calls `CurrencyService.Convert` during authorization to store settlement amount; passes original currency to gateway
- **FX Rate Provider**: External API (Fixer.io) polled every 5 minutes; 5-minute stale rates are acceptable for this use case

### Supported Currencies (initial 30)

USD, EUR, GBP, CAD, AUD, JPY, CHF, SEK, NOK, DKK, NZD, SGD, HKD, MXN, BRL, INR, KRW, ZAR, AED, PLN, THB, IDR, MYR, PHP, CZK, HUF, ILS, SAR, TRY, TWD.

## Information Model

### Core Entities

- **Money**: Enhanced value object. Fields: `amount_minor_units` (int64), `currency` (ISO 4217 string), `decimal_places` (int). Methods: `ToDisplayString()`, `ToMinorUnits()`, `FromMinorUnits()`.
- **FXRate**: Cached rate entry. Fields: `from_currency`, `to_currency`, `rate` (decimal), `fetched_at`, `expires_at`.

### Database Schema Changes

New columns on `payments` table:
- `settlement_amount` (int64, nullable) — USD minor units at authorization time
- `settlement_currency` (char(3), default 'USD') — settlement currency code
- `fx_rate` (numeric(18,8), nullable) — exchange rate applied at authorization

## Interfaces

### CurrencyService

```go
type CurrencyService interface {
    Convert(ctx context.Context, amount Money, toCurrency string) (Money, Rate, error)
    GetRate(ctx context.Context, from, to string) (Rate, error)
    IsSupported(currency string) bool
}
```

### Updated Authorize Request

```json
{
  "amount": 1500,
  "currency": "EUR",
  "idempotency_key": "uuid-v4",
  "payment_method_id": "pm_xxx"
}
```

## Files and Layout

```
internal/
  currency/
    service.go           - CurrencyService implementation
    cache.go             - Redis FX rate cache
    money.go             - Enhanced Money value object
    allowlist.go         - Supported currency list and decimal place config
    service_test.go
  usecase/
    authorize.go         - Updated to call CurrencyService for settlement amount
migrations/
  0010_add_settlement_columns.sql
```

## Work Plan

1. **Phase 1 (Week 1)**: Enhanced `Money` value object with zero-decimal handling; currency allowlist and validation middleware
2. **Phase 2 (Week 2)**: `CurrencyService` with FX rate provider integration, Redis caching, and fallback for brief provider outages
3. **Phase 3 (Week 3)**: Database migration for settlement columns; updated `AuthorizeUseCase` to populate settlement amount
4. **Phase 4 (Week 4)**: End-to-end tests across 5 representative currencies including JPY; canary rollout configuration

## Risks and Mitigations

- **Risk**: FX rate provider outage blocks all non-USD payments. **Mitigation**: 5-minute Redis cache means short outages are transparent. If the cache expires during a provider outage, fall back to the last known rate with a staleness warning logged — do not fail the transaction.
- **Risk**: Zero-decimal currency bugs cause fractional amounts to be passed to gateways. **Mitigation**: `Money` value object enforces minor-unit storage by currency; integration tests include JPY test cases.
- **Risk**: Settlement amount calculated at authorization time diverges from actual settlement amount if rates change significantly before capture. **Mitigation**: This is acceptable and documented; settlement reporting uses actual gateway settlement data, not the stored estimate.

## Operations

- **Deployment**: Multi-currency deployed via feature flag. Canary at 10% of traffic for 1 week before full rollout.
- **Monitoring**: `currency_conversion_total` by currency pair; `fx_rate_cache_miss_total` to detect provider issues; `fx_rate_staleness_seconds` histogram.
- **Alerting**: Alert if `fx_rate_staleness_seconds` p95 exceeds 10 minutes (cache not refreshing).
- **Rollback**: Feature flag disables multi-currency acceptance; existing payments in non-USD currencies are unaffected (already stored).
