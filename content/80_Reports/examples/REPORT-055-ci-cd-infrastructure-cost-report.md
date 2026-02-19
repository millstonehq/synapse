---
id: REPORT-055
type: report
title: CI/CD Infrastructure Cost Report
status: approved
owner: CI/CD Tech Lead
created: '2024-10-21T23:15:34.492Z'
updated: '2026-08-02T02:28:24.259Z'
tags:
  - report
  - ci-cd-platform
summary: CI/CD Infrastructure Cost Report
company: CI/CDPlatform
report_month: 2026-04
report_type: company
overall_health: good
confidence: low
active_initiatives_count: 5
critical_risks_count: 3
example: true
---

## Service Health

| Cost Category | Budget | Actual | Status |
|---------------|--------|--------|--------|
| Runner fleet (compute) | $18,000/mo | $21,400/mo | Over budget |
| Artifact storage (S3 + Harbor) | $2,500/mo | $2,100/mo | On budget |
| Build cache storage | $800/mo | $1,200/mo | Over budget |
| Monitoring (Grafana, logs) | $3,000/mo | $2,800/mo | On budget |
| Total CI/CD infrastructure | $24,300/mo | $27,500/mo | 13% over |

Total infrastructure cost is 13% over budget, driven primarily by runner fleet growth following the Q1 capacity expansion and build cache growth from increased build volume.

## Key Highlights

- **Runner fleet cost increase**: The March fleet expansion added 40 nodes, bringing total monthly compute cost to $21,400. The previous budget was set before this expansion. A revised budget of $22,000 has been submitted for Q3 approval.
- **Build cache storage growing unchecked**: Cache storage has grown 58% in 6 months. The 7-day TTL policy is not aggressively enforcing eviction of large artifacts. A cache size cap of 500GB per repository is being evaluated.
- **Artifact storage well within budget**: Harbor's garbage collection policy successfully removed 12TB of untagged images in Q1, keeping storage costs flat despite higher build volume.

## Active Initiatives

1. **Runner spot instances**: Evaluating spot/preemptible instances for 60% of the fleet to reduce compute cost by an estimated 40%. Reliability risk assessment in progress.
2. **Build cache eviction tuning**: Piloting a 3-day TTL for non-main-branch builds to reduce storage growth.
3. **Cost attribution by team**: Adding team-level cost tags to all runner jobs to enable chargeback reporting.

## Risks

- **High**: Runner fleet cost is $3,400/mo over budget with no approved budget increase yet. If Q3 budget request is denied, fleet capacity may need to be reduced.
- **Medium**: Build cache storage growth will exceed current hardware limits by Q4 at the current growth rate without policy changes.

## Next Month Focus

- Complete spot instance reliability assessment and make go/no-go decision
- Pilot 3-day build cache TTL for non-main branches
- Publish team-level cost attribution report
- Submit revised runner fleet budget for Q3 approval
