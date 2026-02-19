---
id: MEETING-057
type: meeting
title: Real-Time vs Batch Processing Discussion
status: approved
owner: Principal Engineer
created: '2024-08-05T15:04:03.101Z'
updated: '2026-09-03T18:28:02.913Z'
tags:
  - meeting
  - data-pipeline
summary: Real-Time vs Batch Processing Discussion
company: DataPipeline
topic: Real-Time vs Batch Processing Discussion
meeting_date: '2025-03-28T03:34:49.532Z'
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

- **Project**: Data Platform Strategy
- **Topic**: Real-Time vs Batch Processing Discussion
- **Date/Time**: 2025-03-28 9:00 AM PT
- **Attendees (engineering)**: Principal Engineer, Tech Lead, Data Platform Lead
- **Attendees (product)**: Product Manager, Engineering Manager
- **Context**: Product has requested sub-minute freshness for 3 dashboards currently powered by hourly batch pipelines; this session evaluates whether to move these to streaming or find batch optimizations.

## Observations by Domain

- **Product Requirements**: The 3 dashboards require data freshness of under 5 minutes; current hourly batch cycle does not meet this need.
- **Current Batch Architecture**: All three dashboards read from curated dbt models that run hourly; end-to-end latency is 55-65 minutes.
- **Streaming Option**: Kafka infrastructure already in place; building Flink or Spark Structured Streaming jobs would achieve <1 min freshness but adds operational complexity.
- **Micro-batch Option**: Reducing dbt model run frequency to every 5 minutes is feasible for one of the three dashboards; the other two involve complex joins unsuitable for micro-batch.
- **Operational Cost**: Streaming jobs require continuous resource allocation vs. scheduled batch; estimated 3x infrastructure cost for equivalent throughput.
- **Team Capability**: Team has Kafka experience but limited Flink production experience; Spark Structured Streaming is better-known but has higher overhead for low-latency use cases.

## Key Metrics & Data Points

- **Dashboards requiring sub-5-minute freshness**: 3
- **Current batch end-to-end latency**: 55-65 minutes
- **Micro-batch feasibility (5-min cadence)**: 1 of 3 dashboards
- **Estimated streaming infrastructure cost multiplier**: 3x vs. batch
- **Team Flink production experience**: 0 engineers
- **Team Spark Structured Streaming experience**: 2 engineers

## Preliminary Scorecard Hooks

- Product Requirement Fit: 5/5 - Clear and measurable freshness requirement defined
- Batch Architecture Suitability: 2/5 - Cannot meet <5 min requirement without fundamental change
- Streaming Readiness: 3/5 - Infrastructure exists; team capability is the constraint
- Cost Efficiency: 2/5 - 3x cost premium for streaming is significant
- Operational Complexity: 2/5 - Adding streaming adds new failure modes and operational burden

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Streaming introduces new failure modes unfamiliar to team | High | High | Principal Engineer | Invest in Spark Structured Streaming training; start with one dashboard | 2025-04-15 |
| 3x cost increase for streaming is not approved in budget | Medium | Medium | Engineering Manager | Get budget approval before committing to streaming approach | 2025-04-01 |
| Micro-batch on 5-min cadence may overload dbt compute | Medium | Medium | Tech Lead | Load test 5-min cadence in staging before promoting to production | 2025-04-10 |

## Decisions & Next Steps

### Decisions

- Micro-batch (5-minute dbt cadence) will be implemented for the one feasible dashboard first as a low-risk quick win
- Spark Structured Streaming will be evaluated for the remaining two dashboards; a proof-of-concept sprint will be run before committing to production
- No Flink investment at this time; Spark Structured Streaming is the preferred streaming technology given existing team knowledge

### Action Items

- Implement and test 5-minute micro-batch for the first dashboard (Tech Lead - 2025-04-10)
- Run Spark Structured Streaming PoC for one of the remaining dashboards (Principal Engineer - 2025-04-25)
- Get budget approval for streaming infrastructure cost increase (Engineering Manager - 2025-04-01)

### Follow-ups

- Review micro-batch dashboard performance after 2 weeks in production
- Schedule streaming PoC review session after April 25
