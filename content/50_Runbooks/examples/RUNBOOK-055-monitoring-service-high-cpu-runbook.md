---
id: RUNBOOK-055
type: runbook
title: Monitoring Service High CPU Runbook
status: approved
owner: On-Call Engineer
created: '2024-08-25T00:34:36.481Z'
updated: '2025-09-17T03:02:22.646Z'
tags:
  - runbook
  - monitoring-stack
summary: Monitoring Service High CPU Runbook
example: true
---

## Service

- **System**: [[SYSTEM-036|Monitoring Platform System]]
- **Owner team**: Platform / SRE
- **On-call rotation**: PagerDuty schedule "platform-oncall"
- **Slack channel**: #monitoring-ops
- **Runtime**: Kubernetes / Multi-component (Prometheus, Grafana, AlertManager, Jaeger)

## Alerts

- `MonitoringServiceHighCPU` - Any monitoring stack pod CPU usage exceeds 90% of limit for 10 minutes
- `PrometheusRuleEvaluationSlow` - Prometheus rule evaluation duration exceeds 1 minute
- `GrafanaHighCPU` - Grafana pod CPU exceeds 80% of limit for 5 minutes
- `OTelCollectorHighCPU` - OTel collector CPU exceeds 85% of limit

## Diagnosis Steps

1. **Identify which monitoring service is CPU-bound** - Run `kubectl top pods -n monitoring` to see current CPU usage across all monitoring pods. The alert should identify the specific component, but verify against live metrics.
2. **Check for recent traffic spike** - Query `rate(scrape_samples_scraped[5m])` for Prometheus, or check Grafana's active user count (`grafana_stat_active_users`) to see if a usage spike is driving the CPU increase.
3. **Check for expensive Prometheus rule evaluations** - If Prometheus is CPU-bound, run `topk(10, prometheus_rule_evaluation_duration_seconds)` to find the slowest recording rules or alerting rules.
4. **Check for expensive Grafana queries** - Review Grafana server logs for slow queries: `kubectl logs -n monitoring grafana-0 | grep -E "query executed in [0-9]{4,}"`. Long-running panel queries drive Grafana CPU usage.
5. **Check for OTel Collector span processing overload** - If the OTel collector is CPU-bound, check `otelcol_processor_batch_batch_size_trigger_send_ratio` and span ingestion rate to see if it is being overwhelmed with span volume.

## Remediation Steps

1. **If Prometheus is CPU-bound due to rule evaluation**: Optimize the slowest recording rules to reduce label cardinality or computation complexity. As an emergency measure, temporarily disable non-critical recording rule groups.
2. **If Prometheus is CPU-bound due to high scrape volume**: Check if a new target was recently added that has an unusually high number of metrics. Consider increasing the scrape interval for non-critical targets.
3. **If Grafana is CPU-bound**: Scale up Grafana replicas to distribute user query load: `kubectl scale deployment/grafana -n monitoring --replicas=2`. Investigate and optimize expensive dashboard queries.
4. **If OTel Collector is CPU-bound**: Scale up OTel collector replicas. Consider enabling head sampling to reduce span volume if the service generating the volume does not require 100% sampling.
5. **If all monitoring services are high CPU simultaneously**: Check for a Kubernetes node resource pressure event that is throttling the entire monitoring namespace.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer identifies the specific monitoring service and checks recent changes |
| 15 min | Post findings in #monitoring-ops with CPU metrics and suspected cause |
| 30 min | If not resolved: page Platform Lead; consider emergency scale-up |
| 60 min | If monitoring degradation is affecting incident response: escalate to Engineering Manager |

## Dashboards

- [Platform Health Overview](https://grafana.example.com/d/platform-health) - CPU and memory usage for all monitoring components
- [Prometheus Self-Monitoring](https://grafana.example.com/d/prometheus-self) - Rule evaluation duration, scrape throughput
- [Grafana Self-Monitoring](https://grafana.example.com/d/grafana-self) - Request rate, query duration, active users
