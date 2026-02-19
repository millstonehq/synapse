---
id: RUNBOOK-029
type: runbook
title: Search Cluster High Memory Usage Runbook
status: deprecated
owner: On-Call Engineer
created: '2024-11-17T04:45:19.804Z'
updated: '2025-05-31T10:27:53.486Z'
tags:
  - runbook
  - search-platform
summary: Search Cluster High Memory Usage Runbook
example: true
---

## Service

- **System**: [[SYSTEM-021|Search Cluster]]
- **Owner team**: Search Platform Engineering
- **On-call rotation**: PagerDuty schedule "search-oncall"
- **Slack channel**: #search-incidents
- **Runtime**: Kubernetes / Elasticsearch 8 / JVM 17 / Linux

## Alerts

- `search_heap_usage_high` - JVM heap usage exceeds 85% on any data node for 5 minutes
- `search_gc_pause_high` - JVM GC pause duration exceeds 500ms for 3 consecutive collections
- `search_fielddata_evictions_high` - Fielddata eviction rate exceeds 100/min, indicating memory pressure causing cache churn
- `search_node_oom_kill` - A search node process has been OOM-killed by the kernel

## Diagnosis Steps

1. **Identify the affected node** - Run `GET /_cat/nodes?v&h=name,heap.current,heap.max,heap.percent` to see heap usage per node. Identify which node(s) are above 85%.
2. **Check for large aggregations or field data** - Run `GET /_cat/nodes?v&h=name,fielddata.memory_size,query_cache.memory_size,segments.memory` to identify if fielddata or query cache is consuming the heap. High fielddata often indicates un-cached aggregation queries running against text fields.
3. **Check for active heavy queries** - Run `GET /_tasks?actions=*search&detailed=true` to find long-running search tasks. A single expensive aggregation query can consume gigabytes of heap.
4. **Check segment memory** - Run `GET /_cat/indices?v&h=index,segments.count,segments.memory` to identify indexes with many segments. High segment counts increase resident memory overhead.
5. **Review recent deployments** - Check #search-deployments for any ranking or indexing changes in the past 2 hours that may have introduced query patterns with higher memory footprint.

## Remediation Steps

1. **If caused by a single expensive query**: Cancel the task using `POST /_tasks/<task-id>/_cancel`. Alert the query owner and ask them to optimize the query or schedule it for off-peak hours.
2. **If fielddata cache is too large**: Clear fielddata via `POST /<index-name>/_cache/clear?fielddata=true`. Then set a fielddata circuit breaker limit: `PUT /_cluster/settings` with `"transient": {"indices.breaker.fielddata.limit": "40%"}` to prevent recurrence.
3. **If segment memory is high**: Force merge low-traffic indexes: `POST /<index-name>/_forcemerge?max_num_segments=1`. Schedule this during off-peak hours as it is CPU-intensive.
4. **If heap is exhausted and the node is unresponsive**: Restart the node pod in Kubernetes: `kubectl rollout restart deployment/elasticsearch-data -n search`. Elasticsearch will re-join the cluster after restart; verify shard recovery completes.
5. **If multiple nodes are simultaneously high**: The cluster is likely under-sized for current query load. Scale out by adding data nodes following the Scale Search Cluster Horizontally SOP.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins node identification |
| 10 min | Post initial assessment in #search-incidents |
| 20 min | If not resolved: page Search Platform tech lead via PagerDuty |
| 40 min | If not resolved: page Engineering Manager; assess user impact |
| 60 min | If not resolved: initiate major incident process in #incident-war-room |

## Dashboards

- [Search Cluster Memory](https://grafana.example.com/d/search-cluster-memory) - JVM heap, GC activity, fielddata cache per node
- [Search Query Performance](https://grafana.example.com/d/search-query-perf) - Query latency, error rate, active task count
- [Search Cluster Overview](https://grafana.example.com/d/search-cluster-overview) - Node health, shard counts, cluster status
- [Search Slow Logs](https://kibana.example.com/app/discover#/search-slow-logs) - Queries exceeding slow log threshold
