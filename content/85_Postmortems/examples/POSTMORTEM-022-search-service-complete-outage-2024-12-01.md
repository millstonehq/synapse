---
id: POSTMORTEM-022
type: postmortem
title: Search Service Complete Outage 2024-12-01
status: draft
owner: Incident Commander
created: '2024-01-09T18:50:25.549Z'
updated: '2025-07-24T14:04:57.363Z'
tags:
  - postmortem
  - search-platform
summary: Search Service Complete Outage 2024-12-01
incident_number: INC-453
severity: SEV-2
incident_date: '2024-02-17'
detection_time: '2024-08-29T02:02:25.081Z'
resolution_time: '2026-03-18T14:20:39.243Z'
total_duration: ~30 minutes
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-049
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On December 1, 2024, the Search Platform experienced a complete query outage lasting approximately 30 minutes. The Elasticsearch cluster entered a red health state after all three data nodes attempted a simultaneous JVM garbage collection pause triggered by a heap pressure spike, leaving no data nodes available to serve shards. All search queries returned 503 errors during the outage window.

The incident was detected by automated alerting at 09:14 UTC and resolved at 09:44 UTC after the Elasticsearch cluster recovered and shard assignments stabilized. Approximately 350,000 search queries failed during the window. No data was lost and no index corruption occurred.

## Timeline

- **09:08** - A bulk reindex job started that was inadvertently scheduled on the production cluster rather than the staging cluster
- **09:10** - Elasticsearch JVM heap utilization on all three data nodes climbs above 85% as the reindex job triggers GC pressure
- **09:12** - All three data nodes enter a Stop-The-World GC pause simultaneously; cluster loses quorum
- **09:14** - `search_cluster_health_red` alert fires; on-call engineer acknowledges
- **09:16** - Search Query Processing Service Lambda functions begin returning 503; error rate alert fires
- **09:18** - On-call checks recent deploys in #deployments; no application deploys. Checks Elasticsearch cluster health API — cluster is red, no master elected
- **09:22** - On-call pages the Search tech lead per escalation runbook
- **09:25** - Tech lead identifies the runaway reindex job via Elasticsearch task API; cancels the job
- **09:28** - GC pressure subsides; Elasticsearch nodes begin recovering
- **09:36** - Cluster transitions from red to yellow as shard reallocation begins
- **09:44** - Cluster reaches green health; all shards assigned; query service error rate returns to baseline
- **09:44** - Incident closed after 2-minute stable observation window

## Impact

- **Duration**: 30 minutes (09:14 - 09:44 UTC)
- **Queries affected**: ~350,000 search queries returned 503 errors
- **Users affected**: All users who attempted to search during the window
- **Revenue impact**: Estimated $8,400 in lost product discovery (search-assisted purchases during window)
- **SLA impact**: Monthly availability dropped to 99.93% (below 99.99% target)
- **Customer communications**: Status page updated at 09:20; cleared at 09:50

## Root Cause Analysis

1. **Missing environment guard on reindex job**: The bulk reindex job script lacked a guard to prevent execution against the production cluster. A developer ran the job locally intending to target staging but had production AWS credentials active in the terminal session.

2. **Insufficient GC headroom on data nodes**: All three data nodes were configured with identical JVM heap settings (15GB). Under sudden GC pressure from a bulk indexing workload, all three entered GC pause simultaneously, leaving no node available to serve shards or maintain quorum.

## Resolution

1. Cancelled the runaway reindex job via Elasticsearch `/_tasks/{task_id}/_cancel` API
2. Waited for GC pressure to subside across all three nodes (~3 minutes)
3. Monitored cluster health API until green status confirmed
4. Verified query service error rate returned to baseline

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add `--cluster` flag to reindex script with explicit confirmation prompt for production | Search Engineering | P1 | 2024-12-08 | Completed |
| Configure Elasticsearch JVM heap monitoring alert at 80% utilization | SRE | P1 | 2024-12-08 | Completed |
| Stagger JVM heap settings across data nodes to reduce simultaneous GC risk | Search Engineering | P2 | 2024-12-15 | Completed |
| Implement reindex job guardrail: require `CONFIRM_PRODUCTION=true` env var | Search Engineering | P2 | 2024-12-15 | Completed |
| Add `search_cluster_health_yellow` alert to detect degraded state before it reaches red | SRE | P3 | 2024-12-22 | In Progress |

## Lessons Learned

- **What went well**: Automated alerting detected the issue within 2 minutes of cluster entering red state. The tech lead identified the root cause (reindex job) within 3 minutes of joining the incident.
- **What went poorly**: The reindex script had no safeguards against running on production. The on-call engineer spent 8 minutes investigating deploys before escalating; the runbook should explicitly direct checking the Elasticsearch task API for runaway jobs.
- **What was lucky**: The GC pause was transient. If the reindex job had continued after the cluster recovered, the outage would have recurred.
