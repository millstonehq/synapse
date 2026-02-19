---
id: MEETING-076
type: meeting
title: On-Call Process Retrospective
status: review
owner: Principal Engineer
created: '2025-09-24T13:40:24.877Z'
updated: '2026-03-23T21:16:48.128Z'
tags:
  - meeting
  - monitoring-stack
summary: On-Call Process Retrospective
company: MonitoringStack
topic: On-Call Process Retrospective
meeting_date: '2026-06-03T15:33:10.334Z'
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

- **Project**: Monitoring Stack — On-Call Process Review
- **Topic**: On-Call Process Retrospective
- **Date/Time**: 2026-06-03 3:33 PM UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Quarterly on-call retrospective covering the prior quarter's incidents, alert quality, and on-call engineer experience. Focus on reducing night-time pages and improving handoff quality.

## Observations by Domain

- **Night-Time Paging**: 38% of P1 pages occurred between 10pm and 6am local time; 7 of these were later assessed as P2 or lower — engineers are being woken up unnecessarily
- **Handoff Quality**: 40% of handoff notes reviewed were incomplete (missing active incidents or recent change summaries); the handoff process is not being consistently followed
- **Runbook Coverage**: Runbooks are missing for 4 P1 alerts added in the last quarter; on-call engineers are improvising responses which increases MTTR
- **Rotation Fairness**: Two engineers have been on-call 5 of the last 8 weeks due to rotation coverage issues; burnout risk is high
- **Post-Incident Follow-Through**: Only 60% of post-incident action items from the prior quarter have been completed; repeat incidents from the same root causes are occurring

## Key Metrics & Data Points

- **Total on-call pages (last quarter)**: 312
- **Night-time pages (10pm–6am)**: 118 (38%)
- **Night pages assessed as false P1**: 7 of 118 (6%)
- **Mean MTTA (last quarter)**: 7.1 minutes (target: 5 minutes)
- **Handoff notes rated "complete"**: 60% (target: 95%)
- **Post-incident action item completion rate**: 60% (target: 90%)

## Preliminary Scorecard Hooks

- On-Call Fairness: 2/5 - Distribution is uneven; two engineers carrying disproportionate load
- Handoff Quality: 2/5 - 40% incomplete; formal handoff checklist not being used consistently
- Runbook Coverage: 3/5 - Most P1 alerts have runbooks; 4 recent additions are missing
- MTTA: 3/5 - 7.1 minutes vs. 5-minute target; improving but not yet at target
- Post-Incident Follow-Through: 2/5 - 60% completion rate; repeat incidents from unresolved root causes

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| On-call burnout for overloaded engineers leads to turnover | High | Medium | Engineering Manager | Rebalance rotation immediately; enforce max 1 week in 4 policy | 2026-06-10 |
| Missing runbooks cause extended MTTR for new P1 alerts | Medium | High | Tech Lead | Runbook required before any new P1 alert is deployed; enforce in CI | 2026-06-17 |
| Incomplete handoffs lead to missed incidents during shift transitions | Medium | Medium | Principal Engineer | Make handoff checklist a required form in the on-call tool; auto-remind 1 hour before rotation | 2026-06-24 |

## Decisions & Next Steps

### Decisions

- Mandatory handoff checklist to be implemented in the on-call tooling before the next rotation cycle starts
- No new P1 alert may be merged to the AlertManager config without a runbook URL in CI linting
- Engineering Manager to rebalance the rotation immediately and enforce the max-1-in-4 policy

### Action Items

- Principal Engineer to implement handoff checklist enforcement in the on-call tool (due 2026-06-17)
- Tech Lead to write runbooks for the 4 P1 alerts missing them (due 2026-06-10)
- Engineering Manager to audit and rebalance the on-call rotation schedule (due 2026-06-10)

### Follow-ups

- Check handoff completion rate after 2 full rotation cycles
- Review post-incident action item completion rate at next monthly engineering review
