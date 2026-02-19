---
id: MEETING-072
type: meeting
title: SLO Framework Design Workshop
status: accepted
owner: Product Manager
created: '2025-01-24T03:02:46.073Z'
updated: '2026-03-23T15:56:47.070Z'
tags:
  - meeting
  - monitoring-stack
summary: SLO Framework Design Workshop
company: MonitoringStack
topic: SLO Framework Design Workshop
meeting_date: '2024-12-19T15:40:17.118Z'
example: true
our_attendees:
  - Principal Engineer
  - Tech Lead
  - Product Manager
their_attendees:
  - Engineering Manager
  - QA Lead
---

## Meeting Details

- **Project**: Monitoring Stack — SLO Framework Initiative
- **Topic**: SLO Framework Design Workshop
- **Date/Time**: 2024-12-19 3:40 PM UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Pre-launch design session to align on the SLO framework structure, tooling choices, and error budget policies before rolling out SLOs to all production services in Q1.

## Observations by Domain

- **SLI Design**: Current services lack standardized SLI definitions; each team uses different queries and time windows, making cross-team comparisons unreliable
- **Error Budget Policy**: No formal error budget policy exists; teams do not know when to pause feature work in response to reliability degradation
- **Tooling**: Prometheus recording rules are inconsistently used for SLI pre-aggregation; some teams query raw counters in dashboards which is slow and imprecise
- **Alerting Integration**: Burn rate alerting is not yet implemented for any service; teams only get alerted when the SLO is already breached, not when burn rate predicts a breach
- **Organizational Readiness**: Engineering Managers are supportive but need clearer guidance on how SLO reviews should be conducted and what the expected outcomes are

## Key Metrics & Data Points

- **Services with defined SLOs**: 4 out of 23 production services
- **Average error budget consumption (last 90 days)**: 61% across the 4 services with SLOs
- **Burn rate alerting coverage**: 0% — no services have burn rate alerts configured
- **SLO breach rate (last quarter)**: 2 out of 4 services breached their SLO at least once
- **Mean time to detect SLO breach**: 47 minutes (based on available incident data)

## Preliminary Scorecard Hooks

- SLI Coverage: 1/5 - Only 4 of 23 services have any SLI defined; significant gap
- Error Budget Policy: 1/5 - No formal policy; ad-hoc decisions on when to address reliability
- Alerting Integration: 2/5 - Basic threshold alerts exist but no burn rate alerting
- Tooling Maturity: 2/5 - Recording rules exist but not standardized; dashboard SLO panels inconsistent
- Process Maturity: 2/5 - Quarterly review process exists on paper but rarely followed

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Teams define SLOs that are too aggressive and immediately breach them | High | Medium | Product Manager | Provide 90-day historical data review template before SLO definition | 2025-01-15 |
| Burn rate alerts create more noise if thresholds are misconfigured | Medium | High | Principal Engineer | Validate burn rate alert config in staging with historical data before production rollout | 2025-02-01 |
| Low adoption across teams without clear executive sponsorship | Medium | Medium | Engineering Manager | Engineering Manager to present SLO framework at All-Hands and mandate participation by end of Q1 | 2025-01-31 |

## Decisions & Next Steps

### Decisions

- Adopt the Google SRE error budget model: 30-day rolling window, 1-hour and 6-hour burn rate alerts
- All production services must have at least one SLO defined by end of Q1 2025
- SLI queries must use Prometheus recording rules; raw counter queries in SLO contexts are not permitted

### Action Items

- Principal Engineer to publish the standard recording rule template for availability and latency SLIs (due 2025-01-10)
- Tech Lead to configure burn rate alerting for the two highest-traffic services as reference implementations (due 2025-01-24)
- Product Manager to schedule SLO definition workshops with each service team (due 2025-01-31)

### Follow-ups

- Review burn rate alert configuration after 2 weeks of production data
- Schedule Q1 SLO compliance review for last week of March 2025
