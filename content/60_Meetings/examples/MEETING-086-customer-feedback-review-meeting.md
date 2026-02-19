---
id: MEETING-086
type: meeting
title: Customer Feedback Review Meeting
status: approved
owner: Product Manager
created: '2025-04-05T05:26:48.278Z'
updated: '2025-05-08T03:17:01.846Z'
tags:
  - meeting
  - customer-portal
summary: Customer Feedback Review Meeting
company: CustomerPortal
topic: Customer Feedback Review Meeting
meeting_date: '2025-05-09T19:16:49.621Z'
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
- **Topic**: April 2025 Customer Feedback Review - Monthly Analysis Cycle
- **Date/Time**: 2025-05-09 11:00 AM PT
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager
- **Context**: Monthly feedback review meeting using the April data from the feedback analysis process. NPS dropped 4 points month-over-month triggering a focused review session.

## Observations by Domain

- **Feedback Volume**: 847 feedback submissions in April, up 12% from March; increase correlates with the redesign launch of the account overview page
- **Sentiment Analysis**: Overall sentiment is 64% positive, 21% neutral, 15% negative; negative sentiment concentrated in billing-related feedback (38% negative)
- **Top Positive Themes**: Customers praised the new account overview design, faster load times, and improved navigation clarity
- **Top Negative Themes**: Billing page confusion (invoice format not matching customer expectations), slow data export functionality, and difficulty finding audit logs
- **NPS Drivers**: Promoters cite "easy to use" and "fast"; detractors cite "billing is confusing" and "hard to find things"

## Key Metrics & Data Points

- **Monthly feedback submissions**: 847 (up from 756 in March)
- **Overall NPS**: 30 (down from 34 in March, down from 41 one year ago)
- **Negative sentiment rate**: 15% overall; 38% for billing-related feedback
- **Billing feedback volume**: 162 submissions mentioning billing issues
- **Data export complaints**: 28 tickets in April citing slow or failed exports

## Preliminary Scorecard Hooks

- Overall Sentiment: 3/5 - Majority positive but declining NPS is a concern
- Billing Experience: 2/5 - Consistently the top source of negative feedback
- Navigation Improvements: 4/5 - Redesign is landing positively with customers
- Self-Service Capability: 3/5 - Data export and audit log findability are friction points
- Feedback Response Rate: 3/5 - Automated acknowledgments sent but personalized follow-up is inconsistent

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| NPS continues declining if billing issues unresolved | High | High | Product Manager | Prioritize billing page redesign in Phase 2 scope | 2025-05-15 |
| Data export failures drive churn for data-heavy customers | High | Medium | Tech Lead | Investigate export performance and fix as P1 | 2025-05-20 |
| Audit log discoverability causes compliance concerns | Medium | Medium | Product Manager | Add audit log quick-access link to navigation | 2025-05-30 |

## Decisions & Next Steps

### Decisions

- Billing page experience is elevated to a Phase 2 redesign priority; Product Manager to spec new billing invoice format
- Data export performance investigation is a P1 engineering task starting this sprint
- Audit log navigation shortcut added to the portal navigation redesign scope

### Action Items

- Product Manager to draft billing page redesign requirements (due 2025-05-20)
- Tech Lead to investigate data export performance and identify root cause (due 2025-05-16)
- Product Manager to add audit log navigation item to Sprint 25 scope (due 2025-05-12)

### Follow-ups

- May feedback data review scheduled for 2025-06-06
- Billing redesign spec review meeting to be scheduled for 2025-05-22
