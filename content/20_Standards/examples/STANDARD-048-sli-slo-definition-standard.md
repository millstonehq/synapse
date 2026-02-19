---
id: STANDARD-048
type: standard
title: SLI/SLO Definition Standard
status: approved
owner: Compliance Officer
created: '2025-12-16T19:18:06.118Z'
updated: '2026-12-15T22:32:29.551Z'
tags:
  - standard
  - monitoring-stack
summary: SLI/SLO Definition Standard
related_policies:
  - POLICY-038
  - POLICY-040
example: true
related_systems:
  - SYSTEM-039
  - SYSTEM-037
---

## Area

This standard specifies how Service Level Indicators (SLIs) and Service Level Objectives (SLOs) must be defined, implemented, and measured for production services. Clear, measurable SLIs and achievable SLOs form the foundation of the organization's reliability culture and on-call practice.

All engineering teams owning production services are required to implement SLIs and SLOs in accordance with this standard. The platform team is responsible for providing the tooling (e.g., Prometheus recording rules, Grafana SLO dashboards) to support SLO tracking.

## Controls

- SLIs must be expressed as a ratio of good events to total events (e.g., requests returning 2xx / total requests)
- SLIs must be derived from metrics already present in the monitoring stack; SLIs based on synthetic checks require platform team approval
- SLO targets must be set at a level that reflects genuine user impact; targets above 99.9% require a written business justification
- Every SLO must include an error budget calculation: `error_budget_minutes = (1 - SLO_target) * 30 * 24 * 60`
- Error budget burn rate alerts must be configured for 1-hour and 6-hour burn rate windows per Google SRE recommendations
- SLOs must be reviewed quarterly; any SLO that was breached in the prior quarter must include a remediation plan
- SLO compliance status must be visible on the service's primary Grafana overview dashboard

## Compliance Mappings

- SOC 2: A1.1 (Availability) — SLOs define and evidence the availability commitments made to customers
- Internal: [[POLICY-038|SLO Definition Policy]], [[POLICY-040|On-Call Rotation Policy]]
- Google SRE Book Chapter 4 (Service Level Objectives) — aligns with industry-standard SLO methodology

## Related Policies

- [[POLICY-038|SLO Definition Policy]]
- [[POLICY-040|On-Call Rotation Policy]]
