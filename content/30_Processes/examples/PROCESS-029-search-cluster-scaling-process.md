---
id: PROCESS-029
type: process
title: Search Cluster Scaling Process
status: accepted
owner: Platform Lead
created: '2024-10-26T02:20:00.689Z'
updated: '2026-10-13T10:20:42.700Z'
tags:
  - process
  - search-platform
summary: Search Cluster Scaling Process
related_standards:
  - STANDARD-029
  - STANDARD-025
related_sops:
  - SOP-041
  - SOP-048
related_systems:
  - SYSTEM-023
example: true
---

## Purpose

The Search Cluster Scaling Process provides a structured approach for adding or removing capacity from the Elasticsearch cluster that powers the Search Platform. Both horizontal scaling (adding/removing data nodes) and vertical scaling (resizing nodes) are covered. The process ensures that shard rebalancing is managed safely and that scaling operations do not disrupt query availability.

## Scope

- Adding data nodes to the Elasticsearch cluster to increase storage or query throughput capacity
- Removing data nodes during scale-down following a traffic reduction
- Resizing master-eligible nodes during scheduled maintenance
- Emergency scaling triggered by resource saturation alerts

## Roles and Responsibilities

- **SRE Engineer**: Executes the scaling operation, monitors shard rebalancing, and validates cluster health post-scaling
- **Platform Lead**: Approves planned scaling changes; authorizes emergency scaling for urgent situations
- **FinOps / Cost Owner**: Reviews scaling decisions that increase monthly infrastructure cost by more than 15%

## Triggers

- Cluster memory utilization exceeds 80% for more than 30 minutes
- Query latency P95 exceeds SLO threshold and diagnosis confirms insufficient node capacity
- Planned traffic event (product launch, marketing campaign) requires proactive capacity increase
- Quarterly capacity review recommends scaling adjustment

## Inputs

- Current cluster topology: node count, node sizes, shard allocation, and resource utilization metrics
- Scaling plan specifying target node count, node size, and expected shard rebalancing duration
- Approved change ticket with Platform Lead sign-off

## Outputs

- Updated cluster topology with new node configuration
- Shard rebalancing completed and cluster status returned to green
- Change ticket closed with post-scaling metrics confirming improved resource headroom

## Steps

1. Verify current cluster status is green; do not proceed if the cluster is yellow or red - resolve existing shard issues first
2. Calculate target node count based on projected memory headroom and storage requirements; document the calculation in the change ticket
3. For scale-out: provision new nodes using the infrastructure-as-code templates; for scale-in: identify nodes to decommission and verify they hold no unique shard copies
4. Temporarily set `cluster.routing.allocation.exclude._ip` to the nodes being removed (scale-in) or monitor allocation progress for new nodes (scale-out)
5. Monitor shard rebalancing progress using the Cluster Pending Tasks API; wait for active shards to reach zero before proceeding
6. Verify cluster status returns to green and all shards are allocated on the new topology
7. Run a sample of production query patterns against the updated cluster and confirm P95 latency meets SLO
8. Close the change ticket with post-scaling node count, cluster health, and latency metrics

## Controls

- Cluster must be green before any scaling operation begins
- Scale-in operations must use shard exclusion routing to drain nodes before removal
- Scaling operations that increase cost by more than 15% require FinOps review
- All scaling events are logged in the infrastructure change registry
