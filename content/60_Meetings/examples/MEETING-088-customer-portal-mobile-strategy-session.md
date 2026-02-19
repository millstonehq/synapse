---
id: MEETING-088
type: meeting
title: Customer Portal Mobile Strategy Session
status: proposed
owner: Product Manager
created: '2025-02-11T21:06:01.004Z'
updated: '2025-05-24T15:07:33.230Z'
tags:
  - meeting
  - customer-portal
summary: Customer Portal Mobile Strategy Session
company: CustomerPortal
topic: Customer Portal Mobile Strategy Session
meeting_date: '2025-10-10T11:00:48.977Z'
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
- **Topic**: Mobile Strategy Session - Responsive Web vs. Native App Decision
- **Date/Time**: 2025-10-10 11:00 AM PT
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager
- **Context**: 42% of portal sessions are now on mobile; mobile experience has been identified as a top driver of negative NPS. This session is to align on the mobile strategy before committing to the Q4 roadmap.

## Observations by Domain

- **Current Mobile State**: The portal is technically responsive but was not designed mobile-first; 6 pages have horizontal scroll on mobile, and touch targets are frequently too small on the account management pages
- **Usage Patterns**: Mobile users primarily access the portal for support ticket status, invoice downloads, and quick account checks; they are not using complex features like reporting or bulk operations
- **Native App Appetite**: Customer success team reports 15 enterprise customers have requested a mobile app; smaller customers show no preference in surveys
- **Technical Investment**: A full mobile-first responsive redesign is estimated at 4 sprints; a native app (React Native) is estimated at 6-8 months with ongoing maintenance cost
- **Progressive Web App**: A PWA approach with offline capability and home screen installation could address many mobile use cases at lower cost than a native app

## Key Metrics & Data Points

- **Mobile session share**: 42% of all portal sessions
- **Mobile usability score**: 2.6/5 in latest usability research
- **Pages with mobile issues**: 6 pages with horizontal scroll; 12 pages with undersized touch targets
- **Enterprise customers requesting native app**: 15 of 240 enterprise accounts
- **Estimated responsive redesign cost**: 4 sprints (~8 weeks)
- **Estimated native app cost**: 6-8 months + ongoing maintenance

## Preliminary Scorecard Hooks

- Current Mobile UX: 2/5 - Multiple functional issues affecting 42% of sessions
- Native App Demand: 2/5 - Demand exists but is concentrated in a small customer segment
- PWA Viability: 4/5 - PWA can address most use cases at reasonable cost
- Responsive Fix Urgency: 4/5 - 6 broken pages are immediately actionable and high value
- Strategic Clarity: 3/5 - Decision between responsive, PWA, and native needs resolution

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Mobile UX degradation drives churn | High | High | Product Manager | Prioritize mobile-first redesign for Q4 regardless of native app decision | 2025-10-17 |
| Native app decision delays mobile improvements | Medium | High | Product Manager | Decouple responsive improvements from native app strategy decision | 2025-10-17 |
| PWA not sufficient for enterprise requirements | Medium | Medium | Principal Engineer | Survey the 15 requesting enterprise accounts on minimum requirements | 2025-10-24 |

## Decisions & Next Steps

### Decisions

- Responsive mobile improvements for the 6 broken pages are approved immediately; not contingent on native app decision
- Native app vs. PWA decision is deferred until enterprise customer requirements are surveyed
- Mobile-first design approach is adopted for all future portal pages and redesigned pages

### Action Items

- Tech Lead to scope and schedule responsive fixes for 6 broken pages in Q4 sprint planning (due 2025-10-17)
- Product Manager to survey the 15 enterprise customers requesting native app for requirements (due 2025-10-24)
- Principal Engineer to produce a PWA feasibility assessment with scope and effort estimate (due 2025-10-31)

### Follow-ups

- Native app vs. PWA decision meeting scheduled for 2025-11-07 after survey results
- Mobile-first design principles to be added to the portal design system documentation
