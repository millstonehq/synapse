---
id: REFERENCE-016
type: reference
title: OpenTelemetry SDK Configuration Reference
status: published
owner: Engineering Team
created: '2024-11-02T21:17:36.168Z'
updated: '2025-07-24T19:06:46.110Z'
tags:
  - reference
  - monitoring-stack
summary: OpenTelemetry SDK Configuration Reference
upstream_url: https://docs.example.com/opentelemetry-sdk-configuration-reference
last_synced: '2026-10-28T19:53:12.246Z'
attribution: NIST
license: CC BY-SA 4.0
category: specification
example: true
---

## Overview

The OpenTelemetry (OTel) SDK provides vendor-neutral instrumentation for traces, metrics, and logs. This reference documents the configuration options and conventions used within the monitoring stack for services instrumented with the OTel SDK.

All new services must be instrumented using OTel. Services still on vendor-specific or custom instrumentation are tracked for migration. For the full upstream OTel specification and SDK documentation, see the upstream URL.

## Core Concepts

### Signals

OTel produces three signal types:

- **Traces** - Distributed trace spans capturing request flow across service boundaries. Each span records operation name, start/end timestamps, status, and key/value attributes.
- **Metrics** - Time series numeric measurements. OTel supports counters, gauges, histograms, and up-down counters.
- **Logs** - Structured log records that can be correlated with trace context via `trace_id` and `span_id` fields.

### Resources

A `Resource` describes the entity producing telemetry. Resource attributes are attached to all signals from a process and must include at minimum:

| Attribute | Example Value | Description |
|-----------|---------------|-------------|
| `service.name` | `alert-management` | Service identifier matching the Prometheus `job` label |
| `service.version` | `1.4.2` | Deployed version (commit SHA recommended) |
| `service.namespace` | `monitoring-stack` | Logical namespace |
| `deployment.environment` | `production` | `production`, `staging`, or `development` |
| `k8s.pod.name` | `alert-mgmt-7d9f-xkq2` | Pod name (injected via Downward API) |
| `k8s.node.name` | `worker-node-3` | Node name (injected via Downward API) |

### Exporters

Exporters send telemetry data to a backend. All services in this stack export via OTLP (OpenTelemetry Protocol) to the OTel Collector, which fans out to Prometheus (metrics), Jaeger (traces), and the log aggregation pipeline (logs).

## SDK Configuration

### Environment Variables

The OTel SDK is configured primarily via environment variables. These are injected into all service pods via the shared `otel-config` ConfigMap.

**Exporter configuration:**

| Variable | Value | Description |
|----------|-------|-------------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://otel-collector:4318` | OTLP HTTP endpoint of the collector |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `http/protobuf` | Protocol for OTLP export |
| `OTEL_EXPORTER_OTLP_TIMEOUT` | `5000` | Timeout in milliseconds |

**Resource configuration:**

| Variable | Value | Description |
|----------|-------|-------------|
| `OTEL_SERVICE_NAME` | `<service-name>` | Must match the Prometheus `job` label |
| `OTEL_SERVICE_VERSION` | `<git-commit-sha>` | Injected by CI during image build |
| `OTEL_RESOURCE_ATTRIBUTES` | `deployment.environment=production,...` | Additional resource attributes |

**Sampling configuration:**

| Variable | Value | Description |
|----------|-------|-------------|
| `OTEL_TRACES_SAMPLER` | `parentbased_traceidratio` | Sampler type |
| `OTEL_TRACES_SAMPLER_ARG` | `0.1` | 10% base sample rate for production |

**SDK feature flags:**

| Variable | Value | Description |
|----------|-------|-------------|
| `OTEL_SDK_DISABLED` | `false` | Set to `true` to disable OTel entirely (for debugging) |
| `OTEL_METRICS_EXPORTER` | `otlp` | Metrics exporter type |
| `OTEL_TRACES_EXPORTER` | `otlp` | Traces exporter type |
| `OTEL_LOGS_EXPORTER` | `otlp` | Logs exporter type |

### Programmatic Configuration (Go)

Services using the Go OTel SDK initialize the SDK in their `main.go` using the shared `internal/telemetry` package:

```go
func initTelemetry(ctx context.Context) (func(context.Context) error, error) {
    res, err := resource.New(ctx,
        resource.WithFromEnv(),
        resource.WithProcessPID(),
        resource.WithTelemetrySDK(),
        resource.WithHost(),
    )
    if err != nil {
        return nil, err
    }

    traceExporter, err := otlptracehttp.New(ctx)
    if err != nil {
        return nil, err
    }

    tracerProvider := trace.NewTracerProvider(
        trace.WithBatcher(traceExporter),
        trace.WithResource(res),
        trace.WithSampler(trace.ParentBased(
            trace.TraceIDRatioBased(0.1),
        )),
    )
    otel.SetTracerProvider(tracerProvider)
    otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
        propagation.TraceContext{},
        propagation.Baggage{},
    ))

    return tracerProvider.Shutdown, nil
}
```

### Programmatic Configuration (Python)

Python services use the `opentelemetry-sdk` package with the auto-instrumentation entry point where possible:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

provider = TracerProvider(resource=Resource.create({
    SERVICE_NAME: os.environ["OTEL_SERVICE_NAME"],
    SERVICE_VERSION: os.environ["OTEL_SERVICE_VERSION"],
}))
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)
```

## Instrumentation Conventions

### Span Naming

Span names must follow the format `<verb> <noun>` in lowercase, describing the operation at a level of abstraction appropriate for the signal:

- HTTP handler spans: `http <method> <route_template>` — e.g., `http get /api/v1/services/{id}`
- Database spans: `<db_system> <operation>` — e.g., `postgresql select`
- Outbound HTTP: `<http_method> <url_template>` — e.g., `post /api/alerts`
- Queue operations: `<queue_system> <operation>` — e.g., `kafka publish`

Do not include variable values (IDs, request parameters) in span names. Use span attributes instead.

### Required Span Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `http.method` | string | HTTP verb for HTTP spans |
| `http.status_code` | int | HTTP response status |
| `http.url` | string | Full URL (sanitized, no credentials) |
| `db.system` | string | Database type: `postgresql`, `redis`, `scylladb` |
| `db.statement` | string | Query template (no parameter values) |
| `error` | bool | Set to `true` if span is in error state |
| `error.message` | string | Human-readable error message if `error=true` |

### Metric Naming

OTel metrics must follow the OpenTelemetry semantic conventions naming scheme. Custom metrics use the service name as prefix:

- `alert_management.routing.rules.count` — gauge, number of active routing rules
- `metrics_collection.samples.ingested.total` — counter, total samples ingested
- `log_aggregation.pipeline.lag.seconds` — histogram, pipeline processing lag

When metrics are exported to Prometheus via the OTel Collector, dots in metric names are replaced with underscores automatically.

### Context Propagation

Trace context must be propagated across all service boundaries using the W3C TraceContext standard (`traceparent` and `tracestate` headers). The composite propagator initialized in the SDK handles this automatically for outbound HTTP calls made via the OTel-instrumented HTTP client.

For Kafka message passing, trace context is propagated via message headers using the same W3C format.

## OTel Collector Configuration

The OTel Collector runs as a DaemonSet in each Kubernetes node and as a central gateway deployment for cross-cluster data. The collector pipeline:

1. **Receivers**: OTLP receiver on port 4317 (gRPC) and 4318 (HTTP)
2. **Processors**: `batch` (500ms/1000 spans), `memory_limiter` (512MiB), `resource` (adds cluster labels), `filter` (drops health check spans)
3. **Exporters**: `prometheusremotewrite` (metrics to Prometheus), `jaeger` (traces), `loki` (logs via OTLP log exporter)

## Sampling Strategy

| Environment | Strategy | Sample Rate |
|-------------|----------|-------------|
| Production | `parentbased_traceidratio` | 10% baseline; 100% for errors |
| Staging | `parentbased_traceidratio` | 50% |
| Development | `always_on` | 100% |

Error spans are always sampled regardless of the base rate. This is enforced by the tail-based sampler in the gateway collector, which overrides the head-based SDK sampler for spans whose root is in error state.

## Sync Notes

This reference covers OTel SDK versions 1.x (stable API) and collector version 0.9x. The upstream specification evolves frequently; re-sync after major collector upgrades. The Go SDK stable API guarantees backward compatibility within the 1.x series.
