---
id: MEETING-085
type: meeting
title: Customer Portal Redesign Kickoff
status: review
owner: Principal Engineer
created: '2024-04-29T10:51:28.462Z'
updated: '2026-07-02T13:38:02.965Z'
tags:
  - meeting
  - customer-portal
summary: Customer Portal Redesign Kickoff
company: CustomerPortal
topic: Customer Portal Redesign Kickoff
meeting_date: '2025-03-22T17:30:52.146Z'
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
- **Topic**: Portal Redesign Kickoff - Scope, Timeline, and Technical Approach
- **Date/Time**: 2025-03-22 9:30 AM PT
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager
- **Context**: Kickoff meeting for the Q2 Customer Portal redesign initiative. Redesign is motivated by customer feedback (NPS decline), mobile experience gaps, and the need to support upcoming self-service features.

## Observations by Domain

- **Design System**: The current portal uses an ad-hoc component library; the redesign will adopt the new design system with Radix UI primitives, improving consistency and reducing long-term maintenance cost
- **Mobile Strategy**: The redesign will be mobile-first for the first time; existing pages were retrofitted for mobile and consistently score poorly in usability testing
- **Feature Scope**: The redesign covers the dashboard, navigation, account management, billing, and support ticket views; notifications and reporting are out of scope for this phase
- **Migration Strategy**: Pages will be migrated incrementally using Next.js parallel routes to avoid a big-bang cutover; customers can be on old or new design simultaneously during migration
- **Accessibility**: The redesign represents a reset opportunity; every new page must meet WCAG 2.1 AA before shipping, and no accessibility technical debt will be carried forward

## Key Metrics & Data Points

- **Portal NPS**: 34 (down from 41 one year ago)
- **Mobile usability score**: 2.4/5 in most recent customer research sessions
- **Pages in scope**: 12 pages across 4 functional areas
- **Estimated engineering effort**: 8 sprints (16 weeks)
- **Design system components ready**: 28 of 35 needed components are complete

## Preliminary Scorecard Hooks

- Design Readiness: 4/5 - Design system mostly complete; 7 components still needed
- Technical Approach: 4/5 - Incremental migration de-risks the cutover; parallel routes pattern is proven
- Accessibility Plan: 5/5 - Clear commitment to WCAG 2.1 AA with no debt carryover
- Mobile Strategy: 4/5 - Mobile-first approach is the right call; needs explicit testing protocol
- Timeline Realism: 3/5 - 8 sprints is achievable but has no buffer for scope creep or unexpected complexity

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Missing design system components delay engineering | Medium | Medium | Tech Lead | Identify needed components and prioritize with design team immediately | 2025-03-29 |
| Incremental migration creates long-running UX inconsistency | Medium | High | Product Manager | Define maximum migration window (6 sprints max before full cutover) | 2025-03-29 |
| Scope creep delays target completion | High | Medium | Product Manager | Freeze scope for Phase 1; new requests go to Phase 2 backlog | Ongoing |
| Accessibility debt introduced during velocity pressure | High | Medium | Principal Engineer | Accessibility review is a required PR gate; no exceptions | Ongoing |

## Decisions & Next Steps

### Decisions

- Redesign is officially kicked off; Sprint 23 (starting 2025-03-31) is the first implementation sprint
- Mobile-first approach is adopted; all new pages must pass Lighthouse mobile score of 80+
- Scope for Phase 1 is frozen: dashboard, navigation, account management, billing, support tickets

### Action Items

- Tech Lead to identify the 7 missing design system components and create tickets for the design team (due 2025-03-27)
- Product Manager to draft the Phase 1 scope document and get stakeholder sign-off (due 2025-03-28)
- Principal Engineer to set up the parallel routes infrastructure for incremental migration (due 2025-04-04)

### Follow-ups

- Weekly redesign sync added to team calendar for duration of initiative
- Phase 1 target completion date: 2025-07-25 (end of Sprint 30)
