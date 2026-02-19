---
id: MEETING-075
type: meeting
title: Observability Tool Evaluation Meeting
status: deprecated
owner: Principal Engineer
created: '2024-05-03T09:01:37.489Z'
updated: '2025-08-24T12:29:03.922Z'
tags:
  - meeting
  - monitoring-stack
summary: Observability Tool Evaluation Meeting
company: MonitoringStack
topic: Observability Tool Evaluation Meeting
meeting_date: '2024-08-29T22:14:17.446Z'
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

- **Project**: Monitoring Stack — Tooling Evaluation
- **Topic**: Observability Tool Evaluation Meeting
- **Date/Time**: 2024-08-29 10:14 PM UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Evaluation session to assess whether to replace or supplement the current Prometheus + Grafana + Jaeger stack with alternative tools. Triggered by growing storage costs and engineering requests for better trace-to-log correlation.

## Observations by Domain

- **Metrics (Prometheus)**: Prometheus is performing well for metrics but storage costs are growing at 15% month-over-month; Thanos or VictoriaMetrics for long-term storage are under consideration
- **Visualization (Grafana)**: Grafana remains the clear winner for dashboards; no motivation to replace it; the focus is on improving dashboard standards not swapping tools
- **Tracing (Jaeger)**: Jaeger is functional but lacks trace-to-log correlation and search UX is poor; Tempo (Grafana) evaluated as a replacement — provides native correlation with Loki logs
- **Logging (Loki vs. Elasticsearch)**: Current Elasticsearch deployment is expensive and operational overhead is high; Loki is a strong alternative given the team already uses Grafana and it reduces the tool count
- **Vendor Options**: Honeycomb and Datadog were evaluated as all-in-one alternatives; cost is 4-6x higher than self-hosted; not approved for this budget cycle

## Key Metrics & Data Points

- **Current monitoring storage cost (monthly)**: $4,200 (Prometheus + Elasticsearch + Jaeger backends)
- **Projected cost with Thanos + Loki + Tempo**: $2,800/month (33% reduction)
- **Elasticsearch operational incidents (last 6 months)**: 4 incidents requiring manual shard recovery
- **Jaeger search query P95 latency**: 8.4 seconds (high; degrading engineer experience)
- **Grafana Tempo trace query P95 latency (POC)**: 1.2 seconds (significantly better)

## Preliminary Scorecard Hooks

- Prometheus (keep): 4/5 - Core metrics platform remains solid; add Thanos for long-term storage
- Grafana (keep): 5/5 - Excellent; invest in dashboard standards not replacement
- Jaeger (replace with Tempo): 3/5 - Functional but poor UX; Tempo migration is low risk with high benefit
- Elasticsearch (replace with Loki): 2/5 - High operational cost and overhead; Loki migration approved for next quarter
- All-in-one vendors: 1/5 - Cost prohibitive for current budget; revisit if headcount grows significantly

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Jaeger to Tempo migration causes trace data loss during cutover | High | Low | Tech Lead | Run Tempo in parallel with Jaeger for 2 weeks before cutting over | 2024-11-01 |
| Elasticsearch to Loki migration breaks existing log queries | Medium | Medium | Principal Engineer | Audit and rewrite top 20 most-used log queries for LogQL before migration | 2024-10-15 |
| Thanos adds operational complexity to Prometheus setup | Low | Medium | Engineering Manager | Use managed Thanos (Cortex) rather than self-hosted to reduce ops burden | 2024-11-15 |

## Decisions & Next Steps

### Decisions

- Replace Jaeger with Grafana Tempo in Q4 2024; run parallel for 2 weeks before cutover
- Replace Elasticsearch with Loki in Q4 2024; Elasticsearch decommissioned by end of year
- Evaluate Thanos for Prometheus long-term storage in Q1 2025; no commitment yet

### Action Items

- Principal Engineer to create a TDD for the Jaeger-to-Tempo migration (due 2024-09-15)
- Tech Lead to audit existing log queries and estimate LogQL rewrite effort (due 2024-09-22)
- Product Manager to socialize tool changes with all service teams and update observability documentation (due 2024-10-01)

### Follow-ups

- Schedule Tempo POC review after 2-week parallel run
- Review Loki migration plan before October sprint planning
