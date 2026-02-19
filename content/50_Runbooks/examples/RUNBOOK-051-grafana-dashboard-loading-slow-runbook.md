---
id: RUNBOOK-051
type: runbook
title: Grafana Dashboard Loading Slow Runbook
status: approved
owner: On-Call Engineer
created: '2025-10-18T19:07:41.977Z'
updated: '2025-09-22T08:45:09.648Z'
tags:
  - runbook
  - monitoring-stack
summary: Grafana Dashboard Loading Slow Runbook
example: true
---

## Service

- **System**: [[SYSTEM-036|Grafana Monitoring System]]
- **Owner team**: Platform / SRE
- **On-call rotation**: PagerDuty schedule "platform-oncall"
- **Slack channel**: #monitoring-ops
- **Runtime**: Kubernetes / Grafana 10.x / PostgreSQL backend

## Alerts

- `GrafanaDashboardLoadTimeHigh` - Dashboard load time P95 exceeds 10 seconds for 5 minutes
- `GrafanaQueryTimeout` - More than 5% of Grafana panel queries timing out in the last 5 minutes
- `GrafanaHighMemoryUsage` - Grafana pod memory exceeds 80% of limit
- `PrometheusQueryDurationHigh` - Prometheus query engine P95 latency exceeds 30 seconds

## Diagnosis Steps

1. **Identify which dashboards are slow** - Check the Grafana server logs: `kubectl logs -n monitoring grafana-0 | grep "query executed"`. Look for dashboards with query execution times over 5 seconds. Note the panel queries that are slowest.
2. **Check Prometheus query performance** - Open the Prometheus UI at `Graph` and run the slow query from the Grafana panel. If it times out or takes more than 30 seconds, the issue is in the query or Prometheus itself.
3. **Check for expensive queries** - Run `topk(5, prometheus_engine_query_duration_seconds)` in Prometheus to find the slowest query categories. Range queries over long time windows and high-cardinality aggregations are common culprits.
4. **Check Grafana pod resource usage** - `kubectl top pods -n monitoring`. If Grafana is CPU or memory constrained, it may be slow to execute queries even if Prometheus itself is healthy.
5. **Check Prometheus target scrape lag** - `prometheus_target_scrape_pool_exceeded_target_limit` and `prometheus_rule_evaluation_duration_seconds` can indicate Prometheus is overloaded, causing slow query responses.

## Remediation Steps

1. **If a specific dashboard query is slow**: Optimize the query by reducing the range window, adding more specific label matchers, or replacing high-cardinality aggregations with pre-computed recording rules.
2. **If Prometheus is slow overall**: Check if cardinality is too high (see RUNBOOK-050) or if too many rules are evaluated concurrently. Consider adding recording rules to pre-aggregate expensive metrics.
3. **If Grafana is memory-constrained**: Increase Grafana pod memory limit via Helm values. Alternatively, reduce the number of concurrent dashboard users if a usage spike is the cause.
4. **If multiple users are loading heavy dashboards simultaneously**: Enable Grafana query caching if not already enabled. This reduces duplicate Prometheus queries from repeated dashboard loads.
5. **If the issue is a single extremely expensive query**: Temporarily disable that panel in the dashboard and open a ticket to rewrite the query before re-enabling it.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer identifies slow dashboards and begins query analysis |
| 15 min | Post findings in #monitoring-ops: which dashboards, which queries, initial diagnosis |
| 30 min | If not resolved: page Platform Lead; consider increasing Grafana/Prometheus resources |
| 60 min | If dashboards remain unusable: escalate to Engineering Manager; evaluate emergency scale-up |

## Dashboards

- [Grafana Self-Monitoring](https://grafana.example.com/d/grafana-self) - Request latency, query duration, active users
- [Prometheus Self-Monitoring](https://grafana.example.com/d/prometheus-self) - Query engine latency, evaluation duration
- [Platform Health Overview](https://grafana.example.com/d/platform-health) - Overall monitoring stack component health
