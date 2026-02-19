---
id: MEETING-056
type: meeting
title: Data Team Sprint Planning
status: approved
owner: Product Manager
created: '2024-09-30T23:06:01.055Z'
updated: '2025-08-09T01:36:06.132Z'
tags:
  - meeting
  - data-pipeline
summary: Data Team Sprint Planning
company: DataPipeline
topic: Data Team Sprint Planning
meeting_date: '2026-09-12T15:20:35.641Z'
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

- **Project**: Data Platform Engineering
- **Topic**: Data Team Sprint Planning
- **Date/Time**: 2026-09-12 10:00 AM PT
- **Attendees (engineering)**: Principal Engineer, Tech Lead, Data Platform Lead
- **Attendees (product)**: Product Manager, Engineering Manager
- **Context**: Sprint 34 planning for the data platform team; 2-week sprint cycle covering pipeline work, infrastructure, and data quality improvements.

## Observations by Domain

- **Pipeline Backlog**: 12 stories in the ready state; 6 are data quality improvements, 4 are new pipeline development, 2 are infrastructure work.
- **Carry-over from Sprint 33**: 2 stories carrying over — Iceberg migration for the orders table and the schema compatibility CI integration; both are 80% complete.
- **Capacity**: 4 engineers at full capacity; one engineer at 50% due to on-call overlap week 1.
- **Blockers**: The orders Iceberg migration is blocked on a data governance approval for the PII classification change; owner is following up this week.
- **Technical Debt**: Data quality team requested 1 day per engineer for test coverage improvements; agreed to allocate 20% of sprint to tech debt.
- **Incidents Review**: 1 P2 incident in Sprint 33 (schema compatibility failure); 3 hours to resolve. Post-incident action items are in the backlog.

## Key Metrics & Data Points

- **Sprint velocity (last 3 sprints)**: 42, 38, 45 story points
- **Stories ready for sprint**: 12
- **Carry-over stories**: 2 (partially complete)
- **Team capacity this sprint**: 3.5 FTE effective
- **Tech debt allocation**: 20% of sprint capacity
- **Open P2+ incidents with open action items**: 1

## Preliminary Scorecard Hooks

- Backlog Health: 4/5 - Strong ready queue; good mix of new work and quality improvements
- Capacity Utilization: 3/5 - Reduced capacity week 1 due to on-call overlap
- Carry-over Rate: 4/5 - Only 2 stories carrying over; both nearly complete
- Incident Action Item Closure: 3/5 - 1 open P2 action item needs to be scheduled this sprint
- Tech Debt Balance: 4/5 - 20% allocation is healthy for current debt level

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Orders Iceberg migration blocked by governance approval | Medium | High | Tech Lead | Escalate governance review; schedule conditional on approval by day 3 | 2026-09-14 |
| Reduced capacity week 1 may delay schema CI integration | Low | Medium | Principal Engineer | Prioritize schema CI integration in week 2 if week 1 is light | 2026-09-19 |
| P2 incident action item may slip without explicit scheduling | Medium | Medium | Data Platform Lead | Add action item story to sprint commitment explicitly | 2026-09-12 |

## Decisions & Next Steps

### Decisions

- Sprint 34 commitment: Iceberg migration, schema CI integration, 3 data quality gates, and P2 incident action item
- Tech debt allocation of 20% (approximately 1.5 days per engineer) is approved for this sprint
- On-call overlap is acknowledged; Principal Engineer will carry reduced story count week 1

### Action Items

- Confirm governance approval status for orders table PII classification (Tech Lead - 2026-09-14)
- Add P2 incident action item to sprint board as a committed story (Data Platform Lead - 2026-09-12)
- Send sprint 34 commitment summary to stakeholders (Product Manager - 2026-09-12)

### Follow-ups

- Mid-sprint check-in on day 5 to assess if carry-over stories are on track
- Retrospective scheduled for end of sprint with focus on incident response improvement
