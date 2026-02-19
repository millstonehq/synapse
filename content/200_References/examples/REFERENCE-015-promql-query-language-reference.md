---
id: REFERENCE-015
type: reference
title: PromQL Query Language Reference
status: draft
owner: Security Team
created: '2025-10-18T11:14:53.127Z'
updated: '2026-12-27T09:19:18.463Z'
tags:
  - reference
  - monitoring-stack
summary: PromQL Query Language Reference
upstream_url: https://docs.example.com/promql-query-language-reference
last_synced: '2026-07-15T01:30:24.340Z'
attribution: IEEE
license: CC BY-SA 4.0
category: api-reference
example: true
---

## Overview

PromQL (Prometheus Query Language) is the functional query language used to select and aggregate time series data stored in Prometheus. Queries are evaluated at a single point in time (instant queries) or over a range (range queries), and results can be used for dashboards, alert rules, and recording rules.

This reference covers the PromQL constructs used within the monitoring stack. For the official upstream specification, see the upstream URL. This document is annotated with internal usage patterns and common queries used in the Grafana dashboards and AlertManager rule files.

## Data Types

PromQL expressions evaluate to one of four types:

- **Instant vector** - A set of time series, each containing a single sample for the same timestamp. Most selector expressions return instant vectors.
- **Range vector** - A set of time series, each containing a range of samples over a time window. Used with functions like `rate()`, `increase()`, and `avg_over_time()`. Requires a duration suffix: `[5m]`, `[1h]`.
- **Scalar** - A single floating-point numeric value with no time series labels.
- **String** - A constant string value. Rarely used directly in queries.

## Metric Selectors

### Instant Selector

Selects all time series matching the given metric name and label matchers at evaluation time:

```promql
http_requests_total
http_requests_total{job="metrics-collection", status="200"}
```

### Range Selector

Selects samples over a look-back window. Required input for rate-based functions:

```promql
http_requests_total[5m]
http_requests_total{job="alert-management", code=~"5.."}[10m]
```

### Label Matchers

| Operator | Meaning |
|----------|---------|
| `=` | Exact match |
| `!=` | Not equal |
| `=~` | Regex match |
| `!~` | Regex does not match |

## Functions

### Rate and Increase

`rate(v range-vector)` - Calculates the per-second average rate of increase of the time series. Use for counters. Handles counter resets automatically.

```promql
rate(http_requests_total{job="log-aggregation"}[5m])
```

`increase(v range-vector)` - Total increase over the range window. Equivalent to `rate(v) * window_seconds`.

```promql
increase(errors_total[1h])
```

`irate(v range-vector)` - Instantaneous rate using only the last two data points. More responsive but noisier than `rate()`. Use for dashboards where low latency matters, not for alerts.

### Aggregation

`sum()`, `avg()`, `min()`, `max()`, `count()` - Aggregate across all time series or grouped by labels using the `by` or `without` clause:

```promql
sum(rate(http_requests_total[5m])) by (job)
avg(prometheus_tsdb_head_series) without (instance)
```

`topk(k, v)` / `bottomk(k, v)` - Return the k highest or lowest series:

```promql
topk(5, rate(http_requests_total[5m]))
```

### Statistical Functions

`histogram_quantile(phi, v)` - Computes quantiles from Prometheus histogram metrics. `phi` is the quantile as a fraction (0.95 for p95):

```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

`quantile_over_time(phi, v range-vector)` - Quantile over a range of a gauge or summary metric.

### Time Functions

`time()` - Returns the current Unix timestamp as a scalar.

`timestamp(v)` - Returns the Unix timestamp of each sample in the vector.

`hour(v)` / `day_of_week(v)` - Extract time components. Useful in alert inhibitions and routing rules.

### Label Manipulation

`label_replace(v, dst_label, replacement, src_label, regex)` - Adds or rewrites a label using a regex on an existing label value.

`label_join(v, dst_label, separator, src_label...)` - Concatenates multiple label values into a new label.

## Operators

### Arithmetic

`+`, `-`, `*`, `/`, `%`, `^` - Applied between two instant vectors element-wise, or between a vector and a scalar.

### Comparison

`==`, `!=`, `>`, `<`, `>=`, `<=` - Filter or compare. By default, results where the comparison is false are dropped from the output. Use `bool` modifier to return 0/1 instead:

```promql
http_requests_total > bool 0
```

### Logical (Set)

`and`, `or`, `unless` - Operate on two instant vectors to return the intersection, union, or difference.

### Vector Matching

Binary operations between two instant vectors require matching labels. Use `on()` or `ignoring()` to control which labels are matched, and `group_left()` or `group_right()` for many-to-one relationships:

```promql
rate(http_errors_total[5m])
  / on(job, instance) ignoring(status)
rate(http_requests_total[5m])
```

## Subqueries

Subqueries evaluate a range query over a specified step interval, useful when a range vector function is needed on a derived expression:

```promql
max_over_time(
  rate(http_requests_total[5m])[1h:1m]
)
```

## Common Internal Patterns

### SLO Error Rate

The standard error rate query used in SLO dashboards and burn rate alert rules:

```promql
sum(rate(http_requests_total{status=~"5..", job="$service"}[5m]))
/
sum(rate(http_requests_total{job="$service"}[5m]))
```

### Burn Rate (1-hour fast window)

Used by fast-burn rate alerts — detects if current consumption rate would exhaust the 30-day error budget within 1 hour:

```promql
(
  sum(rate(http_errors_total{job="$service"}[1h]))
  /
  sum(rate(http_requests_total{job="$service"}[1h]))
) / (1 - 0.999)
```

### Disk Usage Approaching Full

Used by the Prometheus disk capacity alert rule:

```promql
(
  node_filesystem_avail_bytes{mountpoint="/prometheus-data"}
  /
  node_filesystem_size_bytes{mountpoint="/prometheus-data"}
) * 100 < 20
```

### Alert Noise Ratio

Used in the alert quality report to track non-actionable alerts:

```promql
sum(increase(alertmanager_alerts_received_total{alertname!~"Watchdog"}[24h]))
-
sum(increase(alertmanager_alerts_invalid_total[24h]))
```

## Recording Rules

Recording rules pre-compute expensive expressions and store the result as a new time series. This reduces query latency for dashboards and prevents fan-out at alert evaluation time.

Convention used in this stack: recording rule names follow the format `job:metric:aggregation`, for example:

```yaml
- record: job:http_requests_total:rate5m
  expr: sum(rate(http_requests_total[5m])) by (job)
```

Recording rules are defined in `/etc/prometheus/rules/recording_rules.yml` and are loaded by both Prometheus instances in the HA pair.

## Sync Notes

This reference is based on the Prometheus 2.x PromQL specification with internal annotations specific to our alerting and dashboard conventions. Re-sync when upgrading to Prometheus 3.x, as subquery syntax and some histogram functions have changed in that version.
