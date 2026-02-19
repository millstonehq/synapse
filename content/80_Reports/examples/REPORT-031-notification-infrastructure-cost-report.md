---
id: REPORT-031
type: report
title: Notification Infrastructure Cost Report
status: approved
owner: Notification Tech Lead
created: '2025-08-29T04:25:40.898Z'
updated: '2026-07-22T10:27:51.763Z'
tags:
  - report
  - notification-service
summary: Notification Infrastructure Cost Report
company: NotificationService
report_month: 2026-07
report_type: portfolio
overall_health: fair
confidence: medium
active_initiatives_count: 2
critical_risks_count: 3
example: true
---

## Service Health

| Cost Category | Monthly Budget | Actual | Status |
|---------------|---------------|--------|--------|
| SMS provider (Twilio) | $8,500 | $11,200 | Over budget |
| Email provider (SendGrid) | $1,200 | $1,050 | On target |
| Kubernetes compute | $3,400 | $3,650 | Slightly over |
| RabbitMQ (managed) | $800 | $810 | On target |
| PostgreSQL (managed) | $600 | $590 | On target |
| Total | $14,500 | $17,300 | 19% over budget |

Infrastructure costs are 19% over the monthly budget, driven primarily by SMS costs. Twilio pricing increased effective February 1, and the migration to Vonage for low-priority SMS that was planned as a mitigation has not yet been completed. Kubernetes compute costs are slightly over budget due to the pre-scaling work done ahead of Q2 campaign season.

## Key Highlights

- **SMS cost overrun is the primary driver**: Twilio's 15% price increase, combined with 8% volume growth, has pushed SMS costs $2,700 above budget. Routing low-priority SMS through Vonage (which is 22% cheaper) would reduce this cost by approximately $1,800/month.
- **Email costs tracking well**: The list hygiene automation from last month's deliverability work reduced billable send volume by 12%, keeping email costs below budget despite volume growth.
- **Compute scaling investigated**: The Q2 pre-scaling accounted for $250 in excess compute. Autoscaling will handle the remaining headroom and manual pre-scaling will not be repeated.

## Active Initiatives

1. **Vonage migration for low-priority SMS**: Engineering work in progress. Estimated completion: 3 weeks. Expected monthly savings: ~$1,800.
2. **RabbitMQ on-premises evaluation**: Evaluating self-hosted RabbitMQ on existing EC2 capacity to eliminate the $810/month managed service cost.

## Incidents

No cost-related incidents this period.

## Risks

- **High**: SMS costs will continue to exceed budget until Vonage migration is complete.
- **High**: Volume growth projections suggest SMS costs will reach $14,000/month by Q4 without provider diversification.
- **High**: RabbitMQ self-hosting carries operational risk. Requires dedicated SRE capacity for cluster management.

## Next Month Focus

- Complete Vonage migration for low-priority SMS routing
- Finalize RabbitMQ self-hosting cost-benefit analysis
- Review compute autoscaling parameters to eliminate manual pre-scaling
