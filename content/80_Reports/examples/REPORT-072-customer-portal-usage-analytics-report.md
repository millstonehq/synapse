---
id: REPORT-072
type: report
title: Customer Portal Usage Analytics Report
status: approved
owner: Customer Tech Lead
created: '2025-06-10T15:21:39.413Z'
updated: '2026-10-27T00:22:13.299Z'
tags:
  - report
  - customer-portal
summary: Customer Portal Usage Analytics Report
company: CustomerPortal
report_month: 2026-03
report_type: company
overall_health: poor
confidence: medium
active_initiatives_count: 5
critical_risks_count: 3
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| DAU | 12,000 | 13,100 | Above target |
| MAU | 38,000 | 41,200 | Above target |
| DAU/MAU ratio | > 30% | 31.8% | On target |
| Session duration (median) | > 4 min | 5m 12s | On target |
| Feature adoption (new features) | > 25% in 30 days | 38% | Above target |
| Support ticket deflection rate | > 20% | 22% | On target |

Portal usage is growing strongly. All key usage metrics are at or above target. The notification center launch in February contributed to increased session frequency and duration.

## Key Highlights

- **Top pages by session starts**: (1) Account Overview, (2) Support Tickets, (3) Notification Center (new), (4) Preferences, (5) Invoice History. Notification Center entering the top 5 within 6 weeks of launch validates the investment.
- **Mobile usage is 34% of sessions**: Up from 26% six months ago. This trend supports the case for the Customer Portal Mobile App PRD. Mobile sessions have longer time-to-first-interaction (2.1s vs 1.4s desktop), pointing to performance improvement opportunity.
- **Support ticket deflection**: 22% of users who open a support ticket first visit the FAQ search within the widget without filing a ticket. This metric is above the 20% target and growing.

## Active Initiatives

1. **Search feature prioritization**: Usage data showing 28% of sessions including an account history lookup with no search capability. Input to Q2 roadmap.
2. **Mobile performance optimization**: Mobile-specific performance improvements being scoped based on 34% mobile session share.

## Incidents

No incidents affecting analytics data collection in this period.

## Risks

- **Medium**: 34% mobile usage share means mobile performance bugs now affect a significant user segment; mobile testing coverage in CI needs expansion.
- **Low**: Analytics pipeline is running on the deprecated Customer Analytics Service; migration to new platform is needed before year-end.

## Next Month Focus

- Present search feature case to Q2 roadmap planning
- Expand mobile device coverage in E2E test suite
- Begin Customer Analytics Service migration planning
