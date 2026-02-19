---
id: MEETING-017
type: meeting
title: Auth Team Sprint Retrospective
status: approved
owner: Product Manager
created: '2025-02-22T11:41:56.984Z'
updated: '2026-04-02T06:15:22.642Z'
tags:
  - meeting
  - user-authentication
summary: Auth Team Sprint Retrospective
company: UserAuthentication
topic: Auth Team Sprint Retrospective
meeting_date: '2026-08-10T07:19:49.333Z'
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

- **Project**: Auth Service Platform
- **Topic**: Auth Team Sprint Retrospective — Sprint 24
- **Date/Time**: 2026-08-10 2:00 PM CT
- **Attendees (engineering)**: Principal Engineer, Tech Lead, QA Lead
- **Attendees (product)**: Product Manager, Engineering Manager
- **Context**: End-of-sprint retrospective for Sprint 24 which included JWT key rotation automation delivery, MFA enforcement rollout, and OAuth scope simplification Phase 1.

## Observations by Domain

- **Delivery**: JWT key rotation automation delivered on time; MFA enforcement rollout had a 2-day delay due to a last-minute edge case in service account handling discovered in staging
- **Quality**: No production incidents this sprint; 2 bugs caught in code review that would have caused authentication failures in edge cases
- **Process**: Change ticket approval process is causing average 1.5-day lag for auth deployments; team feels this is slowing velocity on small, low-risk changes
- **Collaboration**: Coordination with the enterprise customer team for MFA rollout went smoothly; advance communication with customers was well-received
- **Technical Debt**: Session cleanup job performance improvement was descoped again this sprint; it has been delayed 3 sprints in a row and should be prioritized

## Key Metrics & Data Points

- **Sprint velocity**: 42 story points (planned: 46)
- **Bugs found in production**: 0
- **Bugs caught pre-production**: 2
- **Average change ticket approval time**: 1.5 days
- **Sprint goals met**: 2 of 3 (MFA rollout delayed by 2 days)

## Preliminary Scorecard Hooks

- Delivery Reliability: 3/5 - One goal delayed; root cause was a staging test gap, not planning failure
- Code Quality: 5/5 - Zero production bugs; 2 pre-production catches; test coverage improving
- Process Efficiency: 3/5 - Change ticket lag is a friction point worth addressing for low-risk changes
- Technical Debt Management: 2/5 - Session cleanup job has been delayed 3 sprints; needs to be a sprint commitment

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Session cleanup job delay causes database performance degradation | High | Medium | Tech Lead | Commit to session cleanup as a sprint 25 must-do | 2026-08-24 |
| Change ticket lag slows response to security patches | Medium | Medium | Engineering Manager | Create expedited review path for security-classified changes | 2026-08-17 |
| Staging test gap repeated for service account edge cases | Medium | Low | QA Lead | Add service account scenarios to the standard staging test suite | 2026-08-17 |

## Decisions & Next Steps

### Decisions

- Session cleanup job will be a committed deliverable in Sprint 25; no further deferral
- Expedited change ticket review path for security patches will be proposed to the change management process owner

### Action Items

- Add session cleanup job to Sprint 25 commitment (Tech Lead — 2026-08-11)
- Draft expedited change review proposal for security-classified auth changes (Engineering Manager — 2026-08-17)
- Add service account scenarios to staging test suite (QA Lead — 2026-08-17)

### Follow-ups

- Sprint 25 planning includes session cleanup as a committed item — confirmed in planning session
- Change management process review meeting to be scheduled with Platform Lead
