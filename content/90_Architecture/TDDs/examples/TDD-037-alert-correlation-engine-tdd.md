---
id: TDD-037
type: tdd
title: Alert Correlation Engine TDD
status: accepted
owner: Senior Engineer
created: '2025-07-31T00:23:03.290Z'
updated: '2025-10-13T11:33:50.331Z'
tags:
  - tdd
  - monitoring-stack
summary: Alert Correlation Engine TDD
related_adrs:
  - ADR-0030
  - ADR-0031
example: true
---

## Summary

Design an alert correlation engine that groups related firing alerts into unified incident records, reducing alert noise for on-call engineers. Instead of receiving 40 individual alerts during a cascading infrastructure failure, an engineer receives a single "Incident: Database cluster degraded — 12 downstream services affected" notification.

The engine builds on the metrics signals standardized in [[ADR-0030|ADR-0030]] and the OTel trace context from [[ADR-0031|ADR-0031]] to identify causal relationships between alerts (e.g., a database latency spike causing downstream timeout alerts).

## Overview

- **Topology-aware correlation**: Uses the service dependency graph to identify root-cause candidates. If service A depends on service B and both are alerting, B's alert is likely the cause.
- **Time-window grouping**: Alerts that fire within a configurable time window (default 5 minutes) across services with dependency relationships are grouped into a single incident.
- **Trace-based evidence**: For services instrumented with OTel, trace data is used to confirm causality — if 90% of failing traces from service A have a failing span from service B, B is flagged as the likely root cause.
- **Deduplication**: The correlation engine feeds into the Alert Management Service, replacing the raw alert stream with correlated incident records.

## Architecture

- **Event consumer**: Consumes raw alert events from the Alert Management Service webhook stream via an internal pub/sub channel.
- **Topology graph**: Maintains an in-memory service dependency graph (refreshed from the Distributed Tracing Platform's service map API every 5 minutes). Graph nodes are services; edges are dependency relationships with call volume weights.
- **Correlation window**: A sliding 5-minute window that groups co-firing alerts by topological proximity. Alerts within 2 hops of each other in the dependency graph are candidates for correlation.
- **Incident publisher**: Publishes correlated incident records back to the Alert Management Service via its REST API. Raw alerts are suppressed; only the incident record is routed to notification channels.
- **Evidence collector**: Queries the Distributed Tracing Platform for error-rate-by-span data to attach causal evidence to incident records.

## Information Model

- **IncidentRecord**: `id`, `title` (auto-generated from root cause candidate), `severity`, `firing_alerts[]`, `root_cause_candidate`, `evidence` (trace data), `created_at`, `resolved_at`
- **AlertEvent**: `alert_name`, `service`, `labels`, `fired_at`, `resolved_at`
- **DependencyEdge**: `source_service`, `target_service`, `call_volume_rps`, `last_updated`

## Interfaces

- Internal webhook consumer: receives AlertManager alert payload on `POST /internal/alert-events`
- Distributed Tracing Platform API: `GET /api/v1/service-map` for topology graph
- Alert Management Service API: `POST /api/v1/incidents` to publish correlated incident records
- `GET /api/v1/correlations/status` — health endpoint showing correlation engine state

## Files and Layout

```
cmd/correlation-engine/main.go
internal/
  consumer/                  - Alert event webhook receiver
  graph/                     - Service dependency graph, topology queries
  correlator/                - Time-window grouping, root cause candidate selection
  evidence/                  - Tracing Platform API client for causal evidence
  publisher/                 - Alert Management Service incident publisher
```

## Work Plan

1. **Phase 1 (Week 1)**: Alert event consumer, in-memory event buffer, basic time-window grouping
2. **Phase 2 (Week 2)**: Service dependency graph integration with Distributed Tracing Platform service map
3. **Phase 3 (Week 3)**: Root cause candidate selection algorithm, trace-based evidence collection
4. **Phase 4 (Week 4-5)**: Integration with Alert Management Service, suppression of raw alerts, end-to-end testing
5. **Phase 5 (Week 6)**: Load test with simulated alert storms, tuning correlation window and topology distance thresholds

## Risks and Mitigations

- **Risk**: Incorrect root cause identification causes engineers to investigate the wrong service. **Mitigation**: Always include all correlated alerts in the incident record; root cause is a suggestion, not a definitive finding.
- **Risk**: Topology graph stale during rapidly evolving incidents. **Mitigation**: 5-minute refresh cycle is acceptable for stable production topologies; force-refresh triggered on incident creation.
- **Risk**: Correlation engine becoming a single point of failure in the alerting path. **Mitigation**: If the correlation engine is unavailable, alert events flow directly to the Alert Management Service without correlation (fail-open design).
