---
id: MEETING-091
type: meeting
title: Billing Engine Architecture Review
status: approved
owner: Product Manager
created: '2025-09-13T05:02:34.732Z'
updated: '2026-06-20T10:25:48.596Z'
tags:
  - meeting
  - billing-engine
summary: Billing Engine Architecture Review
company: BillingEngine
topic: Billing Engine Architecture Review
meeting_date: '2026-06-04T16:44:48.694Z'
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
- **Topic**: Billing Engine Architecture Review
- **Date/Time**: 2026-06-04 16:44 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager
- **Context**: Quarterly architecture review to assess billing engine health ahead of the multi-currency expansion milestone. Focus on scalability of invoice generation pipeline and event schema stability.

## Observations by Domain

- **Invoice Generation**: Batch invoice generation is meeting SLA for current account volume (15,000 accounts in under 2 hours) but projections show it will breach the 4-hour window target at 40,000 accounts without parallelization improvements
- **Event Schema**: The billing event schema is stable at v2.1 but three legacy v1 consumers remain — these must be migrated before v1 is deprecated
- **Tax Calculation**: Tax service latency P99 has crept to 4.2 seconds on complex multi-jurisdiction accounts; the current synchronous call pattern will become a bottleneck during the EU expansion
- **Database**: Billing DB index health is good; usage_events table is at 380M rows and will benefit from partitioning by `occurred_at` before Q4

## Key Metrics & Data Points

- **Invoice generation throughput**: 7,400 invoices/hour (target: 10,000/hour)
- **Billing API P95 latency**: 340ms (SLO: 500ms)
- **Tax service P99 latency**: 4,200ms (threshold: 3,000ms — needs attention)
- **Billing event consumer lag (peak)**: 12,000 messages (recovers within 45 minutes)
- **Monthly billed volume**: $4.2M across 15,200 active accounts

## Preliminary Scorecard Hooks

- Invoice Generation Pipeline: 3/5 - Meets current SLA but parallelization needed before 40k account milestone
- Event Architecture: 4/5 - Schema stable, v1 deprecation timeline is the primary risk
- Tax Integration: 3/5 - Functional but P99 latency is above threshold and will worsen with EU expansion
- Database Health: 4/5 - Healthy today, usage_events table partitioning needed before Q4 growth

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Invoice generation throughput breach at 40k accounts | High | Medium | Tech Lead | Implement parallel invoice generation batches (TDD required) | 2026-08-15 |
| Tax service P99 above threshold | Medium | High | Principal Engineer | Async tax calculation with pre-computation for known jurisdictions | 2026-07-30 |
| Legacy v1 event consumers block schema evolution | Medium | Medium | Engineering Manager | Audit v1 consumers and set deprecation deadline with owning teams | 2026-07-01 |

## Decisions & Next Steps

### Decisions

- Invoice generation parallelization TDD is prioritized for Q3 sprint planning
- Tax calculation will move to async pre-computation model for batch billing runs; synchronous calls retained for on-demand invoice generation only
- v1 billing event schema deprecation date set: 2026-10-01

### Action Items

- Tech Lead: Write TDD for parallel invoice generation batches by 2026-06-18
- Principal Engineer: Spike on async tax pre-computation approach, share findings by 2026-07-01
- Engineering Manager: Contact v1 event consumer teams to confirm migration timelines by 2026-07-01

### Follow-ups

- Next architecture review: 2026-09-04
- Mid-quarter check-in on invoice generation parallelization progress: 2026-07-15
