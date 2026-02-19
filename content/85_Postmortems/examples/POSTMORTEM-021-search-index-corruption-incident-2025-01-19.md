---
id: POSTMORTEM-021
type: postmortem
title: Search Index Corruption Incident 2025-01-19
status: draft
owner: On-Call Engineer
created: '2024-01-06T04:47:03.490Z'
updated: '2025-08-11T10:39:07.989Z'
tags:
  - postmortem
  - search-platform
summary: Search Index Corruption Incident 2025-01-19
incident_number: INC-452
severity: SEV-3
incident_date: '2024-08-13'
detection_time: '2025-02-03T02:49:40.378Z'
resolution_time: '2025-01-09T20:59:55.407Z'
total_duration: ~30 minutes
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-046
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On January 19, 2025, a partial corruption of the primary search index caused degraded and incorrect search results for approximately 30 minutes across all tenants. The corruption was triggered by an interrupted index rebuild job — a scheduled reindex process lost its network connection to the Elasticsearch cluster mid-write, leaving a subset of index shards in an inconsistent state. Queries targeting the affected shards returned stale or malformed document records, causing search result quality to drop sharply.

The incident was detected via automated p95 query-relevance score monitoring at 09:14 UTC. The Search Platform team isolated the corrupted shards, restored them from the previous night's snapshot, and confirmed full index integrity by 09:44 UTC. No documents were permanently lost; the snapshot lag introduced a maximum of six hours of indexing staleness for affected records, which was fully recovered by the catch-up reindex completed at 11:30 UTC.

## Timeline

- **08:47** - Scheduled nightly full reindex job begins on the search-indexer-prod-1 worker node
- **09:02** - Network connectivity between search-indexer-prod-1 and the Elasticsearch primary cluster degrades; bulk write requests begin timing out
- **09:07** - Reindex job retries exhausted; job exits with partial-write error. Index coordinator marks job as failed but does not roll back written shards.
- **09:11** - First customer support tickets arrive reporting irrelevant or missing search results
- **09:14** - `search_relevance_score_p95_low` alert fires; on-call engineer acknowledges
- **09:18** - On-call checks recent deploys — none in past 12 hours. Elasticsearch cluster health shows yellow status on three shards.
- **09:22** - On-call escalates to Search Platform tech lead per [[SOP-046|incident escalation SOP]]
- **09:27** - Tech lead identifies shards 4, 7, and 11 as corrupted via `_cat/shards` API; isolates them from query routing
- **09:31** - Snapshot restore initiated for the three affected shards from the 03:00 UTC snapshot
- **09:40** - Shard restore completes; query routing re-enabled for restored shards
- **09:44** - Search relevance scores return to baseline; incident declared resolved pending monitoring

## Impact

- **Duration**: 30 minutes of degraded search results (09:14 - 09:44 UTC)
- **Users affected**: All tenants relying on full-text search; estimated 2,400 active user sessions during the window
- **Search quality**: p95 relevance score dropped from 0.84 to 0.41 for queries hitting corrupted shards; approximately 18% of all search queries were affected
- **Data staleness**: Records indexed after 03:00 UTC on January 19 were absent from results until catch-up reindex completed at 11:30 UTC (up to 6-hour lag)
- **SLA impact**: Search availability remained above 99.9% threshold; relevance SLA (p95 >= 0.75) was breached for the 30-minute window
- **Customer communications**: Status page updated at 09:20 UTC; no direct customer notifications required given short duration

## Root Cause Analysis

1. **Missing transactional rollback on partial index writes**: The index rebuild job writes shard data in bulk batches without a rollback mechanism. When the job is interrupted mid-run, successfully written batches are committed to the index while subsequent batches are absent. The index coordinator had no logic to detect or revert a partial-write state, leaving corrupted shards in the live query path.

2. **Network instability on the indexer worker node**: The search-indexer-prod-1 node experienced a transient NIC driver issue that caused intermittent packet loss to the Elasticsearch cluster for approximately five minutes starting at 09:02. This was the proximate trigger. The underlying driver bug was confirmed by the infrastructure team and the node was patched; however, the absence of defensive rollback logic in the indexer meant a recoverable network event escalated into index corruption.

3. **Insufficient shard health alerting before query exposure**: Elasticsearch reported yellow shard status at 09:07 when the job failed, but no alert was configured to fire on shard health degradation. The corrupted shards continued serving queries for seven minutes before the relevance-score alert fired, widening the impact window.

## Resolution

1. Identified the three corrupted shards (4, 7, 11) using the `_cat/shards` API and confirmed data inconsistency via document count mismatch against the index metadata log.
2. Removed corrupted shards from the active query routing table to stop serving degraded results to users.
3. Restored shards 4, 7, and 11 from the verified 03:00 UTC Elasticsearch snapshot using the `_snapshot` restore API.
4. Re-enabled query routing for the restored shards after confirming document counts and a spot-check of result relevance scores.
5. Triggered a targeted catch-up reindex for all documents modified between 03:00 UTC and 09:07 UTC to eliminate snapshot-lag staleness; completed at 11:30 UTC.

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Implement atomic shard rollback in the index rebuild job to revert partial writes on job failure | Search Platform | P1 | 2025-02-02 | In Progress |
| Add `search_shard_health_degraded` alert firing on any shard entering yellow or red state | SRE | P1 | 2025-01-26 | Completed |
| Patch NIC driver on search-indexer-prod-1 and audit all indexer nodes for the same driver version | Infrastructure | P1 | 2025-01-21 | Completed |
| Reduce snapshot interval from 6 hours to 1 hour to limit staleness window on restore | Search Platform | P2 | 2025-02-09 | Pending |
| Update [[SOP-046]] with shard isolation and snapshot restore steps as a named diagnosis path | On-Call | P2 | 2025-02-02 | Pending |

## Lessons Learned

- **What went well**: The snapshot-based restore procedure worked cleanly and shard recovery completed ahead of the estimated 20-minute window. The tech lead's familiarity with the `_cat/shards` API accelerated root cause identification significantly.
- **What went poorly**: No alert existed for Elasticsearch shard health degradation, so corrupted shards served live traffic for seven minutes before the relevance-score alert fired. The runbook had no documented path for index corruption, requiring the tech lead to improvise the shard isolation and restore steps under pressure.
- **What was lucky**: The corruption affected only three of twenty-four shards, limiting the query blast radius to ~18% of traffic. Had the network outage begun earlier in the reindex run, more shards would have been in a partial-write state.
- **What went poorly**: The catch-up reindex required manual triggering and monitoring; there was no automated mechanism to detect snapshot-lag after a restore and schedule a reconciliation job.
- **Architecture improvement**: The index rebuild job should treat the Elasticsearch cluster as a transactional target — either all shard writes succeed or none are committed to the live query path. Blue-green index aliasing would provide this guarantee without requiring rollback logic.
