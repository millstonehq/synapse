---
id: RUNBOOK-030
type: runbook
title: Search Latency Spike Runbook
status: approved
owner: On-Call Engineer
created: '2024-04-09T22:45:55.812Z'
updated: '2026-03-23T01:21:22.118Z'
tags:
  - runbook
  - search-platform
summary: Search Latency Spike Runbook
example: true
---

## Service

- **System**: [[SYSTEM-021|Search Query Service]]
- **Owner team**: Search Platform Engineering
- **On-call rotation**: PagerDuty schedule "search-oncall"
- **Slack channel**: #search-incidents
- **Runtime**: Kubernetes / Node.js 20 / Elasticsearch 8

## Alerts

- `search_latency_p95_high` - P95 query latency exceeds 500ms for 5 consecutive minutes
- `search_latency_p99_high` - P99 query latency exceeds 2000ms for 3 consecutive minutes
- `search_timeout_rate_high` - Query timeout rate exceeds 1% over any 5-minute window

## Diagnosis Steps

1. **Check if a recent deployment occurred** - Review #search-deployments for any ranking or service deploys in the past hour. If latency spiked within 30 minutes of a deploy, rollback is the first remediation to consider.
2. **Check cluster resource utilization** - Run `GET /_cat/nodes?v&h=name,cpu,heap.percent,load_1m` to see if any nodes are CPU or memory saturated. High CPU on data nodes indicates the cluster is processing more compute-intensive queries than capacity allows.
3. **Identify slow queries** - Check the Elasticsearch slow query log in Kibana for the past 30 minutes. Look for queries with `took` values that match the observed P95 spike. Common causes: large aggregations, deep pagination (`from` + `size` > 10,000), or queries against un-mapped fields.
4. **Check active shard recovery or rebalancing** - Run `GET /_cat/recovery?v&active_only=true`. Active shard movement consumes I/O and can degrade query throughput significantly.
5. **Check for traffic volume increase** - Review Grafana for QPS (queries per second) trend. A sudden traffic spike without a proportional increase in cluster capacity will cause latency to rise.

## Remediation Steps

1. **If caused by a recent deploy**: Roll back immediately using the Deploy Search Ranking Update SOP rollback procedure. Latency should recover within 5 minutes of rollback.
2. **If caused by expensive queries**: Use `POST /_tasks/<task-id>/_cancel` to terminate long-running queries. If the source is a specific client or service, contact that team to apply query limits or timeout settings.
3. **If caused by shard recovery**: Throttle recovery bandwidth to reduce I/O contention: `PUT /_cluster/settings` with `"transient": {"indices.recovery.max_bytes_per_sec": "40mb"}`. Latency will recover once recovery completes.
4. **If caused by traffic spike**: Scale out the cluster horizontally using the Scale Search Cluster Horizontally SOP. As an immediate measure, reduce query complexity by disabling expensive features (e.g., highlighting, large aggregation buckets) via the search service feature flags.
5. **If cause is unknown after 20 minutes**: Enable query profiling on a sample of requests and escalate to the Search Platform tech lead with the profile data.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges and checks for recent deploys |
| 10 min | Post initial assessment in #search-incidents with latency numbers |
| 25 min | If not resolved: page Search Platform tech lead via PagerDuty |
| 45 min | If not resolved: page Engineering Manager; begin user-facing communication |
| 60 min | If not resolved: initiate major incident in #incident-war-room |

## Dashboards

- [Search Query Performance](https://grafana.example.com/d/search-query-perf) - P50/P95/P99 latency, error rate, QPS
- [Search Cluster Resources](https://grafana.example.com/d/search-cluster-resources) - CPU, heap, I/O per node
- [Search Slow Queries](https://kibana.example.com/app/discover#/search-slow-logs) - Queries above slow log threshold with full details
- [Search Traffic Overview](https://grafana.example.com/d/search-traffic) - QPS by query type and client
