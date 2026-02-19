---
id: REPORT-061
type: report
title: Alert Volume Analysis Report
status: approved
owner: Monitoring Tech Lead
created: '2025-05-04T16:34:21.580Z'
updated: '2026-07-05T17:56:31.192Z'
tags:
  - report
  - monitoring-stack
summary: Alert Volume Analysis Report
company: MonitoringStack
report_month: 2026-04
report_type: company
overall_health: poor
confidence: low
active_initiatives_count: 4
critical_risks_count: 0
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Weekly alert firings | < 500 | 847 | Above target |
| Alert noise ratio | < 20% | 34% | Above target |
| Actionable alert rate | > 80% | 66% | Below target |
| MTTA (mean time to ack) | < 5 min | 8.2 min | Below target |
| False positive rate | < 5% | 12% | Above target |

Alert volume is at an all-time high and the noise-to-signal ratio has deteriorated significantly. Approximately one-third of all firing alerts are being acknowledged and immediately closed without action, indicating they are either false positives or informational noise that does not require human response.

## Key Highlights

- **847 weekly firings vs. 500 target**: Volume has grown 41% over six months as new services were onboarded without alert rule quality review.
- **12% false positive rate**: 101 alerts per week fire and resolve without human action within 5 minutes — a clear indicator of threshold miscalibration.
- **MTTA degradation**: Engineers are taking longer to acknowledge alerts, likely due to alert fatigue from high volume. Mean time to acknowledge has grown from 4.1 minutes to 8.2 minutes over Q1.

## Active Initiatives

1. **Alert rule audit**: Reviewing all 312 active alert rules against firing history. Rules with >50% false positive rate in the last 30 days will be tuned or removed.
2. **Flap suppression**: Implementing AlertManager's `for` duration requirements on all warning-severity rules (minimum 5 minutes before firing).
3. **SLO-based alerting migration**: Moving critical service alerts from threshold-based to error-budget burn rate alerting, which produces higher-quality signals.
4. **Alert ownership tagging**: Requiring all alert rules to have `team` and `service` labels for ownership accountability and routing accuracy.

## Incidents

| Date | Severity | Duration | Description |
|------|----------|----------|-------------|
| Multiple | SEV-3 | < 5 min | 23 distinct alert storm events from flapping rules during deploy windows. |

## Risks

- **Medium**: Alert fatigue is measurable (MTTA increasing). If volume continues to grow, on-call engineers may start ignoring alerts, increasing MTTD for real incidents.
- **Low**: SLO-based alerting migration requires ADR approval (ADR-0033 drafted, pending review).

## Next Month Focus

- Complete alert rule audit and tune/remove lowest-quality rules
- Deploy flap suppression (minimum `for` duration) across all warning rules
- Publish alert ownership tagging standard and enforce on all new rules
- Present SLO-based alerting migration proposal for ADR approval
