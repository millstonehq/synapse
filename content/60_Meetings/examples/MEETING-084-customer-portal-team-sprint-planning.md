---
id: MEETING-084
type: meeting
title: Customer Portal Team Sprint Planning
status: accepted
owner: Product Manager
created: '2024-10-19T21:10:10.954Z'
updated: '2026-03-21T20:45:03.387Z'
tags:
  - meeting
  - customer-portal
summary: Customer Portal Team Sprint Planning
company: CustomerPortal
topic: Customer Portal Team Sprint Planning
meeting_date: '2026-03-22T08:11:51.883Z'
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
- **Topic**: Sprint 24 Planning - Redesign Phase 1 Kickoff
- **Date/Time**: 2026-03-22 8:00 AM PT
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager
- **Context**: Sprint planning for the first sprint of the portal redesign initiative. Team velocity from previous 3 sprints is averaging 42 story points.

## Observations by Domain

- **Redesign Readiness**: Design mockups for the dashboard and account overview pages are finalized and ready for implementation; navigation redesign mockups are still in review and not ready for this sprint
- **Technical Debt**: Two accessibility debt items from the audit are blocking redesign work on the notifications panel; they must be resolved before the new notification design can be implemented
- **QA Coverage**: QA Lead flagged that the current E2E test suite covers 65% of critical customer paths; test coverage gaps need to be addressed in parallel with new feature development
- **Performance Baseline**: Before redesign work ships, a Lighthouse performance baseline has been captured for comparison; engineers must run comparison before merging redesign PRs
- **Engineering Capacity**: One engineer is out for 3 days this sprint; capacity is approximately 34 story points

## Key Metrics & Data Points

- **Team velocity (3-sprint average)**: 42 story points
- **Adjusted sprint capacity**: 34 story points (one engineer PTO)
- **E2E test coverage**: 65% of critical paths
- **Redesign mockups ready**: 2 of 5 planned pages (dashboard, account overview)
- **Accessibility debt tickets**: 2 blocking items identified in audit

## Preliminary Scorecard Hooks

- Sprint Readiness: 3/5 - Blocked on navigation mockups; two pages are ready to proceed
- Capacity Planning: 4/5 - Realistic capacity adjustment made for PTO
- QA Coverage: 2/5 - 65% coverage is below target; risk of regressions during redesign
- Technical Debt: 3/5 - Accessibility blockers identified and scoped; manageable this sprint
- Performance Tracking: 4/5 - Baseline captured; comparison process defined

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Navigation mockup delay blocks Sprint 25 work | Medium | Medium | Product Manager | Escalate to design lead for priority completion by sprint end | 2026-03-29 |
| Redesign introduces accessibility regressions | High | Medium | Tech Lead | Pair each redesign PR with an axe-core and manual keyboard test | Ongoing |
| E2E coverage gap causes undetected regressions | Medium | High | QA Lead | Add E2E test writing to sprint as a parallel workstream | 2026-04-05 |

## Decisions & Next Steps

### Decisions

- Sprint 24 scope: dashboard redesign (13 pts), account overview redesign (10 pts), accessibility debt resolution (8 pts), and E2E test additions (5 pts); total 36 pts (close to adjusted capacity)
- Navigation redesign is deferred to Sprint 25 pending mockup completion
- Every redesign PR requires a Lighthouse comparison screenshot in the PR description

### Action Items

- Product Manager to follow up with design on navigation mockup ETA (due 2026-03-24)
- Tech Lead to assign accessibility debt tickets to engineers at sprint start (due 2026-03-22)
- QA Lead to create E2E test backlog for highest-risk customer paths (due 2026-03-25)

### Follow-ups

- Sprint 24 demo scheduled for 2026-04-05
- Sprint 25 planning pre-work: navigation mockup must be complete by 2026-04-03
