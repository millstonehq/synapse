---
id: POLICY-025
type: policy
title: Search Infrastructure Scaling Policy
status: draft
owner: VP Engineering
created: '2025-09-27T00:25:20.927Z'
updated: '2026-11-02T19:24:08.474Z'
tags:
  - policy
  - search-platform
summary: Search Infrastructure Scaling Policy
example: true
related_standards:
  - STANDARD-026
  - STANDARD-025
---

## Scope

This policy applies to all capacity planning, auto-scaling configuration, and manual scaling operations for the Search Platform's Elasticsearch clusters, ingestion workers, and query routing infrastructure. It governs both reactive scaling in response to load and proactive scaling in advance of anticipated traffic events. All SRE, DevOps, and Search Platform engineers who modify cluster topology must comply with this policy.

## Rationale

- Under-provisioned search infrastructure directly degrades query latency and availability, violating user-facing SLOs
- Uncontrolled scaling-out without guardrails can create runaway infrastructure costs that exceed budget allocations
- Elasticsearch cluster rebalancing during scaling operations carries risk of shard loss if not executed carefully
- Scaling decisions made without documented thresholds lead to inconsistent on-call responses during traffic spikes

## Policy Statements

- Auto-scaling rules must be defined for all search cluster node pools; manual-only scaling is not permitted for production clusters with more than 3 nodes
- Scaling thresholds must be reviewed and updated quarterly or after any incident where SLOs were breached due to capacity
- Adding data nodes to an Elasticsearch cluster must follow the shard rebalancing procedure defined in [[STANDARD-026|Search Index Schema Standard]]
- Scaling operations that increase cluster cost by more than 20% in a single change require Engineering Manager approval
- All scaling events (up or down) must be logged with timestamp, operator, trigger reason, and resulting node count
- Search infrastructure must maintain a minimum 30% headroom above peak observed query throughput at all times

## Related Standards

- [[STANDARD-026|Search Index Schema Standard]]
- [[STANDARD-025|Search API Response Format Standard]]
