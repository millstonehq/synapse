---
id: REPORT-087
type: report
title: CI/CD Lead Time Metrics Report
status: approved
owner: CI/CD Tech Lead
created: '2024-07-08T15:33:13.571Z'
updated: '2026-12-20T09:01:01.527Z'
tags:
  - report
  - ci-cd-platform
summary: CI/CD Lead Time Metrics Report
company: CI/CDPlatform
report_month: 2026-04
report_type: company
overall_health: good
confidence: high
active_initiatives_count: 7
critical_risks_count: 2
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Median lead time (commit to prod) | < 24 hours | 18.4 hours | On target |
| P95 lead time | < 48 hours | 36.2 hours | On target |
| Deployment frequency | > 40/week | 47/week | On target |
| Approval wait time (median) | < 30 min | 22 min | On target |
| Artifact promotion gate pass rate | > 97% | 98.6% | On target |
| Change failure rate | < 5% | 3.8% | On target |

Lead time improved significantly this quarter following the self-service deploy rollout in March and the approval workflow optimization in April. The P95 lead time is slightly elevated for two services with mandatory multi-approver gates; working with those teams to streamline approval groups.

## Key Highlights

- **Self-service deploy adoption**: 91% of production deployments in April were initiated via the self-service deploy UI or CLI without platform team coordination, up from 23% in January. The deployment coordination bottleneck has been effectively eliminated for the majority of services.
- **Approval workflow P95 improvement**: Median approval wait time fell from 45 minutes to 22 minutes after adding a secondary approver to each service's approver group, reducing single-approver availability as the bottleneck.
- **Lead time regression: `inventory-service`**: This service's lead time increased from 8 hours to 31 hours due to a mandatory manual QA step added by the team in March. Flagged for review — manual QA is a significant lead time driver and should be replaced with automated smoke tests.

## Active Initiatives

1. **Approval workflow optimization** (ongoing): Analyzing the 25% of deployments with approval wait times exceeding 60 minutes to identify systemic bottlenecks. Working with two teams that have high wait times due to timezone-distributed approver groups.
2. **Lead time alerting**: Implementing automated alerts when a service's weekly median lead time increases by more than 2x compared to the prior week, enabling early detection of process regressions.
3. **Canary deployment adoption**: Expanding canary rollout adoption from 60% to 80% of services. Services using rolling updates have a higher change failure rate (5.1% vs 2.8% for canary services).

## Incidents

| Date | Severity | Duration | Description |
|------|----------|----------|-------------|
| Apr 7 | SEV-3 | 45 min | Approval workflow Slack notification failure; engineers were unaware of pending approvals; fixed by adding email fallback |

No SEV-1 or SEV-2 incidents this month.

## Risks

- **High-lead-time outliers** could mask overall metric improvement if not tracked separately. Two services with complex approval chains show P95 lead times of 72+ hours, pulling up the fleet P95. Mitigation: track per-service lead time separately and flag outliers in weekly engineering manager reports.
- **Approval bottleneck re-emerging** as team headcount grows and approval groups are not updated. Mitigation: quarterly review of approver group membership; automate notification when group has fewer than 2 active approvers.

## Next Month Focus

- Launch lead time alerting for regressions above 2x weekly baseline
- Complete canary adoption campaign targeting 80% fleet coverage
- Resolve manual QA bottleneck in `inventory-service` with an automated smoke test replacement
- Publish Q2 DORA metrics report for engineering leadership
