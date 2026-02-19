---
id: STANDARD-043
type: standard
title: Metric Naming Convention Standard
status: approved
owner: Security Lead
created: '2024-10-28T21:20:39.151Z'
updated: '2025-05-24T03:40:26.144Z'
tags:
  - standard
  - monitoring-stack
summary: Metric Naming Convention Standard
related_policies:
  - POLICY-037
  - POLICY-040
example: true
related_systems:
  - SYSTEM-040
  - SYSTEM-036
---

## Area

This standard governs the naming conventions for all Prometheus metrics emitted by services in the production monitoring stack. Consistent metric names enable reliable querying, dashboard creation, and alerting across all services and environments.

All engineering teams instrumenting services with Prometheus metrics must follow this naming convention. The standard applies to custom application metrics; well-known Prometheus client library default metrics are exempt.

## Controls

- Metric names must use `snake_case` and follow the pattern `{namespace}_{subsystem}_{name}_{unit}` (e.g., `http_server_request_duration_seconds`)
- The namespace must be the service or component name and must not contain environment prefixes
- Units must be appended as a suffix using base SI units: `seconds`, `bytes`, `total` (for counters), `ratio` (for 0-1 values)
- Counter metrics must end in `_total`; histogram metrics must end in `_seconds`, `_bytes`, or another unit suffix
- Label cardinality must be kept below 10 distinct label values per label key; high-cardinality labels (e.g., user IDs, request IDs) are prohibited
- Metric names must be reviewed by the platform team before a new service is promoted to production
- Deprecated metrics must carry a `deprecated` label and be removed no later than 90 days after replacement metrics are available

## Compliance Mappings

- SOC 2: CC7.2 (System Monitoring) — consistent metric naming enables reliable automated monitoring
- ISO 27001: A.12.4.1 (Event Logging) — structured metric names support traceability requirements
- Internal Observability Standards Policy ([[POLICY-040|On-Call Rotation Policy]], [[POLICY-037|Alert Escalation Policy]])

## Related Policies

- [[POLICY-037|Alert Escalation Policy]]
- [[POLICY-040|On-Call Rotation Policy]]
