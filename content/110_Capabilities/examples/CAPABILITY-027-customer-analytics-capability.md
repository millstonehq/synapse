---
id: CAPABILITY-027
type: capability
title: Customer Analytics Capability
status: draft
owner: Head of Engineering
created: '2025-11-19T11:22:56.916Z'
updated: '2026-09-06T19:32:42.992Z'
tags:
  - capability
  - customer-portal
summary: Customer Analytics Capability
evidence_links:
  - POLICY-041
  - STANDARD-053
  - PROCESS-069
example: true
---

## Domain

- Customer Portal
- Product
- Data and Analytics

## Maturity (0-5)

**Current score: 2 / 5 (Repeatable)**

- **Level 0 - Initial**: No customer analytics. Portal behavior is unknown. No usage tracking.
- **Level 1 - Ad hoc**: Basic page view tracking via server logs. No structured event taxonomy. Reports produced manually on request.
- **Level 2 - Repeatable** (current): Session analytics and page view data collected. Monthly usage reports produced for key stakeholders. The Customer Analytics Service aggregates behavioral data from the portal. Core metrics (DAU, MAU, top pages) are available but not in real-time dashboards.
- **Level 3 - Defined**: Formal analytics event taxonomy documented and enforced. Custom events tracked for all key user flows (ticket submission, settings save, search query). Self-service dashboards available to PM and engineering leads.
- **Level 4 - Managed**: Analytics drive product decisions via A/B testing and funnel analysis. Alerting fires when core engagement metrics drop. Customer cohort analysis available.
- **Level 5 - Optimizing**: Real-time personalization powered by behavioral signals. Predictive models identify customers at risk of churning or needing support intervention.

**Gap to Level 3**: Event taxonomy is informal and not documented. Custom events are inconsistently named and tracked. No self-service dashboards exist for PM team; analytics requests go through the Analytics team's backlog.

## Metrics

- MAU: Currently 41,200, target 45,000 by end of year
- DAU: Currently 13,100, target 15,000
- Session duration P50: Currently 4.2 minutes, target 5.5 minutes
- Feature adoption rate (Notification Center used in session): Currently 42%, target 55%
- Analytics event coverage (% of key flows instrumented): Currently 35%, target 80%

## Evidence Links

- [[POLICY-041|Customer Data Collection Policy]] - Policy governing what customer behavioral data may be collected and for how long
- [[STANDARD-053|Customer Portal Accessibility Standard]] - Standard referenced for ensuring analytics SDKs do not degrade portal accessibility
- [[PROCESS-069|Customer Portal Design Review Process]] - Process that includes a review gate to verify analytics instrumentation before feature launch

## Notes

The Customer Analytics Service (SYSTEM-045) provides the data pipeline backing this capability, built on OpenSearch and a Redis 7 cache.

Key investments required for Level 3:
- Define and publish the analytics event taxonomy (event names, properties, naming convention)
- Instrument all key self-service flows with named events (ticket.submitted, settings.saved, search.executed, wizard.completed)
- Build self-service Grafana dashboards for MAU, DAU, feature adoption, and funnel drop-off
- Establish a data governance review in the design review process (PROCESS-069) to ensure new features include analytics instrumentation before launch
