---
id: STANDARD-046
type: standard
title: Alert Definition Standard
status: approved
owner: Compliance Officer
created: '2024-01-19T19:27:04.141Z'
updated: '2026-10-12T18:36:19.350Z'
tags:
  - standard
  - monitoring-stack
summary: Alert Definition Standard
related_policies:
  - POLICY-039
  - POLICY-038
example: true
related_systems:
  - SYSTEM-039
  - SYSTEM-038
---

## Area

This standard defines the requirements for creating, naming, and documenting alerts in the monitoring stack. Well-defined alerts reduce alert fatigue, improve on-call response quality, and ensure every alert represents a condition that is both actionable and meaningful to the responding engineer.

All teams creating Prometheus alerting rules or PagerDuty incidents must follow this standard. The standard applies to production alerts; staging and development environment alerts are exempt but encouraged to follow the same patterns.

## Controls

- Every alert must have a unique, descriptive name following the pattern `{service}_{condition}_{severity}` (e.g., `api_error_rate_critical`)
- Every alert definition must include these annotations: `summary` (one-line description), `description` (detailed explanation), `runbook_url` (link to the runbook for this alert)
- Alerts must not fire for single-sample violations; minimum `for` duration is 2 minutes for warning alerts and 5 minutes for critical alerts to reduce flapping
- Alert severity must be one of: `info`, `warning`, `critical`; `critical` alerts must trigger PagerDuty notifications
- Every `critical` alert must have a corresponding runbook before it is deployed to production
- Alerts must be tested in staging before being added to the production AlertManager configuration
- Alert rules must be reviewed and tuned at minimum quarterly as part of the alert tuning process

## Compliance Mappings

- SOC 2: CC7.2 (System Monitoring) — documented alerts provide evidence of continuous monitoring
- Internal: [[POLICY-039|Observability Standards Policy]], [[POLICY-038|SLO Definition Policy]]
- ITIL v4: Incident Management — alert definitions map to incident detection and classification requirements

## Related Policies

- [[POLICY-039|Observability Standards Policy]]
- [[POLICY-038|SLO Definition Policy]]
