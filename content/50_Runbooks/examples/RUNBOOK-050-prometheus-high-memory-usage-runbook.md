---
id: RUNBOOK-050
type: runbook
title: Prometheus High Memory Usage Runbook
status: approved
owner: On-Call Engineer
created: '2024-03-12T16:54:02.044Z'
updated: '2026-09-16T20:40:59.737Z'
tags:
  - runbook
  - monitoring-stack
summary: Prometheus High Memory Usage Runbook
example: true
---

## Service

- **System**: [[SYSTEM-036|Prometheus Monitoring System]]
- **Owner team**: Platform / SRE
- **On-call rotation**: PagerDuty schedule "platform-oncall"
- **Slack channel**: #monitoring-ops
- **Runtime**: Kubernetes / Prometheus 2.x / Persistent Volume (SSD)

## Alerts

- `PrometheusHighMemoryUsage` - Prometheus process memory exceeds 85% of pod memory limit for 10 minutes
- `PrometheusTSDBHighCardinality` - Active series count exceeds 5 million
- `PrometheusHeadCompactionSlow` - Head compaction taking longer than 5 minutes
- `PrometheusWALReplayDurationHigh` - WAL replay on startup exceeds 10 minutes

## Diagnosis Steps

1. **Check current memory and cardinality** - Run `curl -s http://prometheus:9090/api/v1/query?query=process_resident_memory_bytes` and `prometheus_tsdb_head_series` to get current values. Compare against the pod's memory limit from `kubectl describe pod prometheus-0 -n monitoring`.
2. **Identify high-cardinality metrics** - Open the Prometheus UI at `Status > TSDB Status`. Review the "Top 10 metric names by series count" table. Any metric with more than 500,000 series is likely contributing to the memory problem.
3. **Correlate with recent deploys** - Check if a service was recently deployed that may have introduced high-cardinality labels. Query `topk(5, count by (__name__)({__name__!=""}))` and compare against the previous day's values.
4. **Check for unbounded label values** - For the top-cardinality metric, run `count by (job, instance) ({metric_name})` to see if a specific target is generating an unusual number of time series.
5. **Check scrape config for new targets** - Run `curl http://prometheus:9090/api/v1/targets | jq '.data.activeTargets | length'` and compare to expected target count. A new scrape job may be importing many series.

## Remediation Steps

1. **If caused by a recent high-cardinality deploy**: Follow [[SOP-078|Handle Prometheus Cardinality Explosion SOP]] to add a metric_relabel_config to drop the offending label. Deploy the config change via GitOps.
2. **If overall series count is high but no single metric dominates**: Increase Prometheus pod memory limit by 25% via the Helm values file. This buys time for the root cause to be addressed.
3. **If Prometheus is about to OOM**: Immediately drop the highest-cardinality metric via scrape config relabeling and trigger a head compaction: `curl -X POST http://prometheus:9090/api/v1/admin/tsdb/clean_tombstones`.
4. **If the WAL is very large**: Restart Prometheus during a low-traffic window. Note that this causes a scrape gap. Post in #monitoring-ops before restarting.
5. **If cardinality has been growing steadily over weeks**: Engage the service owner responsible for the top-cardinality metrics to refactor label usage in their application code.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and checks TSDB status |
| 10 min | Post current series count and top cardinality metrics in #monitoring-ops |
| 20 min | If not resolved: page Platform Lead via PagerDuty |
| 40 min | If Prometheus is OOMing and not stabilizing: involve Engineering Manager, consider emergency memory increase |

## Dashboards

- [Prometheus Self-Monitoring](https://grafana.example.com/d/prometheus-self) - Memory usage, series count, scrape duration, head compaction
- [TSDB Cardinality](https://grafana.example.com/d/tsdb-cardinality) - Top metrics by series, label cardinality heatmap
- [Platform Health Overview](https://grafana.example.com/d/platform-health) - Overall monitoring stack component health
