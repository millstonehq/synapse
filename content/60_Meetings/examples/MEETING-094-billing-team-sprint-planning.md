---
id: MEETING-094
type: meeting
title: Billing Team Sprint Planning
status: deprecated
owner: Engineering Manager
created: '2025-02-12T23:06:51.334Z'
updated: '2026-02-04T17:04:01.023Z'
tags:
  - meeting
  - billing-engine
summary: Billing Team Sprint Planning
company: BillingEngine
topic: Billing Team Sprint Planning
meeting_date: '2025-10-22T16:44:20.514Z'
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

- **Project**: Billing Engine Platform
- **Topic**: Billing Team Sprint Planning (Sprint 34)
- **Date/Time**: 2025-10-22 16:44 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Sprint 34 planning session. Focus areas: completing the billing event schema v2 migration, beginning the tax service async refactor spike, and resolving the invoice generation regression from Sprint 33.

## Observations by Domain

- **Sprint 33 Carry-Over**: Invoice generation regression (INV-4821) was not resolved last sprint — the root cause was identified (race condition in concurrent tax lookups) but the fix requires the async tax refactor, which is still in spike
- **Event Schema Migration**: 4 of 7 consumers have migrated to v2; the remaining 3 are owned by the Notifications, Analytics, and Finance teams — coordination needed this sprint
- **Tax Service Async Spike**: Spike results from last sprint show async pre-computation reduces P99 latency from 4.2s to 340ms; the team is ready to begin implementation
- **Tech Debt**: 12 billing tech debt tickets remain from the Q3 tech debt sprint; 3 are blocking new feature work and need to be addressed before Q4

## Key Metrics & Data Points

- **Sprint 33 velocity**: 42 story points (team target: 48 — below target due to carry-over investigation)
- **Open billing bugs**: 7 (P1: 1, P2: 3, P3: 3)
- **Invoice generation success rate**: 99.1% (SLO: 99.5% — still below target post-regression)
- **Event schema v2 migration progress**: 4/7 consumers migrated (57%)

## Preliminary Scorecard Hooks

- Sprint Execution: 3/5 - Carry-over from regression investigation impacted velocity
- Bug Backlog Health: 3/5 - 1 P1 open, invoice generation success rate below SLO
- Technical Debt: 3/5 - 3 blocking tech debt tickets need resolution before new features
- Cross-Team Coordination: 3/5 - Event schema migration requires 3 external teams to act this sprint

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Invoice generation regression not resolved by sprint end | High | Medium | Tech Lead | Prioritize race condition fix as Sprint 34 P1; pair programming assigned | 2025-10-29 |
| Event schema migration blocked by external teams | Medium | Medium | Engineering Manager | Schedule migration sessions with Notifications and Analytics teams this week | 2025-10-25 |
| Tax async refactor scope creep | Medium | Low | Principal Engineer | Time-box implementation to 2 weeks; defer optimization to Sprint 35 | 2025-11-05 |

## Decisions & Next Steps

### Decisions

- INV-4821 (invoice generation race condition) is Sprint 34 P1 — no new feature work begins until this is resolved
- Tax async refactor implementation begins Sprint 34 with a strict 2-week time-box
- Engineering Manager will unblock event schema migration by coordinating directly with external team leads

### Action Items

- Tech Lead: Pair with QA Lead on INV-4821 root cause fix by 2025-10-25
- Principal Engineer: Begin tax async refactor implementation with scope-limited PR by 2025-10-29
- Engineering Manager: Schedule event schema migration sessions with Notifications and Analytics by 2025-10-24

### Follow-ups

- Daily standup check-in on INV-4821 status until resolved
- Sprint 34 mid-sprint review: 2025-10-29
