---
id: MEETING-082
type: meeting
title: Customer Experience Improvement Workshop
status: approved
owner: Product Manager
created: '2024-03-28T11:25:09.611Z'
updated: '2026-10-16T19:54:56.725Z'
tags:
  - meeting
  - customer-portal
summary: Customer Experience Improvement Workshop
company: CustomerPortal
topic: Customer Experience Improvement Workshop
meeting_date: '2024-03-09T18:52:34.173Z'
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
- **Topic**: CX Improvement Workshop - Reducing Portal Friction and Support Volume
- **Date/Time**: 2024-03-09 10:00 AM PT
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager
- **Context**: Workshop triggered by 18% increase in portal-related support tickets over the past quarter. Goal is to identify top friction points and prioritize UX improvements.

## Observations by Domain

- **Onboarding**: First-time portal login completion rate is 71%; nearly 30% of new customers abandon the setup flow before completing their profile, typically at the billing configuration step
- **Navigation**: Heat map analysis shows customers frequently click on inactive navigation items or take 3+ attempts to find key settings pages
- **Error Messages**: Support tickets frequently reference confusing error messages; the most cited is "Action could not be completed" with no additional context
- **Mobile Usage**: 38% of portal sessions are on mobile devices but the portal is not optimized for mobile; horizontal scrolling exists on 4 critical pages
- **Search**: Customers cannot search across their support tickets or account history; this is the top feature request for the past two quarters

## Key Metrics & Data Points

- **Support ticket volume**: 1,240 portal-related tickets last quarter, up from 1,050 the quarter before
- **First login completion rate**: 71% — 29% abandon before completing account setup
- **Average sessions to find a setting**: 2.4 sessions (target: 1)
- **Mobile session share**: 38% of all portal sessions
- **Top error message frequency**: "Action could not be completed" appeared in 340 support tickets last quarter

## Preliminary Scorecard Hooks

- Onboarding Experience: 2/5 - High abandonment rate on billing step needs immediate attention
- Navigation Usability: 3/5 - Information architecture is reasonable but discoverability is poor
- Error Communication: 2/5 - Error messages are too generic; actionable errors would reduce support volume
- Mobile Experience: 2/5 - Mobile is not a first-class experience; 38% of users are underserved
- Self-Service Capability: 3/5 - Core account actions available but search and history are missing

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Support ticket volume continues increasing | High | High | Product Manager | Prioritize top 3 friction point fixes in Q2 roadmap | 2024-04-01 |
| Mobile experience drives customer churn | High | Medium | Tech Lead | Responsive design audit and mobile-first redesign of 4 broken pages | 2024-04-30 |
| Confusing error messages damage trust | Medium | High | Tech Lead | Implement error message catalog with actionable copy | 2024-04-15 |
| Search absence increases support dependency | Medium | High | Product Manager | Add search to Q2 roadmap as a high-priority feature | 2024-04-01 |

## Decisions & Next Steps

### Decisions

- Onboarding flow billing step will be redesigned to be skippable with in-context guidance; completion is not required to access portal features
- The error message "Action could not be completed" is banned; all error states must use the approved error message catalog
- Mobile responsive fixes for the 4 identified broken pages are treated as P1 bugs, not feature requests

### Action Items

- Product Manager to write onboarding flow redesign spec (due 2024-03-20)
- Tech Lead to audit all error messages against catalog and create fix tickets (due 2024-03-25)
- Tech Lead to assign mobile responsive fixes to the current sprint (due 2024-03-11)

### Follow-ups

- Support ticket volume to be reviewed in 6 weeks; target is 10% reduction
- Customer search feature scoping to begin in Q2 planning
