---
id: CAPABILITY-022
type: capability
title: Observability Platform Capability
status: draft
owner: VP Engineering
created: '2025-06-24T11:05:27.158Z'
updated: '2025-02-01T02:05:07.834Z'
tags:
  - capability
  - monitoring-stack
summary: Observability Platform Capability
evidence_links:
  - PROCESS-045
  - POLICY-036
  - PROCESS-047
example: true
---

## Domain

- Observability covers the ability of the engineering organization to understand the internal state of all production systems from their external outputs (metrics, logs, traces, and events).
- This capability spans the Monitoring Stack (collection, storage, alerting, visualization) and the practices teams follow to instrument their services and respond to signals.
- Maturity at this capability directly affects mean time to detect (MTTD), mean time to resolve (MTTR), and the quality of postmortems.

## Maturity (0-5)

- Observability coverage: 3/5 - All services have basic Prometheus metrics, but trace coverage is incomplete (60% of services instrumented) and structured logging is inconsistent (structured JSON only in 70% of services)
- Alerting quality: 3/5 - Alert rules exist for all services but 34% are low-signal (high false positive rate); burn rate alerting migration is underway
- Dashboarding: 4/5 - All services have Grafana dashboards; SLO dashboards deployed; custom dashboard builder in development
- Incident observability: 3/5 - Grafana dashboards and logs available during incidents; trace correlation not yet fully operational for all services

## Metrics

- Percentage of services with full OTel instrumentation (metrics + traces + logs): currently 60%, target 95%
- Mean time to detect (MTTD) for SEV-1 incidents: currently 8.4 minutes, target < 3 minutes
- Alert noise ratio (non-actionable alerts / total alerts): currently 34%, target < 15%
- Dashboard coverage: all services with on-call rotation have at least one Grafana dashboard: currently 100%

## Evidence Links

- [[PROCESS-045|Observability Onboarding Process]] - Process for instrumenting new services with OTel
- [[POLICY-036|Monitoring Coverage Policy]] - Policy requiring minimum metric and alert coverage for production services
- [[PROCESS-047|Alert Rule Review Process]] - Process for reviewing and approving new alert rule additions

## Notes

- The primary gap to maturity level 4 is OTel trace coverage — 40% of services are still using vendor-specific or no tracing. This is a blocker for alert correlation engine functionality.
- Structured logging adoption is improving; a linting check was added to the CI pipeline in Q1 that enforces JSON log format, which will close the gap over the next 2 quarters as services update.
