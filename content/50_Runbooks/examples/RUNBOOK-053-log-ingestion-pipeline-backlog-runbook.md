---
id: RUNBOOK-053
type: runbook
title: Log Ingestion Pipeline Backlog Runbook
status: draft
owner: On-Call Engineer
created: '2024-05-21T15:31:14.081Z'
updated: '2026-12-06T14:50:02.673Z'
tags:
  - runbook
  - monitoring-stack
summary: Log Ingestion Pipeline Backlog Runbook
example: true
---

## Service

- **System**: [[SYSTEM-037|Log Ingestion Pipeline System]]
- **Owner team**: Platform / SRE
- **On-call rotation**: PagerDuty schedule "platform-oncall"
- **Slack channel**: #monitoring-ops
- **Runtime**: Kubernetes / Fluentd or Vector / Loki or Elasticsearch

## Alerts

- `LogIngestionBacklogHigh` - Log pipeline backlog queue depth exceeds 100,000 entries for 5 minutes
- `LogIngestionDropRateHigh` - Log ingestion drop rate exceeds 1% for 2 minutes
- `LogForwarderPodRestartLoop` - Log forwarder DaemonSet pod restarting more than 3 times in 10 minutes
- `LokiIngestionRateLimitHit` - Loki ingestion rate limit exceeded by more than 10% of tenants

## Diagnosis Steps

1. **Check pipeline backlog depth** - Query the pipeline's internal queue depth metric: `log_forwarder_queue_depth_total` in Prometheus. Compare current value to the historical baseline to assess severity.
2. **Identify the pipeline bottleneck** - Check whether the backlog is at the forwarder (collecting from containers) or at the ingestion endpoint (writing to Loki/Elasticsearch). Check both ends of the pipeline for latency metrics.
3. **Check log forwarder pod health** - `kubectl get pods -n monitoring -l app=log-forwarder`. If pods are crashlooping or pending, the forwarder is the bottleneck. Check pod logs for connection errors or memory exhaustion.
4. **Check Loki/Elasticsearch ingestion health** - Query the ingestion endpoint's write latency and error rate. If the backend is returning write errors, that's causing the backlog at the forwarder.
5. **Identify high-volume log sources** - Check which services are producing the most log volume: `sum by (namespace, app) (rate(log_bytes_total[5m]))`. A recently deployed service may be logging excessively.

## Remediation Steps

1. **If the forwarder pods are crashlooping**: Restart the DaemonSet pods: `kubectl rollout restart daemonset/log-forwarder -n monitoring`. Check pod logs after restart for root cause.
2. **If the backend (Loki/Elasticsearch) is the bottleneck**: Scale the backend horizontally or increase its resource limits. For Loki, increase ingestor replicas; for Elasticsearch, add data nodes.
3. **If a specific service is flooding logs**: Temporarily apply a rate limit to that service's log output via the forwarder configuration. Contact the service team to reduce log verbosity.
4. **If the backlog is transient and the pipeline is catching up**: Monitor the queue depth metric. If it is decreasing steadily, no action is needed beyond observation.
5. **If the backlog is so large it will take hours to drain**: Consider temporarily dropping older log entries from the queue to allow current logs to flow. This is a lossy operation — escalate to Platform Lead before doing so.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer checks pipeline backlog depth and forwarder pod health |
| 15 min | Post findings in #monitoring-ops; note which service is generating volume spikes |
| 30 min | If not resolved: page Platform Lead; assess whether log loss is occurring |
| 60 min | If Loki/Elasticsearch is down: escalate to Engineering Manager; investigate backend recovery |

## Dashboards

- [Log Pipeline Health](https://grafana.example.com/d/log-pipeline) - Ingestion rate, backlog depth, drop rate, forwarder latency
- [Loki Overview](https://grafana.example.com/d/loki-overview) - Write throughput, ingestion errors, retention status
- [Platform Health Overview](https://grafana.example.com/d/platform-health) - Overall monitoring stack component health
