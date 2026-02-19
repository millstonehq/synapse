---
id: MEETING-071
type: meeting
title: Monitoring Platform Architecture Review
status: approved
owner: Engineering Manager
created: '2024-09-08T02:38:04.462Z'
updated: '2025-06-22T19:34:00.588Z'
tags:
  - meeting
  - monitoring-stack
summary: Monitoring Platform Architecture Review
company: MonitoringStack
topic: Monitoring Platform Architecture Review
meeting_date: '2026-02-14T13:09:00.992Z'
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

- **Project**: MonitoringStack Platform
- **Topic**: Monitoring Platform Architecture Review
- **Date/Time**: 2026-02-14 1:09 PM UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager
- **Context**: Architecture review of the current monitoring platform to assess scalability, data pipeline integrity, and alerting reliability ahead of a planned capacity expansion. Engineering Manager and QA Lead participating from the client side to surface operational pain points and validate proposed changes.

## Observations by Domain

- **Data Ingestion**: The metrics collection layer using an agent-based push model is performing adequately at current scale but shows latency spikes above 10,000 active hosts; a pull-based scrape approach or a tiered buffering strategy should be evaluated before the next capacity milestone.
- **Storage & Retention**: Long-term storage relies on a single time-series database instance with no horizontal sharding; retention policies are manually managed, creating operational risk when volumes grow beyond current projections.
- **Alerting Engine**: Alert rule evaluation is running on a shared compute node alongside query processing, introducing resource contention during high-cardinality query bursts; dedicated alert evaluation workers are needed.
- **Visualization Layer**: Dashboard rendering is sluggish for panels querying more than 90 days of data; pre-aggregation or downsampling pipelines have not been implemented yet.
- **Integration & Routing**: Notification routing to PagerDuty and Slack is functioning, but there is no dead-letter queue for failed notification deliveries, meaning alerts can silently drop during downstream outages.
- **Access Control**: Role-based access at the dashboard level is implemented; however, data-source-level permissions are not enforced, allowing any authenticated user to query any metric series directly.

## Key Metrics & Data Points

- **Active monitored hosts**: 8,400 (peak observed: 11,200 during incident drill)
- **Ingestion throughput**: ~2.1 million data points per minute at steady state
- **Alert evaluation latency (p95)**: 4.2 seconds against a 2-second SLO target
- **Storage utilization**: 78% of allocated capacity; projected to reach 95% within 60 days at current growth
- **Failed notification deliveries (last 30 days)**: 34 unacknowledged drops
- **Mean time to dashboard render (90-day range)**: 8.7 seconds

## Preliminary Scorecard Hooks

- Data Ingestion: 3/5 - Functional at current scale but buffering strategy is absent and latency degrades under burst load
- Storage & Retention: 2/5 - Single-node TSDB with manual retention is a fragility risk; sharding and automated lifecycle policies are overdue
- Alerting Engine: 3/5 - Rules are well-defined but shared compute causes SLO misses; evaluation isolation is the critical gap
- Visualization: 3/5 - Core dashboards are useful and well-organized; long-range query performance needs pre-aggregation work
- Integrations: 2/5 - Routing works under normal conditions but lacks resilience; silent drop risk is unacceptable for production alerting
- Access Control: 3/5 - Dashboard RBAC is in place; data-source-level enforcement is missing and represents a compliance gap

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Storage reaching capacity within 60 days | High | High | Principal Engineer | Implement automated retention policies and evaluate horizontal sharding or tiered cold storage | 2026-03-15 |
| Alert evaluation latency exceeding SLO under burst load | High | Medium | Tech Lead | Provision dedicated alert evaluation workers isolated from query compute | 2026-03-01 |
| Silent notification drops during downstream outages | Medium | Medium | Engineering Manager | Add dead-letter queue with retry logic and delivery confirmation logging | 2026-03-22 |
| Unrestricted data-source access by authenticated users | Medium | Low | Principal Engineer | Enforce data-source-level permissions and audit existing query access logs | 2026-04-01 |

## Decisions & Next Steps

### Decisions

- Dedicated alert evaluation workers will be provisioned as the highest-priority infrastructure change, targeting completion before the next capacity expansion wave.
- Automated retention policies and a tiered storage evaluation (warm/cold separation) will be scoped as a formal TDD and assigned to the Principal Engineer.
- A dead-letter queue for notification delivery will be added to the alerting integration layer; no further expansion of notification destinations until this is in place.

### Action Items

- Draft TDD for TSDB sharding and automated retention policy design (Principal Engineer - 2026-02-28)
- Provision and benchmark dedicated alert evaluation worker nodes in staging (Tech Lead - 2026-03-01)
- Implement dead-letter queue and retry logic for PagerDuty and Slack notification routing (Tech Lead - 2026-03-22)
- Audit data-source query access logs and draft data-source RBAC enforcement plan (Principal Engineer - 2026-04-01)
- QA Lead to define acceptance criteria and load test scenarios for alert evaluation SLO validation (QA Lead - 2026-02-28)

### Follow-ups

- Bi-weekly check-in between Principal Engineer and Engineering Manager to track storage capacity and retention policy rollout.
- Reconvene full architecture review group once dedicated alert workers are deployed to validate SLO recovery.
- Product Manager to confirm dashboard performance requirements for the 90-day query range ahead of pre-aggregation pipeline design.
