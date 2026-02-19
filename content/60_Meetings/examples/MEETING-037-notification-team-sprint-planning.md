---
id: MEETING-037
type: meeting
title: Notification Team Sprint Planning
status: approved
owner: Product Manager
created: '2025-10-01T07:19:44.793Z'
updated: '2025-08-08T14:52:43.091Z'
tags:
  - meeting
  - notification-service
summary: Notification Team Sprint Planning
company: NotificationService
topic: Notification Team Sprint Planning
meeting_date: '2026-04-16T19:41:40.068Z'
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

- **Project**: Notification Service - Sprint Planning (Sprint 24)
- **Topic**: Notification Team Sprint Planning
- **Date/Time**: 2026-04-16 19:41 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Sprint 24 planning for the Notification Service team. Carries over 3 items from Sprint 23 due to the email deliverability incident that consumed 40% of sprint capacity.

## Observations by Domain

- **Carryover Items**: Token cleanup job (Sprint 23 carry), DMARC enforcement migration (Sprint 23 carry), and the rate limiting TDD (new work partially researched in Sprint 23)
- **Incident Follow-up**: Sprint 23 email deliverability incident generated 4 action items; 2 must be completed this sprint to close the post-mortem
- **Capacity**: 5 engineers × 8 story points = 40 points capacity; 3 carry-over items consume ~18 points leaving 22 for new work
- **New Work Priority**: Product wants the deferred-delivery feature for time-of-day send windows; estimated 8 points; fits within capacity if incident work completes on schedule
- **QA Automation Gap**: QA Lead flagged that end-to-end tests for the SMS failover path are missing; estimated 5 points of test authoring work

## Key Metrics & Data Points

- **Sprint 23 velocity**: 28 story points (40 planned; 12 lost to incident)
- **Open action items from email incident post-mortem**: 4 (2 must close this sprint)
- **Sprint 24 capacity**: 40 story points (5 engineers, 2-week sprint)
- **Carry-over points**: 18 (token cleanup 5, DMARC migration 8, rate limiting TDD 5)
- **Available for new work**: 22 story points

## Preliminary Scorecard Hooks

- Sprint Scope Confidence: 3/5 - Carry-over manageable but incident work adds risk
- Technical Debt Backlog: 3/5 - 4 open post-mortem items, 2 critical for this sprint
- QA Coverage: 2/5 - SMS failover path has no automated test coverage
- Product Feature Delivery: 3/5 - Time-of-day send windows fits capacity if carryover completes
- Team Health: 4/5 - Good velocity recovery expected; no on-call disruptions anticipated

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Post-mortem action items slip again due to feature pressure | High | Medium | Product Manager | Block feature work until both critical action items are done | Sprint Day 5 |
| DMARC enforcement migration causes legitimate mail failures | Medium | Low | Tech Lead | Maintain 48h monitoring window after enforcement goes live | 2026-04-25 |

## Decisions & Next Steps

### Decisions

- The two critical post-mortem action items are sprint blockers — no new features start until they are done
- Time-of-day send windows feature is in-scope if carryover completes by sprint midpoint
- QA SMS failover test authoring is added to sprint backlog at 5 points

### Action Items

- Principal Engineer owns post-mortem action item 1: secondary IP warmup verification (by Sprint Day 4)
- Tech Lead owns post-mortem action item 2: DMARC enforcement go-live with monitoring (by Sprint Day 5)
- QA Lead to begin SMS failover test authoring in parallel with engineering work

### Follow-ups

- Sprint midpoint check-in to assess capacity for time-of-day send windows feature
- Post-mortem formally closed once both action items are verified complete
