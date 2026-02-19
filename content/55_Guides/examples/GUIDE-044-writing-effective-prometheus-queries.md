---
id: GUIDE-044
type: guide
title: Writing Effective Prometheus Queries
status: approved
owner: Engineering Team
created: '2024-01-22T08:36:13.680Z'
updated: '2025-11-12T01:14:17.261Z'
tags:
  - guide
  - monitoring-stack
summary: Writing Effective Prometheus Queries
audience: partner
related_systems:
  - SYSTEM-037
  - SYSTEM-039
related_sops:
  - SOP-077
  - SOP-075
example: true
---

## Why PromQL Matters

Good Prometheus queries are the foundation of useful dashboards and reliable alerts. A poorly written query can produce misleading results, cause alert fatigue, or make Prometheus slow for everyone. A well-written query is fast, correct, and easy for your colleagues to understand.

This guide covers the most important PromQL patterns for monitoring services in production, with a focus on the queries you'll write most often: rate calculations, error ratios, histogram quantiles, and aggregations.

## The Most Important PromQL Patterns

### Rate and Error Rate

Always use `rate()` for counters, not `increase()` or raw values. `rate()` gives you per-second values over a time window and handles counter resets (e.g., pod restarts) correctly.

```promql
# Request rate per second (last 5 minutes)
rate(http_server_request_total{service="auth"}[5m])

# Error rate as a ratio of errors to total requests
rate(http_server_request_total{service="auth", status=~"5.."}[5m])
  /
rate(http_server_request_total{service="auth"}[5m])
```

The time window for `rate()` should be at least 4x the scrape interval. With a 15-second scrape interval, use `[1m]` as the minimum; `[5m]` is safer for dashboard panels.

### Histogram Quantiles

For latency metrics, use `histogram_quantile()` to calculate percentiles from histogram buckets. Never use `avg()` on latency — it hides outliers.

```promql
# P95 latency for the last 5 minutes
histogram_quantile(0.95,
  rate(http_server_request_duration_seconds_bucket{service="auth"}[5m])
)
```

Always aggregate the `rate()` before passing to `histogram_quantile()`. Aggregating quantiles directly produces incorrect results.

### Aggregating Across Labels

Use `sum by` and `avg by` to aggregate across dimensions you care about. Use `without` to drop dimensions you don't need.

```promql
# Error rate per endpoint
sum by (path) (
  rate(http_server_request_total{service="auth", status=~"5.."}[5m])
)
```

## Avoiding Common Mistakes

**Do not use high-cardinality labels in aggregations** — labels like `user_id`, `request_id`, or `trace_id` create millions of series and will make Prometheus slow. If you see these in a metric, report it to the service owner as a bug.

**Do not use instant vectors where range vectors are needed** — `rate()`, `increase()`, and `irate()` require range vectors. Using an instant vector is a common syntax error.

**Do not compare counters directly across pod restarts** — always use `rate()` or `increase()` which handle resets. Raw counter comparisons break when pods restart.

## Using Recording Rules for Expensive Queries

If a query is used in multiple dashboards or is computationally expensive, create a recording rule instead. Recording rules pre-compute the result on every scrape cycle, making dashboard and alert queries near-instant.

```yaml
# Example recording rule
- record: job:http_request_rate5m:sum_rate
  expr: sum by (job) (rate(http_server_request_total[5m]))
```

Recording rules must follow the naming pattern `{level}:{metric}:{operations}` and must be reviewed by the Platform team before deployment.

## Next Steps

- Use the Prometheus Explore tab in Grafana to experiment with queries before committing them to dashboards
- Review the Alert Definition Standard for requirements on queries used in alerting rules
- Read the Building Grafana Dashboards Guide to learn how to incorporate your queries into production dashboards
