---
id: MEETING-074
type: meeting
title: Monitoring Team Sprint Planning
status: approved
owner: Product Manager
created: '2024-08-25T18:42:40.252Z'
updated: '2026-03-10T02:41:45.386Z'
tags:
  - meeting
  - monitoring-stack
summary: Monitoring Team Sprint Planning
company: MonitoringStack
topic: Monitoring Team Sprint Planning
meeting_date: '2024-09-12T17:56:33.906Z'
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

- **Project**: Monitoring Stack — Sprint 24 Planning
- **Topic**: Monitoring Team Sprint Planning
- **Date/Time**: 2024-09-12 5:56 PM UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Two-week sprint planning session for the platform monitoring team. Sprint focus is completing the SLO framework rollout and reducing alert fatigue.

## Observations by Domain

- **Backlog Health**: 34 open tickets; 9 are P1 (blocking other teams); 12 are P2; carryover from last sprint is 3 tickets
- **SLO Rollout**: 14 of 23 services have SLOs defined and configured; remaining 9 services are scheduled for onboarding in this sprint
- **Alert Tuning**: Alert action rate improved from 47% to 54% after last sprint's tuning work; still below the 70% target
- **Platform Reliability**: Prometheus had one brief storage incident last sprint (30-minute gap); post-incident remediation is in the backlog
- **Capacity**: Team is at full capacity; no slack for unplanned work this sprint

## Key Metrics & Data Points

- **Velocity (last 3 sprints)**: 42, 38, 45 story points
- **Sprint capacity (this sprint)**: 40 story points (1 engineer on PTO for 3 days)
- **Backlog size**: 34 tickets, estimated total of 156 story points
- **P1 backlog items**: 9 tickets blocking service team onboarding
- **Alert action rate trend**: 47% → 54% (improving but below 70% target)

## Preliminary Scorecard Hooks

- Sprint Health: 3/5 - Healthy velocity but at capacity; unplanned work will push items to next sprint
- Backlog Grooming: 3/5 - Backlog is well-prioritized but growing; P1 items are blocked on platform work
- SLO Rollout Progress: 4/5 - 61% complete; on track for end-of-quarter completion
- Alert Quality Trend: 3/5 - Improving but still below target; more tuning work needed
- Technical Debt: 2/5 - Prometheus storage incident root cause fix is unaddressed; risk of recurrence

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Prometheus storage incident recurs before root cause fix is deployed | High | Medium | Tech Lead | Prioritize storage fix in sprint backlog; allocate 5 story points | 2024-09-20 |
| 9 remaining SLO onboardings take longer than estimated | Medium | Medium | Product Manager | Add buffer sprint for SLO onboarding; communicate updated timeline to service teams | 2024-09-26 |
| Unplanned on-call work disrupts sprint commitments | Low | High | Engineering Manager | Reserve 10% capacity for unplanned work; do not commit to full velocity | 2024-09-26 |

## Decisions & Next Steps

### Decisions

- Prometheus storage root cause fix is P0 for this sprint; it is not negotiable and cannot be pushed
- Commit to completing SLO onboarding for 6 of the 9 remaining services; defer 3 to next sprint
- Alert tuning work is allocated 8 story points this sprint (20% of capacity)

### Action Items

- Tech Lead to implement and deploy Prometheus storage fix by 2024-09-20
- Principal Engineer to complete SLO onboarding sessions for 6 service teams by 2024-09-24
- QA Lead to write test cases for burn rate alert configuration validation by 2024-09-19

### Follow-ups

- Sprint retrospective scheduled for 2024-09-26 at 4pm UTC
- Mid-sprint check-in on SLO onboarding progress (2024-09-19)
