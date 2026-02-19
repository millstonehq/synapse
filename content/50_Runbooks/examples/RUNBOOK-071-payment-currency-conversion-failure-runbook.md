---
id: RUNBOOK-071
type: runbook
title: Payment Currency Conversion Failure Runbook
status: approved
owner: On-Call Engineer
created: '2024-07-28T04:08:50.032Z'
updated: '2026-10-10T03:30:09.779Z'
tags:
  - runbook
  - payment-processing
summary: Payment Currency Conversion Failure Runbook
example: true
---

## Service

- **System**: [[SYSTEM-001|Payment Gateway Service]]
- **Owner team**: Payments Engineering
- **On-call rotation**: PagerDuty schedule "payments-oncall"
- **Slack channel**: #payments-incidents
- **Runtime**: Kubernetes / Go 1.22 / PostgreSQL 16 / Redis 7

## Alerts

- `fx_rate_staleness_seconds_p95_high` - FX rate cache staleness exceeds 10 minutes (rates not refreshing from provider)
- `currency_conversion_error_rate_high` - Currency conversion error rate exceeds 2% for 5 minutes
- `fx_rate_provider_timeout` - FX rate provider API timeout for 2 consecutive fetches
- `non_usd_payment_failure_rate_high` - Non-USD payment failure rate exceeds 5% (potential currency handling bug)

## Diagnosis Steps

1. **Check if a recent deploy happened** - Look at #deployments channel and the ArgoCD dashboard. If the issue started within 30 minutes of a deploy, the deploy is the likely cause. Skip to Remediation Step 1 (rollback).
2. **Check FX rate cache freshness** - Run `redis-cli -h payments-redis GET "fx_rate:USD:EUR"` to check if the cache key exists, and `redis-cli -h payments-redis TTL "fx_rate:USD:EUR"` to check its TTL. A TTL of -2 means the key is expired. If most rate keys are expired, the cache is not being refreshed from the provider.
3. **Check FX rate provider connectivity** - In Kibana, filter by `service:payments-api` and `component:currency_service` for the last 15 minutes. Look for: connection timeout errors to the FX rate provider, authentication errors (API key may have expired), or provider HTTP 5xx responses.
4. **Check the FX rate provider status page** - The provider status page link is bookmarked in #payments-incidents. If the provider is having a confirmed outage, skip directly to Remediation Step 3.
5. **Check if the issue is isolated to a specific currency** - Filter error logs by `currency` field. If only one or two currencies are failing, this is likely a provider data gap or a zero-decimal currency handling bug (JPY, KRW) rather than a general provider outage.
6. **Check for zero-decimal currency amount errors** - Look for `invalid amount` or `amount must be positive integer` error patterns in logs filtered by `currency:JPY` or `currency:KRW`. These indicate the minor-unit conversion is producing a decimal value.

## Remediation Steps

1. **If caused by a recent deploy**: Roll back immediately via ArgoCD. Do not wait. Check the git diff for changes to `internal/currency/` or `internal/model/money.go`.
2. **If FX rate cache is expired (provider unreachable)**: The `CurrencyService` serves stale rates for up to 30 minutes automatically. Verify this is working by checking if non-USD payments are still processing. If the 30-minute grace period has expired and non-USD payments are failing, enable the USD-only fallback: `kubectl set env deployment/payments-api -n payments CURRENCY_FALLBACK_USD_ONLY=true`. This disables non-USD checkout until the provider recovers.
3. **If FX rate provider is down**: For outages under 30 minutes, stale rate serving handles it transparently with no action needed. For outages over 30 minutes, enable the USD-only fallback (see Step 2) and post a status update in #payments-incidents with an ETA from the provider's status page.
4. **If a specific currency is failing**: Check if the currency key exists in Redis. If missing and the provider is healthy, the currency may have been removed from the provider's data feed. Add the currency to the disable list: `kubectl set env deployment/payments-api -n payments CURRENCY_DISABLE_LIST=XYZ`. This prevents 5xx errors while the cause is investigated.
5. **If zero-decimal currency amounts are wrong (JPY/KRW)**: This is a code bug. Immediately disable the affected currencies: `kubectl set env deployment/payments-api -n payments CURRENCY_DISABLE_LIST=JPY,KRW`. File a P1 bug ticket and page the Payments tech lead.
6. **If cause is unknown after 15 minutes**: Escalate to the Payments tech lead immediately.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 5 min | Post initial assessment in #payments-incidents |
| 15 min | If not resolved: page the Payments tech lead via PagerDuty |
| 30 min | If FX provider outage ongoing: enable USD-only fallback, page Engineering Manager |
| 60 min | If issue unresolved: initiate major incident process |

**Who to escalate to:**
- Payments tech lead: PagerDuty schedule "payments-leads"
- FX rate provider outage: Contact provider support via link in #payments-incidents bookmarks
- Infrastructure issues (Redis, K8s): PagerDuty schedule "infra-oncall"

## Dashboards

- [Payments Currency Overview](https://grafana.example.com/d/payments-currency) - FX rate cache hit rate, staleness, error rate by currency
- [FX Rate Provider Health](https://grafana.example.com/d/fx-provider) - Provider API latency, error rate, last successful fetch time
- [Payments API Logs](https://kibana.example.com/app/discover#/payments-currency) - Currency conversion error logs filtered by component
- [Non-USD Payment Volume](https://grafana.example.com/d/payments-currency-volume) - Transaction volume and failure rate by currency
