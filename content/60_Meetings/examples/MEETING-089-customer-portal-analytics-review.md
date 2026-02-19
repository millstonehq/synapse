---
id: MEETING-089
type: meeting
title: Customer Portal Analytics Review
status: draft
owner: Principal Engineer
created: '2024-05-26T19:08:07.395Z'
updated: '2025-11-24T23:25:46.572Z'
tags:
  - meeting
  - customer-portal
summary: Customer Portal Analytics Review
company: CustomerPortal
topic: Customer Portal Analytics Review
meeting_date: '2024-04-17T05:56:18.708Z'
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

- **Project**: Customer Portal Platform
- **Topic**: Q1 2024 Portal Analytics Review - User Behavior and Feature Usage
- **Date/Time**: 2024-04-17 9:00 AM PT
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager
- **Context**: Quarterly review of portal analytics data to understand feature usage patterns, identify underutilized features, and surface insights for the Q2 roadmap.

## Observations by Domain

- **Feature Adoption**: Dashboard (89% of active users), Support Tickets (76%), Account Settings (54%), Billing (48%), Reports (12%) — reports feature is significantly underutilized
- **Navigation Patterns**: 34% of users navigate directly to support tickets from the homepage; the support ticket flow is the most-used portal workflow
- **Session Duration**: Average session is 4.2 minutes; sessions involving support ticket creation average 11.6 minutes, suggesting the ticket creation flow has significant friction
- **Search Usage**: The new global search (launched in Q4) has 23% adoption; users who use search have 40% lower support ticket submission rate
- **Drop-off Analysis**: The billing setup flow has a 31% drop-off rate at the payment method step; tax information step drops an additional 18%

## Key Metrics & Data Points

- **Monthly active users**: 10,800
- **Reports feature adoption**: 12% of active users
- **Average session duration**: 4.2 minutes
- **Support ticket creation session duration**: 11.6 minutes
- **Global search adoption**: 23% of active users
- **Billing setup drop-off (payment step)**: 31%

## Preliminary Scorecard Hooks

- Core Feature Adoption: 4/5 - High adoption for primary features (dashboard, tickets, settings)
- Reports Feature: 1/5 - 12% adoption indicates a discovery or value problem
- Support Ticket UX: 3/5 - High usage but long session time suggests friction
- Search Value: 5/5 - Strong correlation between search adoption and reduced support load
- Billing Funnel: 2/5 - 31% drop-off at payment step is a significant conversion problem

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Reports feature low adoption represents investment waste | Medium | High | Product Manager | User research to understand why reports are not being used | 2024-04-30 |
| Billing drop-off reduces portal revenue enablement | High | High | Product Manager | Simplify payment step and add contextual help | 2024-04-30 |
| Long support ticket creation time increases support cost | Medium | Medium | Tech Lead | Conduct session replay analysis to identify friction points | 2024-04-24 |

## Decisions & Next Steps

### Decisions

- Reports feature will go through a user research evaluation in Q2 to determine whether to invest in improving adoption or deprecate
- Billing setup flow simplification is added to Q2 roadmap as a high-priority initiative
- Search adoption target is set at 40% by end of Q2; in-portal search discoverability will be improved

### Action Items

- Product Manager to schedule user research sessions for reports feature evaluation (due 2024-04-25)
- Tech Lead to set up session replay analysis for support ticket creation flow (due 2024-04-24)
- Product Manager to write billing setup simplification spec (due 2024-05-03)

### Follow-ups

- Q2 analytics review scheduled for 2024-07-10
- Reports feature user research findings to be presented at next product team meeting
