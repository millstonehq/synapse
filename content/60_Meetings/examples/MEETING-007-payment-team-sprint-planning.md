---
id: MEETING-007
type: meeting
title: Payment Team Sprint Planning
status: approved
owner: Engineering Manager
created: '2025-06-09T01:07:12.810Z'
updated: '2026-12-12T09:11:05.277Z'
tags:
  - meeting
  - payment-processing
summary: Payment Team Sprint Planning
company: PaymentProcessing
topic: Payment Team Sprint Planning
meeting_date: '2026-03-23T11:52:43.270Z'
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

- **Project**: Payment Platform Q1 Sprint
- **Topic**: Payment Team Sprint Planning
- **Date/Time**: 2026-03-23, 11:52 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Bi-weekly sprint planning session to prioritize and size work items for the upcoming two-week sprint

## Observations by Domain

- **Sprint Capacity**: 6 engineers available for the sprint; 1 engineer on PTO for 3 days and 1 engineer on-call for the week
- **Carry-Over Work**: 3 stories carried over from last sprint: reconciliation adapter edge case fixes, Adyen Phase 3 routing config, and fraud model coverage extension
- **New Priorities**: Chargeback ratio dashboard requested by Finance is the top new item; estimated at 3 story points
- **Tech Debt**: Two payment service tech debt items identified in Q4 retrospective are now scheduled: connection pool tuning and error code normalization for the Adyen adapter
- **QA Coverage**: QA Lead notes that the dispute processing path still lacks end-to-end test coverage; requesting 2 story points for test additions this sprint

## Key Metrics & Data Points

- **Sprint Velocity (last 3 sprints)**: 34, 29, 31 story points
- **Backlog Size**: 47 items (14 in current sprint scope)
- **Carry-Over Story Points**: 8 (from last sprint)
- **New Story Points Committed**: 26
- **Total Sprint Commitment**: 34 story points
- **Team Capacity Hours**: 192 hours (adjusted for PTO and on-call)

## Preliminary Scorecard Hooks

- Capacity Planning: 4/5 - Commitment aligns with velocity; PTO impact accounted for
- Backlog Health: 3/5 - 47 items is manageable but tech debt items need consistent scheduling
- QA Coverage: 3/5 - Dispute path gap acknowledged; 2 story points allocated this sprint
- Priority Alignment: 5/5 - Finance chargeback dashboard aligns with Q1 OKR on financial visibility
- Carry-Over Risk: 3/5 - 8 carry-over points is above team's 5-point comfort threshold

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| On-call engineer pulled into incident disrupts sprint | Medium | Medium | Engineering Manager | Pre-identify sprint backup tasks on-call engineer can pick up if capacity freed | 2026-03-25 |
| Adyen Phase 3 routing config blocked by QA sign-off | Low | Medium | QA Lead | Schedule Adyen QA session early in sprint; do not leave for last days | 2026-03-27 |

## Decisions & Next Steps

### Decisions

- 34 story points committed for the sprint; no new items added after planning unless a P1 incident creates an emergency story
- Chargeback ratio dashboard is top priority for Product Manager sign-off upon completion
- Tech debt items are time-boxed: if connection pool tuning exceeds 3 points actual, scope is cut and rescheduled

### Action Items

- Tech Lead to assign all sprint stories in the project tracker before end of day
- QA Lead to schedule Adyen Phase 3 QA session for the first week of the sprint
- Engineering Manager to confirm on-call schedule does not overlap with complex story assignments

### Follow-ups

- Mid-sprint check-in on Wednesday of week 2 to assess carry-over risk
- Retrospective scheduled for end of sprint with emphasis on carry-over root cause
