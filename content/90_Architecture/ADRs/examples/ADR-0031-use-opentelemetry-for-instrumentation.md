---
id: ADR-0031
type: adr
title: Use OpenTelemetry for Instrumentation
status: deprecated
owner: Tech Lead
created: '2024-05-19T07:43:30.757Z'
updated: '2026-01-29T19:11:32.846Z'
tags:
  - adr
  - monitoring-stack
summary: Use OpenTelemetry for Instrumentation
example: true
supersedes: ADR-0033
---

## Context

As the monitoring stack matures, services are instrumented with a mix of Prometheus client libraries (for metrics), custom logging middleware (for structured logs), and vendor-specific tracing SDKs (Jaeger for some, Zipkin for others, and several services with no tracing at all). This fragmentation creates operational challenges: trace correlation across services with different SDKs is unreliable, adding a new telemetry dimension requires updating every service individually, and vendor lock-in to specific tracing backends makes infrastructure changes expensive.

The OpenTelemetry (OTel) project has reached stability (v1.0 for traces, v1.0 for metrics) and is now the industry-standard vendor-neutral instrumentation framework. It provides a single SDK per language that covers metrics, traces, and logs with a common data model, and exporters for all major backends (Prometheus, Jaeger, Zipkin, Datadog, etc.).

**Note**: This ADR was superseded by ADR-0033, which refined the implementation approach for error budget-based alerting built on top of the OTel metric signals standardized here. This ADR defines the instrumentation standard; ADR-0033 defines how alerts are built on top of it.

## Decision

All services in the platform will adopt **OpenTelemetry SDKs** as the standard instrumentation framework for metrics, traces, and logs. The migration will be phased over two quarters, starting with the highest-traffic services.

Standard exporters: OTel metrics exported to Prometheus (via OTLP Prometheus exporter); OTel traces exported to the Distributed Tracing Platform (via OTLP gRPC); OTel logs exported to the Log Aggregation Pipeline (via OTLP HTTP). Services must initialize the OTel SDK at startup and propagate trace context via W3C TraceContext headers on all outbound HTTP and gRPC calls.

## Consequences

**Positive:**
- Single instrumentation codebase per service for metrics, traces, and logs
- W3C TraceContext propagation enables end-to-end trace correlation across all services
- Backend-agnostic: we can swap the tracing backend (Jaeger → ClickHouse-based platform) without changing service code
- Industry standard with large community and strong library ecosystem

**Negative:**
- OTel SDK has higher baseline memory overhead than minimal Prometheus client libraries (~15MB per service in Go)
- Migration requires coordinated effort across all service teams — cannot be done incrementally without a compatibility shim
- OTel log bridge is still maturing; some edge cases require workarounds

**Neutral:**
- Existing Prometheus-format `/metrics` endpoints can be replaced by the OTel Prometheus exporter with no Grafana dashboard changes required

## Alternatives Considered

**Keep current approach (Prometheus client + custom logging + vendor tracing):**
- Pro: No migration cost; teams are familiar with current setup
- Con: No cross-service trace correlation; three separate instrumentation systems to maintain; adding a new backend requires changes to every service
- Rejected because: The fragmentation is a growing operational burden that compounds with each new service added.

**OpenCensus (OTel predecessor):**
- Pro: Already used in some services; familiar API
- Con: OpenCensus is officially deprecated in favor of OpenTelemetry. No new features, limited maintenance
- Rejected because: Migrating to OpenCensus would be technical debt incurred immediately upon adoption.
