---
id: SOP-048
type: sop
title: Handle Elasticsearch Shard Relocation SOP
status: proposed
owner: DevOps Lead
created: '2024-01-10T19:52:17.135Z'
updated: '2025-07-23T13:03:09.521Z'
tags:
  - sop
  - search-platform
summary: Handle Elasticsearch Shard Relocation SOP
related_process: PROCESS-025
related_systems:
  - SYSTEM-024
example: true
---

## Preconditions

- Shard relocation is occurring in the cluster (visible via `GET /_cluster/health` showing `relocating_shards > 0`)
- You have determined whether the relocation is expected (triggered by a scaling operation) or unexpected (triggered by node departure or disk pressure)
- Cluster health is yellow or green; if red, treat as a higher-severity incident

## Materials/Access

- Elasticsearch cluster management API access
- `GET /_cat/recovery?v&active_only=true` to see active shard recovery/relocation progress
- `GET /_cat/nodes?v&h=name,disk.used_percent,heap.percent,load_1m` for node resource state
- Grafana: Search Cluster Overview dashboard (relocating shard count, node I/O)
- kubectl or SSH access for node-level investigation if needed

## Procedure

1. Determine the scope of relocation: `GET /_cluster/health` for relocating shard count; `GET /_cat/recovery?v&active_only=true` to see which shards are moving and between which nodes.
2. Determine the cause of relocation. Common causes: (a) a new node joined the cluster and Elasticsearch is rebalancing, (b) a node left the cluster and shards are being re-replicated, (c) disk watermark was breached on a node and shards are being evacuated.
3. Check disk usage across nodes: `GET /_cat/nodes?v&h=name,disk.used_percent`. If any node is above the high watermark (default 90%), Elasticsearch will actively move shards off that node. If disk pressure is the cause, you must address disk space before relocation will stabilize.
4. If the relocation was triggered by a new node joining (expected behavior), verify the relocation is progressing at a reasonable rate via Grafana. Throttle if I/O is too high: `PUT /_cluster/settings` with `"transient": {"indices.recovery.max_bytes_per_sec": "40mb"}`.
5. If relocation was triggered by node departure (unexpected), confirm the node has not rejoined the cluster: `GET /_cat/nodes?v`. If the node is gone permanently, wait for replica promotion and re-replication to complete; monitor until cluster returns to green.
6. If relocation is thrashing (shards moving repeatedly between nodes), check for conflicting allocation rules: `GET /_cluster/allocation/explain`. Resolve allocation rule conflicts before relocation will stabilize.
7. Once relocating shard count reaches zero and cluster health returns to green, confirm the final shard distribution is balanced: `GET /_cat/shards?v&h=index,shard,prirep,state,node` — verify shards are spread across nodes evenly.
8. Post status update in #search-operations with root cause and resolution.

## Validation

- `GET /_cluster/health` shows `relocating_shards: 0` and status `green`
- `GET /_cat/nodes?v` shows all expected nodes present with disk usage below 85%
- Grafana shows cluster I/O has returned to normal levels

## Rollback

1. If throttling or allocation settings were changed and are causing issues, reset them: `PUT /_cluster/settings` with `"transient": null` to clear all transient settings.
2. If a forced reroute was attempted and caused data inconsistency, escalate to the Platform Lead immediately — do not attempt further manual shard moves without expert review.
