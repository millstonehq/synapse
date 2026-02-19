---
id: SOP-045
type: sop
title: Scale Search Cluster Horizontally SOP
status: approved
owner: SRE Lead
created: '2025-09-14T20:14:28.788Z'
updated: '2025-12-23T16:39:47.222Z'
tags:
  - sop
  - search-platform
summary: Scale Search Cluster Horizontally SOP
related_process: PROCESS-065
related_systems:
  - SYSTEM-022
example: true
---

## Preconditions

- Cluster health is green; do not scale if the cluster is yellow or red
- An approved change ticket exists with the target node count and justification
- Current cluster resource utilization has been recorded as a baseline (CPU, heap usage, disk usage per node)
- For scale-in: confirmed that the nodes to be removed hold no unique (un-replicated) shard copies
- Infrastructure-as-code templates for the node instance type are available and tested in staging

## Materials/Access

- Access to the infrastructure provisioning system (Terraform or equivalent) with the search cluster module
- Elasticsearch cluster management APIs
- Grafana: Search Cluster Overview dashboard (shard allocation, node resource utilization)
- `GET /_cat/nodes?v` and `GET /_cat/shards?v` for real-time cluster state inspection
- Change ticket ID with Platform Lead approval

## Procedure

1. Run `GET /_cluster/health` and confirm status is `green`. Record current `number_of_nodes`, `active_shards`, and `relocating_shards` as baseline.
2. For scale-out: provision the new node(s) using the infrastructure-as-code template. Set the node role to `data` (not `master-eligible`) unless adding dedicated master nodes. Wait for provisioning to complete.
3. For scale-in: identify target nodes for removal. Set allocation exclusion to drain shards off the target nodes: `PUT /_cluster/settings` with `"transient": {"cluster.routing.allocation.exclude._ip": "<node-ip>"}`.
4. Monitor shard rebalancing via `GET /_cat/shards?v` — wait until all shards have moved off the excluded nodes (scale-in) or until new nodes have received their share of shards (scale-out). Use `GET /_cat/recovery?v` to track active shard movements.
5. During rebalancing, monitor cluster throughput on Grafana to confirm indexing and query rates remain within SLOs. If cluster I/O saturates, pause the rebalancing: `PUT /_cluster/settings` with `"transient": {"cluster.routing.allocation.enable": "none"}`.
6. Once rebalancing is complete and cluster is green, for scale-in: terminate the drained nodes and clear the allocation exclusion setting by setting it to `""`.
7. Run `GET /_cluster/health` to confirm the cluster is green with the new node count. Verify no shards are relocating or unassigned.
8. Run a set of representative queries and confirm P95 latency meets SLO. Record post-scaling metrics in the change ticket and close it.

## Validation

- `GET /_cluster/health` returns `green` with the expected `number_of_nodes`
- `GET /_cat/shards?v` shows no unassigned or relocating shards
- Grafana shows node memory and disk utilization distributed evenly across the new topology
- P95 query latency is at or below the pre-scaling baseline

## Rollback

1. For scale-out rollback: add the newly added nodes back to the exclusion list and drain shards off them using the same procedure as scale-in.
2. Once drained, terminate the extra nodes and clear the exclusion setting.
3. For scale-in rollback: re-provision the removed nodes and allow Elasticsearch to rebalance shards back onto them.
