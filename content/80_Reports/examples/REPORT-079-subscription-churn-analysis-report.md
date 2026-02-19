---
id: REPORT-079
type: report
title: Subscription Churn Analysis Report
status: review
owner: Billing Tech Lead
created: '2025-03-12T13:06:38.767Z'
updated: '2026-03-30T16:03:58.703Z'
tags:
  - report
  - billing-engine
summary: Subscription Churn Analysis Report
company: BillingEngine
report_month: 2025-06
report_type: portfolio
overall_health: poor
confidence: high
active_initiatives_count: 2
critical_risks_count: 0
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Monthly churn rate | < 2% | 3.4% | Above target |
| Voluntary churn rate | — | 2.1% | Tracked |
| Involuntary churn rate (failed payments) | < 0.5% | 1.3% | Above target |
| Subscription renewals (total) | — | 41,200 | Tracked |
| Past-due recovery rate | > 70% | 62% | Below target |
| Trial-to-paid conversion rate | > 35% | 38% | On target |

Churn is significantly above target this period. Involuntary churn (failed payments) is the primary concern, driven by an increase in expired payment methods that were not updated before renewal. The past-due recovery rate of 62% is below the 70% target, meaning a larger proportion of past-due accounts are reaching cancellation before payment is received.

## Key Highlights

- **Involuntary churn root cause identified**: Analysis of churned accounts shows 78% of involuntary churns occurred on subscriptions where the stored payment method expired in the reporting month. We lack a pre-expiry notification workflow.
- **Trial-to-paid conversion healthy**: The 38% trial-to-paid conversion rate exceeds target and is up from 33% last period, reflecting improvements to the onboarding flow.
- **Dunning sequence gap identified**: Current dunning sequence sends 2 payment failure notifications over 7 days. Industry benchmark for SaaS is 3-5 touchpoints over 14 days with payment method update link. Upgrading this is the highest-priority churn reduction lever.

## Active Initiatives

1. **Pre-expiry payment method notification**: Building an automated email campaign that notifies customers 30 and 7 days before their stored payment method expires. Target: next billing cycle.
2. **Dunning sequence expansion**: Extending from 2 to 4 touchpoints over 14 days with a direct "Update payment method" CTA in each. Design complete; implementation in progress.
3. **Churn prediction model**: Data team building an early-warning model using usage metrics to identify at-risk accounts before they churn voluntarily.

## Incidents

| Date | Severity | Duration | Description |
|------|----------|----------|-------------|

No system incidents this period. All churn is business-layer, not caused by billing platform failures.

## Risks

- **High**: If involuntary churn is not reduced in the next 60 days, revenue impact will exceed $200K ARR. Pre-expiry notifications and dunning improvements are the primary mitigations.
- **Medium**: Voluntary churn driver analysis is incomplete. Without understanding why customers are cancelling voluntarily, it is difficult to intervene.

## Next Month Focus

- Ship pre-expiry payment method notification campaign
- Deploy expanded dunning sequence (4 touchpoints, 14 days)
- Complete voluntary churn driver analysis
- Review churn prediction model prototype with Data team
