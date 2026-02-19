---
id: RUNBOOK-078
type: runbook
title: Prometheus Disk Full Recovery Runbook
status: approved
owner: On-Call Engineer
created: '2025-11-30T02:26:42.124Z'
updated: '2025-03-13T14:44:16.799Z'
tags:
  - runbook
  - monitoring-stack
summary: Prometheus Disk Full Recovery Runbook
example: true
---

## Service

- **System**: [[SYSTEM-036|Metrics Collection Service]]
- **Owner team**: Monitoring Platform Engineering
- **On-call rotation**: PagerDuty schedule "monitoring-oncall"
- **Slack channel**: #monitoring-incidents
- **Runtime**: Kubernetes / Prometheus 2.x / Node Exporter / Thanos Sidecar

## Alerts

- `PrometeusDiskFull` - Prometheus TSDB data directory has less than 5% free space remaining; alert fires after 15 minutes
- `PrometheusDiskPredictedFull` - Linear prediction indicates disk will be full within 4 hours at the current ingestion rate
- `PrometheusRemoteWriteQueueFull` - Remote write queue is backing up; Prometheus cannot forward samples to long-term storage
- `PrometheusCompactionFailed` - TSDB head compaction has failed; blocks are not being committed to disk correctly
- `PrometheusStorageErrors` - Prometheus is logging storage write errors; samples may be dropped

## Diagnosis Steps

1. **Confirm which Prometheus instance is affected** - The monitoring stack runs a HA pair (`prometheus-0` and `prometheus-1`). Check both: `kubectl get pods -n monitoring -l app=prometheus`. Identify whether one or both instances are affected. If only one instance has the disk issue, the HA pair is still partially operational and the immediate urgency is lower.

2. **Check current disk usage** - SSH into the affected pod and inspect the data directory: `kubectl exec -n monitoring prometheus-0 -- df -h /prometheus-data`. Also check the TSDB stats endpoint for block-level breakdown: `curl http://prometheus-0.monitoring.svc:9090/api/v1/status/tsdb`.

3. **Check ingestion rate for anomalies** - Query the Prometheus metrics endpoint or the Grafana prometheus overview dashboard. Look for a recent spike in `prometheus_tsdb_head_samples_appended_total` rate. A spike often indicates a cardinality explosion from a new label value being introduced by a service deployment.

4. **Check for stale blocks not being compacted** - Run `kubectl exec -n monitoring prometheus-0 -- ls -lh /prometheus-data/` and look for many small block directories. If compaction is not running, blocks accumulate. Check `prometheus_tsdb_compactions_total` and `prometheus_tsdb_compaction_duration_seconds` for recent activity.

5. **Check remote write queue health** - If the Thanos sidecar or remote write target is unreachable, Prometheus buffers samples locally instead of forwarding them. Check `prometheus_remote_storage_queue_highest_sent_timestamp_seconds` lag. A large lag means samples are piling up locally.

6. **Check for high-cardinality metrics** - Run the cardinality analysis query: `topk(10, count by (__name__)({__name__=~".+"}))`. Metrics with millions of series are the most likely cause of sudden disk growth. Compare against the previous week's values.

## Remediation Steps

1. **Immediate space recovery — delete old chunks from WAL**: If disk is critically full (< 2%), the Prometheus process may have already stopped writing. Free space immediately by deleting WAL segments: `kubectl exec -n monitoring prometheus-0 -- find /prometheus-data/wal -name "0000*" -mmin +60 -delete`. This is safe because WAL segments older than 1 hour have been checkpointed. Do not delete checkpoint files.

2. **Expand the PersistentVolumeClaim**: If the disk is consistently running near capacity, expand the PVC. Check if the storage class supports online expansion: `kubectl get storageclass`. If supported, patch the PVC: `kubectl patch pvc prometheus-data-prometheus-0 -n monitoring -p '{"spec":{"resources":{"requests":{"storage":"500Gi"}}}}'`. The volume will expand without restarting the pod.

3. **If cardinality explosion is the cause — drop the offending metric**: Identify the high-cardinality metric from step 6. Add a `metric_relabel_configs` drop rule to the Prometheus scrape config for that job, then reload: `curl -X POST http://prometheus-0.monitoring.svc:9090/-/reload`. This stops new samples being written. Existing data in TSDB will be retained until the block retention period elapses (default 15 days).

4. **If remote write backlog is causing local accumulation — restart the Thanos sidecar**: If the Thanos sidecar is the bottleneck, restart it: `kubectl rollout restart deployment/thanos-sidecar -n monitoring`. This clears in-flight request state without affecting the Prometheus TSDB. Monitor remote write lag for 10 minutes after restart.

5. **If compaction is failing — force a compaction**: Stop Prometheus writes temporarily with `POST /-/quit` (this takes the pod down — only do this if the disk is so full that a restart is acceptable), then restart the pod. Prometheus performs a compaction on startup if there are uncommitted blocks. Alternatively, for non-critical situations, wait for the next automatic compaction interval (default 2 hours).

6. **Restore from the HA peer if one instance is unrecoverable**: If `prometheus-0` is unrecoverable and its PVC needs to be wiped, delete the PVC and let the StatefulSet recreate it. `prometheus-1` continues serving queries during this time (AlertManager is configured to query both). The rebuilt instance will backfill recent history via the remote write receive path.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins disk usage assessment |
| 5 min | Post initial assessment in #monitoring-incidents: which instance, how full, probable cause |
| 10 min | If disk is > 95% full and growing: apply immediate remediation (step 1 or 2) |
| 20 min | If cause not identified or space not recovering: page Monitoring Platform tech lead |
| 45 min | If both Prometheus instances are affected and alerting is dark: page Engineering Manager and declare monitoring SEV-1 |

**Who to escalate to:**
- Monitoring Platform tech lead: PagerDuty schedule "monitoring-leads"
- Infrastructure issues (PVC expansion, K8s nodes): PagerDuty schedule "infra-oncall"
- Cardinality explosion from a specific service team: page that team's on-call directly

## Dashboards

- [Prometheus Overview](https://grafana.example.com/d/prometheus-overview) - Ingestion rate, TSDB head series, remote write lag, disk usage
- [Prometheus TSDB Details](https://grafana.example.com/d/prometheus-tsdb) - Block count, compaction rate, WAL size, head chunk count
- [Cardinality Analysis](https://grafana.example.com/d/prometheus-cardinality) - Top-N metrics by series count, label value cardinality breakdown
- [Remote Write Health](https://grafana.example.com/d/prometheus-remote-write) - Queue depth, send rate, error rate, last successful send timestamp
- [Kubernetes PVC Usage](https://grafana.example.com/d/k8s-pvc) - PVC capacity and usage across the monitoring namespace
