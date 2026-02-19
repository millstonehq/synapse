---
id: SOP-077
type: sop
title: Debug Missing Traces SOP
status: approved
owner: SRE Lead
created: '2024-06-23T05:57:10.791Z'
updated: '2026-06-06T18:20:07.957Z'
tags:
  - sop
  - monitoring-stack
summary: Debug Missing Traces SOP
related_process: PROCESS-043
related_systems:
  - SYSTEM-040
example: true
---

## Preconditions

- You have confirmed that traces are missing for a specific service (either no traces appear in Jaeger for that service, or trace context is not being propagated to downstream spans)
- You have verified that the service is running and receiving traffic (check metrics — traffic should be non-zero)
- You have access to the Jaeger UI and the service's pod logs

## Materials/Access

- Jaeger UI access for querying traces by service name and time range
- `kubectl` access to the service's namespace for checking pod logs and environment variables
- Prometheus access to verify that the OTEL collector is scraping correctly
- Access to the service's source code or configuration to review instrumentation settings
- OTel Collector pod logs access in the `monitoring` namespace

## Procedure

1. Open Jaeger UI and search for traces from the affected service in the last 15 minutes. If zero traces appear, the issue is either in the SDK configuration or the collector pipeline.
2. Check whether the service is emitting trace data at all by looking at the OTel Collector metrics: `otelcol_receiver_accepted_spans_total{service="your-service"}` in Prometheus. If this counter is zero, the service SDK is not sending spans.
3. Check the service's environment variables to confirm the OTel endpoint is set correctly: `kubectl exec -n {namespace} {pod} -- env | grep OTEL`. The `OTEL_EXPORTER_OTLP_ENDPOINT` should point to the collector service.
4. Check the service's pod logs for OTel SDK initialization errors. Look for messages like "failed to send spans" or "connection refused to collector."
5. Check the OTel Collector pod logs in the monitoring namespace: `kubectl logs -n monitoring otel-collector-0 | grep error`. Look for errors related to the service's traces being rejected (e.g., invalid format, authentication failure).
6. If the SDK is sending but collector is dropping: check the collector's pipeline configuration to ensure the service name matches an active pipeline receiver, and that the export target (Jaeger) is healthy.
7. If traces appear in Jaeger but span context is not propagating between services: verify that the downstream service is reading `traceparent` and `tracestate` headers and that the HTTP client in the upstream service is injecting them.
8. Apply the fix identified (update environment variable, fix SDK configuration, correct collector pipeline), deploy the change, and retest by generating a request and searching Jaeger.

## Validation

- Traces from the affected service appear in Jaeger within 60 seconds of generating a request
- Traces show a complete span hierarchy including downstream service calls
- OTel Collector metrics show `otelcol_receiver_accepted_spans_total` incrementing for the service
- No OTel-related errors appear in the service pod logs

## Rollback

1. If the SDK configuration change causes a service regression, revert the environment variable change or deployment.
2. If the OTel Collector configuration change causes other services to lose traces, revert the collector configuration from the monitoring repository.
3. Missing traces are not a P1 incident on their own; however, if trace loss prevents investigation of an active incident, escalate to the Platform Engineer immediately.
