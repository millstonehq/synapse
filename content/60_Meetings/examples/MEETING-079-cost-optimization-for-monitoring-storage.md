---
id: MEETING-079
type: meeting
title: Cost Optimization for Monitoring Storage
status: accepted
owner: Principal Engineer
created: '2025-10-06T05:45:04.661Z'
updated: '2025-12-25T10:47:33.679Z'
tags:
  - meeting
  - monitoring-stack
summary: Cost Optimization for Monitoring Storage
company: MonitoringStack
topic: Cost Optimization for Monitoring Storage
meeting_date: '2026-05-06T21:53:53.157Z'
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

- **Project**: Monitoring Stack — Cost Optimization Initiative
- **Topic**: Cost Optimization for Monitoring Storage
- **Date/Time**: 2026-05-06 9:53 PM UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Quarterly cost review of the monitoring stack storage. Total monitoring storage costs have grown 40% YoY; this session is to identify and prioritize cost reduction initiatives.

## Observations by Domain

- **Prometheus TSDB**: Prometheus TSDB is consuming 2.4 TB of SSD-backed storage; 60% of this is metrics that have not been queried in the past 90 days; downsampling and retention policy tightening are the primary lever
- **Log Storage (Loki)**: Loki S3 storage is growing at 18% month-over-month; several services are logging at DEBUG level in production, generating 10x the expected log volume; log level enforcement would reduce this significantly
- **Trace Storage (Tempo)**: Tempo object storage is within budget since the Jaeger migration; no action needed at this time
- **Cardinality**: 14 metrics have series counts above 500,000; these are the largest contributors to Prometheus storage costs; addressing them would reduce TSDB size by an estimated 35%
- **Retention Policy Enforcement**: Current retention policies are not enforced automatically; the Prometheus and Loki retention configs have not been updated in 18 months

## Key Metrics & Data Points

- **Total monitoring storage cost (monthly)**: $6,800
- **Prometheus TSDB size**: 2.4 TB ($3,200/month)
- **Loki S3 storage size**: 8.2 TB ($2,100/month)
- **Tempo S3 storage**: 1.4 TB ($480/month)
- **Metrics unqueried in 90 days (estimated)**: 60% of total TSDB series
- **Estimated savings from cardinality reduction**: $1,100/month

## Preliminary Scorecard Hooks

- Prometheus Cost Efficiency: 2/5 - 60% of stored metrics are unqueried; significant waste
- Log Cost Efficiency: 2/5 - DEBUG logging in production is inflating costs 10x for some services
- Trace Cost Efficiency: 5/5 - Tempo migration achieved target cost; no action needed
- Retention Policy Compliance: 1/5 - Policies not updated in 18 months; not enforced automatically
- Cardinality Management: 2/5 - 14 high-cardinality metrics identified but not yet remediated

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Overly aggressive metric retention causes incident investigation gaps | High | Medium | Principal Engineer | Audit incident investigation patterns before reducing retention; keep 13-month aggregates | 2026-05-20 |
| Enforcing log level in production breaks debugging workflows for service teams | Medium | Low | Tech Lead | Provide dynamic log level API for temporary DEBUG enable; no permanent production DEBUG | 2026-06-01 |
| Cardinality fixes require service teams to change their code | Medium | Medium | Product Manager | Engage service teams early; provide relabeling config as interim fix while code is updated | 2026-06-15 |

## Decisions & Next Steps

### Decisions

- Prometheus retention policy to be updated: raw data 15 days, 5-min downsamples 90 days, 1-hour aggregates 13 months
- No service may run at DEBUG log level in production without a 4-hour time-boxed authorization
- Top 5 high-cardinality metrics to be addressed this quarter via relabeling configs and service team engagement

### Action Items

- Principal Engineer to update Prometheus and Loki retention configs and deploy via GitOps (due 2026-05-20)
- Tech Lead to identify the 5 largest cardinality contributors and engage their service teams (due 2026-05-15)
- Engineering Manager to communicate log level policy to all service teams with the new enforcement date (due 2026-05-13)

### Follow-ups

- Review storage cost trend in the next quarterly meeting (August 2026)
- Follow up with service teams on cardinality fix progress at the June sprint planning meeting
