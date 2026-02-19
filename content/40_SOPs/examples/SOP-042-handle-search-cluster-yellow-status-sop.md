---
id: SOP-042
type: sop
title: Handle Search Cluster Yellow Status SOP
status: review
owner: Release Manager
created: '2024-02-09T08:49:21.420Z'
updated: '2026-11-19T20:09:01.152Z'
tags:
  - sop
  - search-platform
summary: Handle Search Cluster Yellow Status SOP
related_process: PROCESS-025
related_systems:
  - SYSTEM-021
example: true
---

## Preconditions

- A `search_cluster_yellow` alert has fired or a manual check of cluster health shows status `yellow`
- You have confirmed the cluster is not in `red` status (red requires a more urgent escalation path)
- You have access to the Elasticsearch cluster health API and the Grafana cluster dashboard
- The on-call SRE is informed and available if escalation is needed

## Materials/Access

- Elasticsearch cluster health endpoint: `GET /_cluster/health?level=shards`
- Unassigned shards detail: `GET /_cat/shards?v&h=index,shard,prirep,state,unassigned.reason`
- Cluster allocation explanation: `GET /_cluster/allocation/explain`
- Grafana: Search Cluster Overview dashboard (node disk usage, memory, shard counts)
- kubectl or SSH access to add or restart nodes if needed

## Procedure

1. Call `GET /_cluster/health` and note the number of `unassigned_shards` and the `active_primary_shards` count. Yellow means all primary shards are active but one or more replica shards are unassigned — search is still serving but redundancy is reduced.
2. Identify which indexes have unassigned replicas: `GET /_cat/shards?v&h=index,shard,prirep,state,unassigned.reason` — filter for state `UNASSIGNED`.
3. For each unassigned shard, call `GET /_cluster/allocation/explain` with the shard details. The response will explain why the shard cannot be allocated (e.g., no node with sufficient disk, node filter mismatch, max retry exceeded).
4. If the cause is insufficient disk space on all candidate nodes, check disk usage: `GET /_cat/nodes?v&h=name,disk.used_percent`. If any node is above 85%, you must either free disk space or add a new data node before the replica can be assigned.
5. If the cause is `MAX_RETRIES_EXCEEDED`, reset the retry counter: `POST /_cluster/reroute?retry_failed=true`. This allows Elasticsearch to attempt allocation again.
6. If the cause is a node that has left the cluster, check `GET /_cat/nodes?v` to confirm the node count. If a node has been lost, investigate whether it has restarted or needs to be replaced before replicas will re-allocate.
7. After taking corrective action, watch `GET /_cluster/health` until status returns to `green`. This may take several minutes while shards copy data to the newly assigned replica location.
8. Confirm the cluster is green and post resolution in #search-incidents. Update the alert ticket with root cause and corrective action taken.

## Validation

- `GET /_cluster/health` returns `"status": "green"` with `unassigned_shards: 0`
- `GET /_cat/shards?v` shows no shards in `UNASSIGNED` state
- Grafana cluster dashboard shows all nodes healthy with disk usage below 80%

## Rollback

1. If corrective actions have made the situation worse (e.g., forced reroute caused a shard to be placed on an overloaded node), cancel the allocation: `POST /_cluster/reroute` with a `cancel` action for the problematic shard.
2. Re-examine allocation constraints and identify a node with sufficient capacity to hold the shard.
3. If no suitable node exists, add a new data node to the cluster following the Search Cluster Scaling Process before retrying allocation.
