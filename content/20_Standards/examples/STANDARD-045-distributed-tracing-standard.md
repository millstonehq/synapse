---
id: STANDARD-045
type: standard
title: Distributed Tracing Standard
status: proposed
owner: Head of Engineering
created: '2025-09-07T18:22:38.712Z'
updated: '2025-10-19T21:28:29.309Z'
tags:
  - standard
  - monitoring-stack
summary: Distributed Tracing Standard
related_policies:
  - POLICY-039
  - POLICY-036
example: true
related_systems:
  - SYSTEM-036
  - SYSTEM-038
---

## Area

This standard specifies the requirements for distributed tracing instrumentation across all production services. Distributed tracing enables engineers to follow a request across service boundaries, identify latency hotspots, and understand failure propagation in the monitoring stack.

All services that make outbound HTTP, gRPC, or message-queue calls must implement this standard. Services that only consume events without making outbound calls are encouraged but not required to participate.

## Controls

- All services must use an OpenTelemetry-compatible SDK for trace instrumentation; vendor-specific SDKs are not permitted
- Every inbound request must generate a root span with attributes: `service.name`, `http.method`, `http.url`, `http.status_code`
- Trace context must be propagated using W3C TraceContext headers (`traceparent`, `tracestate`) for all outbound HTTP calls
- Sampling rate must be at least 10% for all production traffic; error and slow-request traces (>1s) must always be sampled (100%)
- Span attributes must not contain PII, credentials, or secrets; services must redact sensitive request parameters
- Custom spans must include a descriptive `operation.name` and must not exceed 50 ms without child span annotations
- Trace export must target the central Jaeger/OTel collector endpoint; services must not write traces directly to disk

## Compliance Mappings

- SOC 2: CC7.1 (Logical and Physical Access Controls) — trace context supports access audit across service calls
- Internal: [[POLICY-039|Observability Standards Policy]], [[POLICY-036|Monitoring Data Retention Policy]]
- OpenTelemetry specification (OTLP trace protocol compliance)

## Related Policies

- [[POLICY-039|Observability Standards Policy]]
- [[POLICY-036|Monitoring Data Retention Policy]]
