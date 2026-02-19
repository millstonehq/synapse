---
id: MEETING-080
type: meeting
title: OpenTelemetry Adoption Planning
status: approved
owner: Principal Engineer
created: '2025-01-07T02:21:22.287Z'
updated: '2026-03-11T11:07:33.411Z'
tags:
  - meeting
  - monitoring-stack
summary: OpenTelemetry Adoption Planning
company: MonitoringStack
topic: OpenTelemetry Adoption Planning
meeting_date: '2025-05-08T03:59:30.388Z'
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

- **Project**: Monitoring Stack — OpenTelemetry Adoption
- **Topic**: OpenTelemetry Adoption Planning
- **Date/Time**: 2025-05-08 3:59 AM UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Planning session to define the organization-wide migration from vendor-specific SDKs and the Jaeger thrift protocol to a fully standardized OpenTelemetry stack for all three signal types: metrics, logs, and traces.

## Observations by Domain

- **Current State**: 19 of 23 services use OTel SDKs for traces only; metrics are still exported via Prometheus client libraries directly; logs are not part of the OTel pipeline at all; no unified telemetry pipeline exists
- **OTel Collector Role**: The OTel Collector is currently only used for trace forwarding; it could serve as a unified telemetry gateway for all three signal types, simplifying service-side configuration
- **Metrics Migration**: OTel Prometheus receiver can scrape existing `/metrics` endpoints; no service-side code change is needed to route metrics through the OTel Collector
- **Logs Migration**: OTel log SDK adoption requires service-side changes; however, auto-instrumentation for common frameworks (Express, Gin) can reduce manual effort significantly
- **Benefits**: A unified OTel pipeline simplifies on-call correlation; trace IDs will be propagated consistently across metrics, logs, and traces enabling single-pane-of-glass investigation

## Key Metrics & Data Points

- **Services using OTel SDK (traces only)**: 19 of 23
- **Services with OTel log instrumentation**: 0 of 23
- **Services exporting metrics via OTel OTLP**: 0 of 23 (all use Prometheus directly)
- **Estimated effort to route metrics via OTel Collector**: 3 days platform work, no service team changes
- **Estimated effort for OTel log adoption across 23 services**: 6-8 weeks with platform team support
- **Projected reduction in monitoring config surface area**: ~40% (unified collector config vs. per-signal configs)

## Preliminary Scorecard Hooks

- Trace Standardization: 4/5 - Most services already use OTel SDK; legacy Jaeger exporters are the last gap
- Metrics Standardization: 2/5 - No services use OTel for metrics; routing through Collector is low-effort but not yet done
- Logs Standardization: 1/5 - No services use OTel for logs; significant adoption work required
- Unified Pipeline Vision: 3/5 - Clear target architecture defined; implementation phasing needed
- Organizational Readiness: 3/5 - Engineering teams supportive but need clear guidance and tooling before they can self-serve

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| OTel log SDK breaks existing structured log format and breaks Loki ingestion | High | Medium | Tech Lead | Validate OTel log output matches Loki ingestion expectations in staging with 3 pilot services before full rollout | 2025-06-15 |
| OTel Collector becomes a single point of failure for all telemetry | High | Low | Principal Engineer | Deploy OTel Collector as a DaemonSet to avoid SPOF; implement fallback direct-to-Prometheus scraping for metrics | 2025-07-01 |
| Service teams resist adding another SDK dependency | Medium | Medium | Product Manager | Provide auto-instrumentation libraries that add OTel with minimal code changes; document in onboarding guide | 2025-06-01 |

## Decisions & Next Steps

### Decisions

- Phase 1 (Q2 2025): Route all metric scrapes through OTel Collector alongside existing Prometheus scraping; validate no data loss
- Phase 2 (Q3 2025): Pilot OTel log SDK with 3 volunteer service teams; document patterns and update onboarding guide
- Phase 3 (Q4 2025): Mandate OTel log SDK for all new services; existing services have until end of Q1 2026 to migrate

### Action Items

- Principal Engineer to configure OTel Collector with Prometheus receiver for all existing scrape targets (due 2025-06-01)
- Tech Lead to recruit 3 pilot services for OTel log SDK adoption and lead the implementation (due 2025-06-15)
- Product Manager to publish the OTel adoption roadmap to all engineering teams with phase timelines (due 2025-05-22)

### Follow-ups

- Phase 1 readiness review meeting scheduled for 2025-06-15
- Pilot service retrospective after 30 days of OTel log adoption
