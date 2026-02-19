---
id: MEETING-077
type: meeting
title: Tracing Infrastructure Upgrade Discussion
status: approved
owner: Product Manager
created: '2025-01-28T04:27:03.558Z'
updated: '2025-02-18T12:19:47.033Z'
tags:
  - meeting
  - monitoring-stack
summary: Tracing Infrastructure Upgrade Discussion
company: MonitoringStack
topic: Tracing Infrastructure Upgrade Discussion
meeting_date: '2024-10-03T00:00:26.345Z'
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

- **Project**: Monitoring Stack — Tracing Infrastructure Upgrade
- **Topic**: Tracing Infrastructure Upgrade Discussion
- **Date/Time**: 2024-10-03 12:00 AM UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Planning session for the approved Jaeger-to-Tempo migration. Focus on migration timeline, parallel running strategy, and risk management.

## Observations by Domain

- **Current Jaeger State**: Jaeger is stable but query latency at P95 is 8.4 seconds; the Cassandra backend requires manual tuning after each Kubernetes node rotation; operational overhead is high
- **Grafana Tempo POC Results**: Tempo POC in staging ran for 3 weeks; P95 query latency was 1.2 seconds; trace-to-log correlation with Loki works seamlessly; no stability issues observed
- **OTel Compatibility**: All services using the OTel SDK can send to Tempo without code changes by updating the exporter endpoint; services using the legacy Jaeger thrift exporter need SDK updates
- **Data Migration**: Historical trace data in Jaeger will not be migrated to Tempo; engineers agreed to accept a "cold start" period where only new traces are in Tempo; Jaeger will remain readable for 30 days post-cutover
- **Storage Cost**: Tempo with object storage backend (S3) is estimated at $380/month vs. Jaeger/Cassandra at $920/month

## Key Metrics & Data Points

- **Jaeger query P95 latency (current)**: 8.4 seconds
- **Tempo query P95 latency (POC)**: 1.2 seconds (7x improvement)
- **Services using OTel SDK (can migrate without code change)**: 19 of 23
- **Services using legacy Jaeger thrift exporter (need SDK update)**: 4
- **Estimated monthly storage cost savings**: $540/month ($6,480/year)
- **Estimated migration effort**: 2 engineers, 3 weeks including parallel running period

## Preliminary Scorecard Hooks

- Migration Readiness: 4/5 - POC successful; most services are code-change-free; 4 legacy services need updates
- Risk Level: 3/5 - Parallel running for 2 weeks mitigates data loss risk; old-data loss is accepted trade-off
- Cost Impact: 5/5 - 58% cost reduction for tracing storage is significant and well-validated
- Timeline Confidence: 4/5 - 3-week estimate is conservative; team has strong POC experience
- Stakeholder Alignment: 4/5 - All teams briefed; no blocking objections; 4 legacy service teams need SDK update scheduling

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| 4 legacy services miss the SDK update deadline and lose trace coverage | Medium | Medium | Tech Lead | Schedule pairing sessions with each legacy service team to complete SDK updates | 2024-10-20 |
| Tempo object storage (S3) access issues during cutover | High | Low | Principal Engineer | Pre-validate S3 bucket permissions and IAM roles in staging before production cutover | 2024-10-28 |
| Engineers reference old Jaeger links in runbooks after cutover | Low | High | Product Manager | Audit all runbooks for Jaeger URLs; update to Tempo URLs before cutover date | 2024-10-28 |

## Decisions & Next Steps

### Decisions

- Proceed with Jaeger-to-Tempo migration; target cutover date is 2024-11-04
- Parallel run period: October 21 to November 3; both Tempo and Jaeger receive traces during this window
- Jaeger remains read-only after cutover through December 3, then is decommissioned

### Action Items

- Principal Engineer to deploy Tempo to production and configure OTel Collector dual-export by 2024-10-21
- Tech Lead to pair with 4 legacy service teams to update Jaeger thrift exporters to OTel by 2024-10-20
- Product Manager to update all runbook Jaeger links to Tempo URLs by 2024-10-28

### Follow-ups

- Parallel run review meeting on 2024-11-01 to confirm Tempo is receiving all expected traces
- Jaeger decommission confirmation meeting on 2024-11-15
