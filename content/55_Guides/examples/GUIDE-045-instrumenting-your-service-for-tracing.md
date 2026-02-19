---
id: GUIDE-045
type: guide
title: Instrumenting Your Service for Tracing
status: approved
owner: Engineering Team
created: '2025-04-17T21:11:13.663Z'
updated: '2026-09-28T08:28:35.923Z'
tags:
  - guide
  - monitoring-stack
summary: Instrumenting Your Service for Tracing
audience: customer
related_systems:
  - SYSTEM-037
  - SYSTEM-036
related_sops:
  - SOP-075
  - SOP-072
example: true
---

## Why Distributed Tracing Matters

When a request fails in a microservices system, the error is often not in the service that the user hit first. It propagated from a downstream dependency. Without distributed tracing, tracking a failure across three or four services requires correlating logs by timestamp across multiple systems — tedious and error-prone. Distributed tracing lets you see the entire request journey in a single view.

Our tracing stack uses OpenTelemetry SDKs to instrument services, an OTel Collector to receive and route spans, and Jaeger as the trace backend. This guide shows you how to add tracing instrumentation to your service.

## Prerequisites

- Your service is deployed to the production Kubernetes cluster and is onboarded to the monitoring stack
- You have identified the OTel SDK for your service's language (see the supported SDK list in the platform documentation)
- The OTel Collector endpoint for your environment: `otel-collector.monitoring.svc.cluster.local:4317`

## Step-by-Step Instrumentation

### Step 1: Install the OTel SDK

Add the OpenTelemetry SDK to your service's dependencies. For Node.js:

```bash
npm install @opentelemetry/sdk-node @opentelemetry/auto-instrumentations-node
```

For Go:
```bash
go get go.opentelemetry.io/otel go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc
```

### Step 2: Configure the Exporter

Configure the SDK to export spans to the OTel Collector. The endpoint and service name should come from environment variables set in your Kubernetes deployment:

```yaml
# In your Kubernetes deployment manifest
env:
  - name: OTEL_EXPORTER_OTLP_ENDPOINT
    value: "http://otel-collector.monitoring.svc.cluster.local:4317"
  - name: OTEL_SERVICE_NAME
    value: "your-service-name"
  - name: OTEL_TRACES_SAMPLER
    value: "parentbased_traceidratio"
  - name: OTEL_TRACES_SAMPLER_ARG
    value: "0.1"
```

### Step 3: Initialize the SDK at Startup

Initialize the tracing provider before your service starts handling requests. Auto-instrumentation libraries for HTTP frameworks (Express, Gin, Spring) will automatically create spans for incoming requests.

### Step 4: Propagate Context on Outbound Calls

If your service makes outbound HTTP calls, ensure the HTTP client injects `traceparent` and `tracestate` headers. Most auto-instrumentation libraries handle this automatically — verify by checking if downstream services show as child spans in Jaeger.

## Validating Your Instrumentation

After deploying with tracing enabled, open Jaeger and search by your service name over the last 5 minutes. You should see traces appearing. Click into one to confirm:

- Root span shows the inbound request with correct `http.method` and `http.url` attributes
- Outbound calls to downstream services appear as child spans
- Span duration matches what you'd expect for the operation
- No PII or credentials are present in span attributes

## Common Issues

**No traces appearing**: Check the OTel Collector logs for your service name. The most common cause is a wrong endpoint URL or a NetworkPolicy blocking egress from your pod to the monitoring namespace.

**Traces appear but downstream services are missing**: The downstream service may not be instrumented, or the HTTP client in your service is not injecting trace context headers.

**Traces contain PII**: Use `SpanProcessor` to filter or redact sensitive attributes before they are exported. This is required by the Distributed Tracing Standard.

## Next Steps

- Follow the Debug Missing Traces SOP if your traces are not appearing after deployment
- Review the Distributed Tracing Standard for compliance requirements
- Read the Jaeger Trace Collection Failure Runbook so you can troubleshoot collector issues if they arise
