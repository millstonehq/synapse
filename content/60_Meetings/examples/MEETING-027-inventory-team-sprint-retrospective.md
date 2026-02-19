---
id: MEETING-027
type: meeting
title: Inventory Team Sprint Retrospective
status: approved
owner: Engineering Manager
created: '2024-01-27T06:46:36.520Z'
updated: '2025-08-27T15:46:44.609Z'
tags:
  - meeting
  - inventory-management
summary: Inventory Team Sprint Retrospective
company: InventoryManagement
topic: Inventory Team Sprint Retrospective
meeting_date: '2024-01-16T21:29:08.404Z'
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

- **Project**: Inventory Platform
- **Topic**: Inventory Team Sprint Retrospective
- **Date/Time**: 2024-01-16 3:30 PM CT
- **Attendees (engineering)**: Principal Engineer, Tech Lead, Integration Engineer, Platform Engineer, QA Lead
- **Attendees (product)**: Product Manager, Engineering Manager
- **Context**: End-of-sprint retrospective for the inventory team. Sprint focused on the new warehouse onboarding tooling and the stock discrepancy alerting improvements.

## Observations by Domain

- **Sprint Delivery**: 7 of 9 planned tickets completed; the two incomplete tickets were both blocked by a third-party WMS vendor not responding to credential requests
- **Onboarding Tooling**: The new warehouse onboarding wizard was well-received in user testing; warehouse operations staff found the step-by-step validation checks significantly reduced onboarding errors
- **Discrepancy Alerting**: New discrepancy alerting shipped on day 9 of the sprint; caught two real discrepancy events in production within the first 24 hours, validating the feature
- **Technical Debt**: Two unplanned tech debt tickets were raised mid-sprint due to a production incident; pulled engineer capacity away from planned work
- **Process**: Daily standups were consistently too long (average 18 minutes vs. target 10 minutes); team noted that blocked items were not being escalated quickly enough

## Key Metrics & Data Points

- **Sprint velocity**: 7/9 tickets delivered (78%)
- **Unplanned work (incidents/tech debt)**: 2 tickets (22% of capacity consumed by unplanned work)
- **Discrepancy alerts fired in first 24 hours post-launch**: 2 (both confirmed real issues)
- **Average standup duration**: 18 minutes (target: 10 minutes)
- **Vendor credential response time**: 9 days and counting (blocked 2 tickets)

## Preliminary Scorecard Hooks

- Sprint Delivery: 3/5 - Solid output but external blockers and unplanned work reduced velocity
- Quality: 5/5 - Discrepancy alerting caught real issues immediately; zero post-release defects
- Process Efficiency: 3/5 - Standup duration and blocker escalation need improvement
- External Dependencies: 2/5 - WMS vendor responsiveness is a recurring sprint risk
- Team Wellbeing: 4/5 - Team felt good about the sprint outcome despite the challenges

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Vendor credential delays will block warehouse integration tickets next sprint too | Medium | High | Product Manager | Establish SLA with WMS vendors for credential delivery; escalate to vendor account manager if not met within 3 days | 2024-01-19 |
| Unplanned incident work consuming 20%+ of sprint capacity | Medium | Medium | Engineering Manager | Add 15% buffer for unplanned work in sprint planning; track unplanned vs. planned ratio | 2024-01-22 |
| Standup running long reducing team focus time | Low | High | Tech Lead | Timebox standup strictly at 10 minutes; blockers moved to async channel | 2024-01-17 |

## Decisions & Next Steps

### Decisions

- Sprint planning will include a 15% unplanned work buffer starting next sprint
- Standups will be timeboxed to 10 minutes; blocked items escalated in #inventory-blockers channel before standup
- Product Manager will establish a 3-day credential delivery SLA with all WMS vendors and track compliance

### Action Items

- Set up #inventory-blockers Slack channel and communicate async escalation process (Engineering Manager - 2024-01-17)
- Add 15% unplanned buffer to next sprint capacity calculation (Engineering Manager - 2024-01-22)
- Contact WMS vendor account manager re: outstanding credential request (Product Manager - 2024-01-17)

### Follow-ups

- Check standup duration at next retrospective
- Review unplanned vs. planned work ratio at mid-sprint check-in
- Vendor credential SLA retrospective in 4 weeks
