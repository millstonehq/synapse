---
id: GUIDE-068
type: guide
title: Writing Effective Alert Rules Guide
status: approved
owner: Developer Experience
created: '2024-09-21T20:32:02.810Z'
updated: '2025-08-12T00:37:03.572Z'
tags:
  - guide
  - monitoring-stack
summary: Writing Effective Alert Rules Guide
audience: customer
related_systems:
  - SYSTEM-040
  - SYSTEM-039
related_sops:
  - SOP-074
  - SOP-075
example: true
---

## Why Alert Rule Quality Matters

An alert is a promise to an engineer: "This is worth waking you up for." When that promise is broken — when an alert fires but requires no action, or fires so often that engineers tune it out — the entire monitoring system degrades. Engineers begin to ignore pages, critical signals get lost in noise, and the mean time to detect real incidents rises.

The [[SYSTEM-039|Alert Management Service]] routes every alert rule in this stack. Every alert you write runs through its evaluation engine and, when firing, pages someone. The goal of this guide is to help you write alert rules that fire when they should, stay silent when they should, and communicate clearly what to do when they fire.

The [[SYSTEM-040|Status Page Service]] surfaces service health status derived in part from alert state. Well-designed alert rules ensure status page accuracy and prevent false customer-facing degradation notices.

## The Three Questions

Before writing an alert rule, answer these three questions:

1. **Is this condition always actionable?** If an engineer receives this page, can they always do something meaningful in response? If the answer is sometimes "just wait," the alert is not ready. Either the threshold is wrong, or the condition needs a longer evaluation window.

2. **Is this the right level of abstraction?** Alert on symptoms, not causes. `high_error_rate` (symptom) is better than `database_connection_refused` (cause). Symptom-based alerts are more stable, catch more failure modes, and are clearer about business impact. Cause-based alerts can be used as additional context, but should not be the primary page trigger.

3. **Does this overlap with an existing alert?** Before creating a new alert, check whether an existing rule already covers this condition. Duplicate alerts create noise and confuse incident responders who receive multiple pages for the same event.

## Anatomy of a Good Alert Rule

Every alert rule in the monitoring stack follows this structure:

```yaml
- alert: ServiceErrorRateHigh
  expr: |
    sum(rate(http_requests_total{job="my-service", status=~"5.."}[5m]))
    /
    sum(rate(http_requests_total{job="my-service"}[5m]))
    > 0.01
  for: 3m
  labels:
    severity: warning
    team: platform
    service: my-service
  annotations:
    summary: "High error rate on {{ $labels.job }}"
    description: >
      Error rate on {{ $labels.job }} is {{ $value | humanizePercentage }}
      over the last 5 minutes (threshold: 1%).
    runbook_url: "https://runbooks.example.com/my-service-error-rate"
    dashboard_url: "https://grafana.example.com/d/my-service-overview"
```

### The `for` Duration

The `for` clause is the most important lever for reducing false positives. It requires the expression to be continuously true for the specified duration before the alert fires.

- **Omitting `for`**: Alert fires on the first evaluation that satisfies the condition. Only appropriate for binary conditions (pod is CrashLooping, disk is 100% full) where any occurrence is significant.
- **`for: 1m`**: Appropriate for conditions that should resolve within a scrape cycle if they are transient. Use for fast-moving signals where a 1-minute window is enough to confirm persistence.
- **`for: 3m`**: The standard baseline. Most error-rate and latency alerts use this. Long enough to filter transient spikes, short enough to detect real problems quickly.
- **`for: 10m`** or longer: Use when the underlying signal is slow-moving (capacity trends, gradual saturation) or when the alert is informational (warning-level only).

Never use `for: 0` on a high-severity alert that pages an engineer.

### Severity Labels

All alert rules must include a `severity` label. The routing tree in the [[SYSTEM-039|Alert Management Service]] uses this label to determine notification channel and escalation path:

| Severity | Meaning | Notification |
|----------|---------|-------------|
| `critical` | Service is down or SLO breach is imminent; customer impact now | PagerDuty (immediate page) |
| `warning` | Degradation detected; action required within business hours | Slack `#alerts-warning` |
| `info` | FYI condition; no immediate action required | Slack `#alerts-info` only |

Do not use `critical` for conditions that can wait until morning. Reserve `critical` for conditions where delay causes measurable customer impact.

### Annotations

Every alert rule must include:

- `summary`: A one-line description of the condition that fired. This appears in the PagerDuty notification subject and the AlertManager Slack message title. Write it to answer "what is broken" in 10 words or fewer.
- `description`: 2-3 sentences providing context: current metric value, threshold, which service, what this means for users. Include `$value` and relevant `$labels` template variables.
- `runbook_url`: Direct link to the runbook for this alert. If no runbook exists yet, create a stub before shipping the alert rule.
- `dashboard_url`: Direct link to the Grafana dashboard most relevant for diagnosing this alert.

Missing annotations cause alert responders to lose time during incidents looking for context that should have been embedded in the alert itself.

## Common Mistakes

### Threshold Alerting on Counters

Alerting directly on a counter value (total requests, total errors) instead of a rate is a common mistake:

```promql
# Wrong: fires whenever the counter value exceeds threshold
http_errors_total > 100

# Correct: fires when the rate exceeds a percentage threshold
rate(http_errors_total[5m]) / rate(http_requests_total[5m]) > 0.01
```

Counter values only increase, so threshold-based counter alerts either fire immediately (threshold too low) or never (threshold too high). Always use `rate()` or `increase()` for counter-based alerts.

### Alerting on Individual Instances Without Aggregation

Alerting on a per-instance metric when you have multiple replicas means you get one alert per pod:

```promql
# Wrong: fires once per pod — 6 alerts for a 6-replica service
http_errors_total{job="my-service"} > 0

# Correct: aggregate first, alert once
sum(rate(http_errors_total{job="my-service"}[5m])) > 0.01
```

If you need per-instance alerts (for example, to detect a bad pod in a heterogeneous replica set), use `by (instance)` in the aggregation and accept that multiple alerts may fire.

### Overly Sensitive Thresholds

Set thresholds based on historical data, not intuition. Before creating an alert, query the last 30 days of the metric to understand its normal distribution. A threshold at the 99.9th percentile of historical values is a starting point; adjust based on false positive rate in the first two weeks.

### Missing Inhibition Configuration

If your alert fires alongside a broader alert (for example, a component-level error alert that fires whenever a node-level alert is already firing), configure an inhibition rule in the AlertManager routing config. Without inhibition, incident responders receive duplicate alerts and spend time correlating them manually.

## Testing Alert Rules

Before shipping a new alert rule to production, verify it in staging:

1. **Confirm it fires in the intended condition** - Use PromQL to manually query the expression against staging data and confirm the expression evaluates to a value that would satisfy the threshold.
2. **Confirm it does NOT fire under normal conditions** - Query the same expression against the last 7 days of staging data. If it fires during normal operation, the threshold or `for` duration needs adjustment.
3. **Confirm the annotations render correctly** - Use the AlertManager test endpoint or the Prometheus `/-/alerts` UI to view the rendered annotation with template variable substitution.
4. **Run it for 24 hours in warning severity** - Before setting a new alert to `critical`, run it as `warning` for at least one full day in production. Review the firing history before promoting severity.

## Maintenance

Alert rules are not set-and-forget. Every alert rule must have a named owner (`team` label). The Alert Rule Review Process runs quarterly and requires teams to review their alert firing history. Alerts with:

- False positive rate > 20% over the past 30 days — must be adjusted or removed
- Zero fires in the past 90 days for a `critical` alert — must be validated as still relevant
- No `runbook_url` annotation — must have a runbook stub created before the next review

The review process ensures that alert rules remain accurate signals over time as services evolve and traffic patterns change.
