---
id: STANDARD-047
type: standard
title: Dashboard Design Standard
status: approved
owner: Head of Engineering
created: '2024-07-25T09:30:16.956Z'
updated: '2026-05-28T10:46:12.594Z'
tags:
  - standard
  - monitoring-stack
summary: Dashboard Design Standard
related_policies:
  - POLICY-037
  - POLICY-039
example: true
related_systems:
  - SYSTEM-038
  - SYSTEM-037
---

## Area

This standard defines the required structure and content guidelines for Grafana dashboards in the monitoring stack. Consistent dashboard design enables on-call engineers to quickly orient themselves during incidents and ensures that key service health signals are always visible at a glance.

All Grafana dashboards used for production service monitoring must conform to this standard. Exploratory or personal dashboards are exempt but should follow these patterns where practical.

## Controls

- Every production service must have a primary overview dashboard with panels for: request rate, error rate, latency (P50/P95/P99), and saturation (CPU/memory)
- Dashboards must include a variables row at the top for environment (`env`), cluster (`cluster`), and time range selection
- All panels must include a unit annotation matching the metric unit (e.g., `seconds`, `%`, `req/s`)
- Dashboard JSON must be stored in version control and deployed via GitOps; manual-only edits to production dashboards are not permitted
- Dashboards must use the standard color scheme: green for healthy, yellow for warning, red for critical thresholds
- Each dashboard must include a link panel or annotation connecting to the relevant runbook and alert definitions
- Dashboards must be titled with the pattern `[Service Name] - [View Type]` (e.g., `Auth Service - Overview`)

## Compliance Mappings

- SOC 2: CC7.2 (System Monitoring) — consistent dashboards support continuous monitoring evidence
- Internal: [[POLICY-037|Alert Escalation Policy]], [[POLICY-039|Observability Standards Policy]]
- Grafana Labs Best Practices for Dashboard Design (external reference)

## Related Policies

- [[POLICY-037|Alert Escalation Policy]]
- [[POLICY-039|Observability Standards Policy]]
