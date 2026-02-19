---
id: REPORT-054
type: report
title: Deployment Frequency Analysis Report
status: approved
owner: CI/CD Tech Lead
created: '2025-04-24T03:58:34.875Z'
updated: '2025-01-09T17:30:11.584Z'
tags:
  - report
  - ci-cd-platform
summary: Deployment Frequency Analysis Report
company: CI/CDPlatform
report_month: 2026-02
report_type: company
overall_health: poor
confidence: medium
active_initiatives_count: 5
critical_risks_count: 0
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Deployments per week (total) | 50+ | 42 | Below target |
| Services deploying daily | > 60% | 48% | Below target |
| Lead time (commit to production) | < 2 days | 2.3 days | Below target |
| Change failure rate | < 2% | 3.8% | Below target |
| Rollback rate | < 2% | 3.8% | Below target |
| MTTR after failed deploy | < 5 min | 8 min | Below target |

Deployment frequency metrics indicate the platform is classified as "medium" on DORA's four-key metrics scale. The primary gap is that less than half of services are deploying daily; most accumulate 2-4 days of changes between deployments due to manual approval workflows.

## Key Highlights

- **DORA baseline established**: Q1 2025 is the first quarter with full DORA metric instrumentation. Deployment frequency is 6 per day (42/week), lead time is 2.3 days, change failure rate is 3.8%, and MTTR is 8 minutes.
- **Manual approval workflow bottleneck**: Teams deploying less than once per day were surveyed. The most common reason is waiting for manual approval in the Deployment Controller gate. Teams with automated approval criteria deploy 3x more frequently.
- **Rollback time improvement needed**: The 8-minute MTTR is driven by the time to detect a failure (alerting latency) and trigger a rollback. Canary analysis is expected to reduce this by catching failures earlier.

## Active Initiatives

1. **Automated approval criteria expansion**: Working with 6 high-value teams to define automated gate criteria so manual approval is only required for high-risk changes.
2. **Alert latency reduction**: Investigating whether P95 alert-to-trigger latency can be reduced from 4 minutes to 2 minutes for deploy-related failures.
3. **DORA dashboard**: Public Grafana dashboard for DORA metrics published to the engineering portal.

## Risks

- **Medium**: Change failure rate of 3.8% is nearly double the 2% target. Investigation suggests test coverage gaps in 3 services account for the majority of failures.
- **Low**: Manual approval workflows are unlikely to fully disappear; targeting 75% of services with automated criteria is a realistic Q2 goal.

## Next Month Focus

- Pilot automated approval criteria with 3 teams
- Publish DORA dashboard to all-hands
- Investigate the 3 services responsible for the majority of change failures
