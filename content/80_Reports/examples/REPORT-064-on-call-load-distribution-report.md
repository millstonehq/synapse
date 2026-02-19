---
id: REPORT-064
type: report
title: On-Call Load Distribution Report
status: deprecated
owner: Monitoring Tech Lead
created: '2025-12-18T17:38:57.154Z'
updated: '2026-11-12T03:49:38.805Z'
tags:
  - report
  - monitoring-stack
summary: On-Call Load Distribution Report
company: MonitoringStack
report_month: 2024-07
report_type: portfolio
overall_health: good
confidence: low
active_initiatives_count: 7
critical_risks_count: 3
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Weekly alerts per on-call engineer | < 20 | 28 | Above target |
| After-hours pages per engineer/month | < 8 | 11 | Above target |
| On-call rotation coverage (engineers) | 6+ | 5 | Below target |
| MTTA | < 5 min | 7.8 min | Below target |
| On-call burnout score (survey) | > 3.5/5 | 2.9/5 | Below target |

On-call load is unevenly distributed and above sustainable targets. The monitoring team lost one engineer in Q3, reducing the rotation from 6 to 5 engineers. This increased per-engineer on-call frequency from every 6 weeks to every 5 weeks, and simultaneous alert volume growth has made each rotation more demanding.

## Key Highlights

- **28 alerts/week per on-call engineer**: 40% above the 20-alert target. Combined with after-hours pages averaging 11/month (target 8), engineers are reporting alert fatigue.
- **On-call burnout score at 2.9/5**: Team survey in July showed a measurable decline from 3.6/5 in January. Engineers cite alert volume, poor runbook coverage for newer services, and insufficient rotation size.
- **Uneven load by service**: Alert Management Service generates 38% of all pages despite being one of five services. Investigation revealed 12 miscalibrated alert rules firing on transient conditions.

## Active Initiatives

1. **Rotation size expansion**: Hiring for two Monitoring Engineering positions. Target: restore rotation to 7 engineers by Q4.
2. **Alert load rebalancing**: Alert Management Service rule audit to reduce per-engineer page rate. Targeting 30% reduction.
3. **Runbook coverage gaps**: Mapping all active alert rules to runbook sections. 22% of rules have no runbook procedure.

## Incidents

| Date | Severity | On-Call Impact | Description |
|------|----------|---------------|-------------|
| Multiple | SEV-3 | 4 after-hours pages | Alert storm events during deploys woke engineers with low-signal pages. |

## Risks

- **High**: Rotation size of 5 is below the minimum for sustainable on-call. Hiring is in progress but not yet complete.
- **High**: On-call burnout score below 3.0 is a retention risk. Two engineers have flagged on-call load as a concern in 1:1s.
- **Medium**: 22% of alert rules have no runbook coverage. Engineers receiving pages for these rules must diagnose from scratch.

## Next Month Focus

- Complete Alert Management Service rule audit and deploy fixes
- Publish runbook coverage report and assign owners to uncovered rules
- Finalize job descriptions for two Monitoring Engineering open roles
- Re-survey team on on-call experience after alert volume changes
