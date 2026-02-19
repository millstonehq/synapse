---
id: RUNBOOK-035
type: runbook
title: Search Replica Sync Failure Runbook
status: approved
owner: On-Call Engineer
created: '2024-10-26T20:01:56.409Z'
updated: '2025-10-08T05:44:14.376Z'
tags:
  - runbook
  - search-platform
summary: Search Replica Sync Failure Runbook
example: true
---

## Service

- **System**: [[SYSTEM-021|Search Cluster]]
- **Owner team**: Search Platform Engineering
- **On-call rotation**: PagerDuty schedule "search-oncall"
- **Slack channel**: #search-incidents
- **Runtime**: Kubernetes / Elasticsearch 8 / dedicated data node pool

## Alerts

- `search_replica_unassigned` - One or more replica shards have been unassigned for more than 5 minutes
- `search_replication_lag` - Replica shard recovery is progressing at less than 10MB/s, indicating a slow sync
- `search_cluster_yellow` - Cluster health is yellow due to unassigned replica shards

## Diagnosis Steps

1. **Identify unassigned replicas** - Run `GET /_cat/shards?v&h=index,shard,prirep,state,unassigned.reason,node` and filter for `prirep=r` (replica) and `state=UNASSIGNED`. Note the index and shard numbers.
2. **Get allocation explanation** - For each unassigned replica, call `GET /_cluster/allocation/explain` with the shard details to understand the specific reason for non-allocation (e.g., no eligible node, disk watermark breached, max retries exceeded).
3. **Check node disk capacity** - Run `GET /_cat/nodes?v&h=name,disk.used_percent,disk.avail`. If nodes are above 85% disk usage (the high watermark), Elasticsearch will not assign additional replicas to those nodes.
4. **Check if the primary shard is healthy** - Confirm the primary for the affected shard is in `STARTED` state. A replica cannot sync from an unhealthy or relocating primary.
5. **Check network throughput between nodes** - If replication lag is the issue (slow sync), verify there is no network I/O saturation between the primary and the candidate replica node using Grafana network metrics.

## Remediation Steps

1. **If the cause is MAX_RETRIES_EXCEEDED**: Elasticsearch has given up trying to allocate the replica after repeated failures. Reset the retry counter: `POST /_cluster/reroute?retry_failed=true` to allow allocation to be attempted again.
2. **If the cause is disk watermark**: Free disk space on the target nodes (delete old indexes, expand volumes) or add a new data node with available disk space. The replica will be allocated once a suitable node is available.
3. **If the cause is a node filter mismatch** (allocation filtering rules): Review allocation settings with `GET /_cluster/settings` and `GET /<index>/_settings`. Remove or adjust the filter that is preventing replica placement.
4. **If replication sync is extremely slow**: Increase the recovery bandwidth temporarily: `PUT /_cluster/settings` with `"transient": {"indices.recovery.max_bytes_per_sec": "100mb"}`. Monitor I/O impact on query performance.
5. **If the same replica keeps failing to sync**: The target node may have an underlying storage issue. Exclude it from allocation and investigate: `PUT /_cluster/settings` with `"transient": {"cluster.routing.allocation.exclude._ip": "<node-ip>"}`.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer confirms replica state and gets allocation explanation |
| 15 min | Post status in #search-incidents (search is still serving via primaries) |
| 30 min | If multiple replicas are failing: page Search Platform tech lead |
| 60 min | If cluster remains yellow and no root cause identified: page Engineering Manager |

## Dashboards

- [Search Cluster Overview](https://grafana.example.com/d/search-cluster-overview) - Shard allocation status, cluster health color
- [Search Cluster Resources](https://grafana.example.com/d/search-cluster-resources) - Disk usage per node, network I/O
- [Search Shard Recovery](https://grafana.example.com/d/search-shard-recovery) - Active recoveries, recovery throughput, estimated completion time
