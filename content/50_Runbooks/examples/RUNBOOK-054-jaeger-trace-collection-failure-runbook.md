---
id: RUNBOOK-054
type: runbook
title: Jaeger Trace Collection Failure Runbook
status: approved
owner: On-Call Engineer
created: '2024-07-27T15:34:28.144Z'
updated: '2026-05-08T06:05:04.734Z'
tags:
  - runbook
  - monitoring-stack
summary: Jaeger Trace Collection Failure Runbook
example: true
---

## Service

- **System**: [[SYSTEM-038|Jaeger Tracing System]]
- **Owner team**: Platform / SRE
- **On-call rotation**: PagerDuty schedule "platform-oncall"
- **Slack channel**: #monitoring-ops
- **Runtime**: Kubernetes / Jaeger 1.x / Elasticsearch or Cassandra backend

## Alerts

- `JaegerCollectorDown` - Jaeger collector pod is not running
- `JaegerSpanDropRateHigh` - Jaeger collector span drop rate exceeds 5% for 5 minutes
- `JaegerCollectorQueueFull` - Jaeger collector internal queue utilization exceeds 90%
- `OTelCollectorExportFailure` - OpenTelemetry collector is failing to export spans to Jaeger

## Diagnosis Steps

1. **Check Jaeger collector health** - `kubectl get pods -n monitoring -l app=jaeger-collector`. If pods are not running, check events and logs: `kubectl logs -n monitoring -l app=jaeger-collector`.
2. **Check OTel collector connectivity to Jaeger** - Query `otelcol_exporter_send_failed_spans_total` in Prometheus. A non-zero and increasing counter indicates the OTel collector cannot export to Jaeger.
3. **Check Jaeger storage backend health** - If Jaeger uses Elasticsearch, check the ES cluster health endpoint. If using Cassandra, check the Cassandra pod status. Jaeger will fail to ingest spans if the storage backend is unavailable or returning errors.
4. **Check span ingestion rate** - Query `jaeger_collector_spans_received_total` and `jaeger_collector_spans_dropped_total`. If the drop rate is high relative to received, the collector is overloaded.
5. **Check OTel collector config** - Verify the OTel collector's pipeline config includes a Jaeger/OTLP exporter pointing to the correct Jaeger collector endpoint. Check for auth token issues if mTLS is enabled.

## Remediation Steps

1. **If Jaeger collector pods are down**: Check for OOM kills or crashloops. If OOM, increase memory limits in the Helm values. Restart the collector: `kubectl rollout restart deployment/jaeger-collector -n monitoring`.
2. **If the storage backend is down**: Restore the storage backend first. Jaeger will buffer some spans in its collector queue, but spans will be dropped if the queue fills. Escalate to the storage team.
3. **If the collector queue is full**: Scale up collector replicas: `kubectl scale deployment/jaeger-collector -n monitoring --replicas=3`. This distributes the ingestion load.
4. **If OTel collector is failing exports**: Check the OTel collector pod logs for error details. Common causes: wrong endpoint address, certificate mismatch, or Jaeger collector auth token expired.
5. **If span loss is occurring and cannot be prevented**: Document the time window of the loss. Notify the teams whose traces are affected so they know trace data is incomplete for that period.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer checks Jaeger collector and OTel collector health |
| 15 min | Post findings in #monitoring-ops; note span drop rate and affected services |
| 30 min | If storage backend is down: page Platform Lead; trace loss is occurring |
| 60 min | If Jaeger remains down: escalate to Engineering Manager; document affected time window |

## Dashboards

- [Jaeger Self-Monitoring](https://grafana.example.com/d/jaeger-self) - Span receive rate, drop rate, collector queue depth
- [OTel Collector Health](https://grafana.example.com/d/otel-collector) - Export success/failure rate by service
- [Platform Health Overview](https://grafana.example.com/d/platform-health) - Overall monitoring stack component health
