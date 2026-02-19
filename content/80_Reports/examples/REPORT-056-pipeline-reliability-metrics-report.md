---
id: REPORT-056
type: report
title: Pipeline Reliability Metrics Report
status: review
owner: CI/CD Tech Lead
created: '2025-03-19T13:15:46.680Z'
updated: '2025-07-24T16:41:34.730Z'
tags:
  - report
  - ci-cd-platform
summary: Pipeline Reliability Metrics Report
company: CI/CDPlatform
report_month: 2026-07
report_type: portfolio
overall_health: good
confidence: high
active_initiatives_count: 7
critical_risks_count: 3
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Pipeline pass rate | 98% | 98.4% | On target |
| Flaky test rate | < 2% | 1.4% | On target |
| Infra-caused build failures | < 0.5% | 0.3% | On target |
| Deploy success rate | 99% | 98.9% | Near target |
| ArgoCD sync success rate | 99% | 99.3% | On target |
| Runner heartbeat timeout rate | < 0.1% | 0.08% | On target |

Pipeline reliability is in a strong state with most metrics at or above target. The deploy success rate shortfall is attributable to three specific services with elevated failure rates under investigation.

## Key Highlights

- **Three services above failure threshold**: `reporting-service`, `data-export`, and `legacy-importer` have deploy failure rates of 8%, 6%, and 5% respectively, pulling the overall average below target. All three have open investigation tickets.
- **Runner heartbeat improvement**: The heartbeat timeout rate dropped from 0.4% to 0.08% after the fleet manager's stale job reclaim timeout was adjusted from 60 seconds to 90 seconds. Fewer jobs were being incorrectly abandoned.
- **Infra-caused failures at all-time low**: Only 0.3% of build failures are attributable to infrastructure issues (runner crashes, network timeouts, storage errors), down from 2.1% a year ago.

## Active Initiatives

1. **Failing service investigations**: Active RCAs for the three high-failure-rate services. `reporting-service` failure root cause identified as flaky DB seed; fix in progress.
2. **Synthetic pipeline monitoring**: A canary build job runs every 5 minutes and alerts if the end-to-end pipeline takes more than 15 minutes or fails. Deployed to all environments.
3. **Deployment circuit breaker**: Rolling to production in Q3. Will halt all deploys to an environment when the failure rate exceeds 20% in 15 minutes.

## Risks

- **High**: Three services with elevated failure rates are pulling overall deploy success below target. No timeline confirmed for `data-export` and `legacy-importer` fixes.
- **Medium**: The deployment circuit breaker has not yet been tested under a real incident scenario. First live exercise will be unplanned.

## Next Month Focus

- Ship fix for `reporting-service` flaky seed issue
- Escalate `data-export` and `legacy-importer` investigations to service owners
- Roll out deployment circuit breaker to production
- Publish pipeline reliability scorecard to engineering portal
