---
id: POSTMORTEM-023
type: postmortem
title: Elasticsearch Cluster Split-Brain 2025-02-26
status: approved
owner: Incident Commander
created: '2024-11-28T18:10:55.258Z'
updated: '2026-04-29T20:03:22.860Z'
tags:
  - postmortem
  - search-platform
summary: Elasticsearch Cluster Split-Brain 2025-02-26
incident_number: INC-454
severity: SEV-2
incident_date: '2024-03-21'
detection_time: '2025-04-19T06:32:57.115Z'
resolution_time: '2025-01-24T10:46:55.490Z'
total_duration: ~30 minutes
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-048
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On February 26, 2025, the Elasticsearch cluster experienced a split-brain event lasting approximately 30 minutes. A network partition between two of the three master-eligible data nodes caused the cluster to temporarily elect two masters, resulting in conflicting index writes and query inconsistency. When the partition resolved, Elasticsearch's conflict resolution merged the diverged state, but approximately 1,200 document updates written during the split were applied twice, resulting in duplicate entries in the index.

The duplicate documents were identified and removed by a cleanup job within 6 hours of the incident. No search queries failed during the split, but result quality was degraded during the window due to duplicate results appearing.

## Timeline

- **03:42** - Network packet loss begins between `es-data-1` and `es-data-3` in different AZs (AWS network event)
- **03:44** - `es-data-3` loses contact with `es-data-1`; detects only itself and `es-data-2` as reachable; elects a new master
- **03:44** - `es-data-1` retains quorum with `es-data-2` from its perspective; original master remains
- **03:44** - Two masters active simultaneously; cluster enters split-brain state
- **03:46** - `search_cluster_health_yellow` alert fires (degraded shard state)
- **03:48** - On-call engineer acknowledges; checks cluster health API; sees two master-eligible nodes reporting different cluster states
- **03:52** - On-call pages tech lead; both engineers assess the partition
- **04:02** - AWS network event resolves; `es-data-1` and `es-data-3` regain connectivity
- **04:04** - Elasticsearch conflict resolution runs; cluster re-forms under a single master
- **04:12** - Cluster reaches green health; duplicate document detection job initiated
- **10:18** - Duplicate document cleanup job completes; 1,247 duplicate entries removed

## Impact

- **Duration**: 30 minutes (03:42 - 04:12 UTC)
- **Query failures**: Zero — queries served throughout, but with degraded relevance (duplicate results)
- **Duplicate documents**: 1,247 documents written twice during the split window
- **Data loss**: None — all documents written during split were preserved and deduplicated
- **SLA impact**: Availability technically maintained (no 5xx errors), but result quality SLO violated

## Root Cause Analysis

1. **Minimum master nodes setting**: The cluster `discovery.zen.minimum_master_nodes` was set to 2 (correct for 3 nodes), but the network partition isolated one node which then formed a partition with a different quorum, allowing two separate clusters to briefly coexist. This is the classic Elasticsearch split-brain failure mode when network partitions isolate nodes in different AZs.

2. **Insufficient AZ-awareness in shard routing**: The replica shard for `es-data-3`'s primary shards was on `es-data-1`, both in different AZs. A network event isolating them caused the shard routing to diverge.

## Resolution

1. Waited for AWS network partition to resolve naturally (8 minutes)
2. Verified cluster re-formed under a single elected master
3. Initiated duplicate document detection script against the affected index segment
4. Ran cleanup job to remove duplicates (identified by `_id` and `_version` conflict)

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Upgrade to Elasticsearch 8.x cluster coordination (Raft-based, replaces zen discovery) | Search Engineering | P1 | 2025-03-15 | Completed |
| Add `cluster.routing.allocation.awareness.attributes: az` to prevent same-AZ replica co-location | Search Engineering | P1 | 2025-03-01 | Completed |
| Implement post-write duplicate detection in Index Writer for split-brain recovery | Search Engineering | P2 | 2025-03-22 | In Progress |
| Add `search_cluster_split_brain_detected` alert based on multiple-master log pattern | SRE | P2 | 2025-03-08 | Completed |

## Lessons Learned

- **What went well**: Queries continued to serve during the split — zero query failures. Automated alerting detected the degraded state within 2 minutes.
- **What went poorly**: The duplicate document cleanup took 6 hours because no automated deduplication tooling existed. Degraded result quality persisted for 6 hours after the cluster recovered.
- **What was lucky**: The split lasted only 20 minutes. A longer partition could have resulted in far more diverged state and a more complex recovery.
