---
id: ADR-0033
type: adr
title: Implement Error Budget Based Alerting
status: deprecated
owner: Tech Lead
created: '2024-02-15T07:31:24.713Z'
updated: '2026-08-29T01:12:34.010Z'
tags:
  - adr
  - monitoring-stack
summary: Implement Error Budget Based Alerting
example: true
---

## Context

The monitoring platform currently uses static threshold alerting: an alert fires when a metric crosses a fixed value (e.g., "error rate > 1%"). This approach generates excessive noise — brief spikes that don't materially affect monthly SLOs fire the same alert as sustained degradations — and simultaneously misses slow-burning problems that consume error budget without ever crossing a threshold in a single evaluation window.

Error budget-based alerting (also called burn rate alerting) addresses both issues by alerting on the rate at which the monthly error budget is being consumed, rather than on absolute metric values. A fast burn rate (e.g., consuming 5% of the monthly budget per hour) warrants an immediate page; a slow burn rate (consuming 2% over 6 hours) warrants a ticket but not a page.

This ADR was superseded in practice — the implementation proceeded and this ADR is now deprecated. It is preserved for historical context on the decision-making process.

## Decision

All SLO-bearing services in the monitoring stack adopted **error budget burn rate alerting** using two complementary alert rules per service:

- **Fast burn (page-worthy)**: Fires when the 1-hour burn rate exceeds 14.4x the SLO threshold (consuming >2% of the monthly budget in 1 hour). Routes to PagerDuty high-urgency.
- **Slow burn (ticket-worthy)**: Fires when the 6-hour burn rate exceeds 6x the SLO threshold (consuming >5% of the monthly budget over 6 hours). Routes to Slack for next-business-day follow-up.

These thresholds follow the Google SRE Workbook recommendations for 99.9% SLOs.

## Consequences

**Positive:**
- Alert volume reduced by 31% in the first month after migration (as measured in REPORT-061)
- Actionable alert rate improved from 66% to 84% — engineers receive fewer false positives
- Slow-burn alerts catch problems that threshold alerting misses entirely
- Alerts are directly tied to SLO impact, making on-call triage more straightforward

**Negative:**
- Engineers must understand error budget math to interpret alert context; requires training investment
- Alert rules are more complex PromQL expressions; harder to write and review correctly
- Fast/slow burn thresholds require tuning per SLO target level (99.9% vs 99.99% use different multipliers)

**Neutral:**
- Requires SLOs to be formally defined before alerts can be written; this forced SLO definition for services that previously had informal availability targets

## Alternatives Considered

**Multi-window, multi-burn-rate alerting (more granular):**
- Pro: Even more precise alerting; reduces both false positives and false negatives further
- Con: 4 alert rules per SLO instead of 2; significantly more complex to explain and maintain
- Rejected because: The two-rule approach (fast + slow burn) captures 95% of the benefit at significantly lower complexity.

**Keep static threshold alerting:**
- Pro: Simple to understand, write, and debug
- Con: Continued alert fatigue (31% excess volume demonstrated), continued false negatives for slow-burn degradations
- Rejected because: The data from REPORT-061 demonstrated the status quo was unsustainable.
