---
id: MEETING-081
type: meeting
title: Customer Portal Architecture Review
status: accepted
owner: Product Manager
created: '2025-11-18T03:37:04.627Z'
updated: '2026-12-09T18:21:35.582Z'
tags:
  - meeting
  - customer-portal
summary: Customer Portal Architecture Review
company: CustomerPortal
topic: Customer Portal Architecture Review
meeting_date: '2025-03-25T09:33:59.665Z'
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
- **Topic**: Quarterly Architecture Review - Portal Scalability and Technical Debt
- **Date/Time**: 2025-03-25 9:30 AM PT
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager
- **Context**: Quarterly architecture review ahead of planned portal redesign initiative. Current portal supports 12,000 active customers; target is 50,000 by end of year.

## Observations by Domain

- **Frontend Architecture**: Next.js App Router migration is 60% complete; remaining pages still on Pages Router causing inconsistent data fetching patterns and bundle splitting challenges
- **API Layer**: BFF API has grown to 87 endpoints without a consistent versioning strategy; several endpoints are tightly coupled to UI-specific data shapes
- **Authentication**: SSO integration is solid but session management has three separate implementations across different portal sections; should be unified
- **Performance**: Core Web Vitals are passing targets on the dashboard but the account management section consistently scores below LCP threshold on slower connections
- **Observability**: Structured logging is inconsistent; some portal services emit JSON logs while others emit plain text, making correlation difficult in Datadog

## Key Metrics & Data Points

- **Portal active users**: 12,400 monthly active users, up 34% YoY
- **P95 API latency**: 620ms against an 800ms target; headroom is shrinking
- **Frontend bundle size**: Initial bundle at 218KB gzipped; 32KB below limit but trending up
- **Error rate**: 0.4% overall, with the billing section at 1.2% (above policy threshold)
- **SSO login success rate**: 97.8% — 2.2% of login attempts fail requiring support intervention

## Preliminary Scorecard Hooks

- Frontend Architecture: 3/5 - App Router migration in progress but split codebase creates inconsistencies
- API Design: 3/5 - Functional but lacks versioning strategy and accumulating technical debt
- Authentication: 4/5 - SSO works well, session unification needed
- Performance: 3/5 - Meets most targets but billing section needs attention
- Observability: 2/5 - Inconsistent logging and alerting coverage gaps

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| P95 latency breaches SLA threshold at 50k users | High | High | Principal Engineer | Implement API response caching and DB query optimization | 2025-05-15 |
| Billing section error rate exceeds policy threshold | High | Medium | Tech Lead | Root cause investigation and fix for billing API errors | 2025-04-10 |
| App Router migration creates regression risk | Medium | Medium | Tech Lead | Feature-by-feature migration with comprehensive test coverage | 2025-06-30 |
| Inconsistent logging delays incident diagnosis | Medium | High | Principal Engineer | Enforce structured logging standard across all portal services | 2025-04-30 |

## Decisions & Next Steps

### Decisions

- App Router migration is the top engineering priority for Q2; Pages Router pages must be fully migrated before the redesign begins
- A portal API versioning strategy (URL versioning with `/v1/`, `/v2/` prefixes) will be adopted for all new endpoints
- Billing section error rate investigation is escalated to a P2 engineering task for this sprint

### Action Items

- Tech Lead to create billing API error investigation ticket and assign to frontend engineer (due 2025-04-02)
- Principal Engineer to draft API versioning ADR for team review (due 2025-04-08)
- Principal Engineer to add structured logging enforcement to CI pipeline (due 2025-04-30)

### Follow-ups

- Next architecture review scheduled for 2025-06-24
- Weekly App Router migration progress check-in added to engineering standup
