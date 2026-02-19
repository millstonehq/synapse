---
id: MEETING-093
type: meeting
title: Usage-Based Billing Design Session
status: approved
owner: Product Manager
created: '2025-11-26T06:28:56.650Z'
updated: '2026-02-16T07:28:53.651Z'
tags:
  - meeting
  - billing-engine
summary: Usage-Based Billing Design Session
company: BillingEngine
topic: Usage-Based Billing Design Session
meeting_date: '2026-01-23T16:37:41.686Z'
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
- **Topic**: Usage-Based Billing Design Session
- **Date/Time**: 2026-01-23 16:37 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Design session for the next generation usage-based billing infrastructure to support the new compute-minute and data-transfer billing dimensions. Current metering pipeline is single-dimension; this expands to multi-dimension with real-time usage dashboards.

## Observations by Domain

- **Metering Pipeline**: Current single-event-type pipeline will need to handle 3 concurrent event types (compute.minutes, data.transfer.gb, api.requests) at 5x the current event volume
- **Aggregation**: Daily aggregation checkpoints are needed for real-time customer dashboards; current monthly-only aggregation does not support intra-period usage queries
- **Pricing Engine**: Tiered pricing currently evaluates each dimension independently; cross-dimension commit pricing (e.g., "spend $500/month across any dimensions for a 10% discount") is not supported
- **Customer Visibility**: Product team requires a usage dashboard endpoint that returns real-time aggregates — this is currently not available in the Billing API

## Key Metrics & Data Points

- **Projected event volume at launch**: 18M events/day (current: 3.2M/day)
- **Real-time dashboard latency requirement**: Under 5 minutes from event emission to dashboard display
- **Pricing dimensions to support at launch**: 3 (compute.minutes, data.transfer.gb, api.requests)
- **Cross-dimension commit pricing accounts**: Expected 120 enterprise accounts on commit plans at launch

## Preliminary Scorecard Hooks

- Metering Capacity: 2/5 - Pipeline must be re-architected for 6x volume before launch
- Aggregation Freshness: 2/5 - Daily checkpoints required; current monthly-only aggregation is insufficient
- Pricing Engine Flexibility: 3/5 - Multi-tier works; cross-dimension commit pricing is a new build
- Billing API Readiness: 3/5 - Core invoice API is solid; real-time usage endpoint is a new feature

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Metering pipeline cannot handle 18M events/day | High | High | Principal Engineer | Re-architect with Kafka partitioning and consumer scaling; load test before launch | 2026-03-15 |
| Daily aggregation adds DB write load at scale | Medium | Medium | Tech Lead | Use materialized views with incremental refresh instead of full re-aggregation | 2026-03-01 |
| Cross-dimension commit pricing adds calculation complexity | Medium | Low | Tech Lead | Design commit pricing as a billing plan modifier layer; spike required | 2026-02-28 |

## Decisions & Next Steps

### Decisions

- Metering pipeline will be re-architected with Kafka for horizontal scalability before the UBB launch
- Daily aggregation will use materialized views with 5-minute incremental refresh
- Cross-dimension commit pricing will be implemented as a plan modifier in v2 (not at launch)

### Action Items

- Principal Engineer: Write TDD for metering pipeline re-architecture by 2026-02-06
- Tech Lead: Spike on materialized view aggregation approach with performance benchmarks by 2026-02-14
- Product Manager: Confirm commit pricing can be deferred to v2 with customer advisory board

### Follow-ups

- Architecture review of TDD once drafted
- Load test plan review session scheduled for 2026-02-28
