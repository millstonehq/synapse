---
id: MEETING-078
type: meeting
title: Dashboard Standardization Workshop
status: approved
owner: Product Manager
created: '2025-10-25T16:16:24.507Z'
updated: '2026-11-26T21:41:31.592Z'
tags:
  - meeting
  - monitoring-stack
summary: Dashboard Standardization Workshop
company: MonitoringStack
topic: Dashboard Standardization Workshop
meeting_date: '2024-03-26T13:27:01.645Z'
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

- **Project**: Monitoring Stack — Dashboard Standards Initiative
- **Topic**: Dashboard Standardization Workshop
- **Date/Time**: 2024-03-26 1:27 PM UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Workshop to define and agree on dashboard design standards for the monitoring platform. 47 Grafana dashboards exist across 23 teams; currently no standards exist; on-call engineers report difficulty orienting to unfamiliar service dashboards during incidents.

## Observations by Domain

- **Layout Consistency**: Current dashboards have wildly different layouts; some start with infrastructure metrics, some with business metrics, some with no structure at all; on-call engineers lose time orienting to new dashboards during incidents
- **Unit Labels**: 62% of dashboard panels have no unit annotation; engineers cannot distinguish `requests/second` from `total requests` without reading the query
- **Threshold Lines**: Only 8% of panels have threshold lines drawn at SLO levels; engineers must recall SLO targets during incidents instead of seeing them visually
- **GitOps Adoption**: 71% of dashboards were created manually in the Grafana UI and are not in version control; they will be lost if Grafana is restarted
- **Template Variables**: Only 31% of dashboards have environment/cluster variable selectors; dashboards cannot be reused across environments without variables

## Key Metrics & Data Points

- **Total Grafana dashboards in production**: 47
- **Dashboards in version control (GitOps)**: 33 (71%)
- **Dashboards with unit labels on all panels**: 38% (18 of 47)
- **Dashboards with threshold lines**: 8% (4 of 47)
- **Dashboards with template variables**: 31% (15 of 47)
- **Teams with a service overview dashboard**: 12 of 23 (52%)

## Preliminary Scorecard Hooks

- Layout Standardization: 1/5 - No standard exists; each dashboard is unique and often confusing
- Unit Labels: 2/5 - Majority of panels lack units; significant usability gap
- Threshold Visibility: 1/5 - Almost no dashboards show SLO thresholds visually
- GitOps Adoption: 3/5 - Most dashboards are in version control but significant minority are not
- Template Variable Coverage: 2/5 - Less than a third of dashboards support multi-environment filtering

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Standard is too prescriptive and slows down dashboard creation | Medium | Medium | Principal Engineer | Provide a standard template that teams import; compliance is verified in review, not authoring | 2024-04-10 |
| Retroactive compliance work is too large and blocks the team | Medium | High | Engineering Manager | Prioritize the 23 service overview dashboards first; all others have a 90-day grace period | 2024-04-15 |
| Teams create compliant dashboards initially but drift over time | Low | Medium | Tech Lead | Add automated compliance check to the GitOps pipeline; non-compliant dashboards fail merge | 2024-05-01 |

## Decisions & Next Steps

### Decisions

- Dashboard standard is adopted as documented in the Dashboard Design Standard draft
- Standard Grafana dashboard template will be published in the monitoring repo within 2 weeks
- Retroactive compliance for the 23 service overview dashboards is required by end of Q2 2024

### Action Items

- Principal Engineer to publish the standard dashboard JSON template to the monitoring repository (due 2024-04-10)
- Tech Lead to build an automated compliance linter for dashboard JSON and integrate it into the GitOps pipeline (due 2024-05-01)
- Product Manager to communicate the standard and 90-day compliance timeline to all 23 service teams (due 2024-04-03)

### Follow-ups

- Review compliance progress at the end of Q2 (first week of July 2024)
- Share the template with service teams during each SLO onboarding session
