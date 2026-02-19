---
id: POSTMORTEM-025
type: postmortem
title: Autocomplete Service Failure 2025-03-15
status: approved
owner: Incident Commander
created: '2024-02-06T11:19:19.682Z'
updated: '2026-02-27T20:33:34.584Z'
tags:
  - postmortem
  - search-platform
summary: Autocomplete Service Failure 2025-03-15
incident_number: INC-456
severity: SEV-1
incident_date: '2025-01-24'
detection_time: '2026-07-14T15:46:40.654Z'
resolution_time: '2025-08-03T04:10:02.492Z'
total_duration: ~2 hours
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

On March 15, 2025, the Search Autocomplete Service was unavailable for approximately 2 hours due to a DynamoDB hot-key partition issue. A viral search trend caused millions of users to search for nearly identical query prefixes within a short window, which concentrated DynamoDB read requests onto a single partition key. The partition became throttled, causing Lambda functions to time out and return 503 errors to clients.

During the 2-hour outage window, all typeahead suggestions were unavailable. Users could still type full queries and search, but the autocomplete dropdown did not appear. The search service itself was unaffected.

## Timeline

- **13:55** - A social media post goes viral, causing a 12x spike in searches for a specific prefix ("mid-year sale")
- **13:57** - DynamoDB `search-suggestions` table begins throttling reads on the partition holding "mid*" prefix keys
- **14:02** - Autocomplete Lambda functions begin timing out on DynamoDB GetItem calls; 503 errors begin
- **14:05** - `autocomplete_error_rate_high` alert fires; on-call engineer acknowledges
- **14:08** - On-call identifies DynamoDB throttling in CloudWatch metrics
- **14:12** - On-call attempts to increase DynamoDB provisioned read capacity; discovers table is in on-demand mode (no manual scaling needed)
- **14:18** - On-call escalates to tech lead; hot-key pattern confirmed in DynamoDB CloudWatch metrics
- **14:25** - Decision made to deploy emergency hot-key workaround: distribute prefix keys across 16 shards using suffix hash
- **15:20** - Hot-key sharding deployed to staging; validated
- **15:55** - Hot-key sharding deployed to production; throttling subsides
- **16:02** - Autocomplete error rate returns to baseline; incident resolved

## Impact

- **Duration**: 2 hours (14:02 - 16:02 UTC)
- **Users affected**: All users who used the search box typeahead during the window
- **Search impact**: Full search queries worked; only autocomplete suggestions were unavailable
- **Revenue impact**: Estimated 8% reduction in search engagement during the window (lower query rate without autocomplete guidance)
- **SLA impact**: Autocomplete availability dropped to 98.6% for the day (below 99.99% monthly target)

## Root Cause Analysis

1. **Non-uniform prefix distribution in DynamoDB**: The suggestion table used the query prefix as the partition key directly. This creates a hot-key vulnerability: if many users query the same prefix, all reads land on the same DynamoDB partition, exhausting its read capacity unit allocation.

2. **No circuit breaker for autocomplete timeouts**: The autocomplete Lambda had no fallback when DynamoDB calls timed out. It should have returned an empty suggestion list (silent failure) rather than a 503 error, to preserve the search experience.

## Resolution

1. Deployed hot-key sharding: prefix keys are distributed across 16 logical shards using `prefix + ':' + (hash(prefix) % 16)` as the partition key, with scatter-gather on reads
2. Added empty-result fallback in Lambda handler for DynamoDB timeout errors
3. Monitored autocomplete error rate until it returned to baseline

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Deploy hot-key sharding for DynamoDB suggestion table | Search Engineering | P1 | 2025-03-15 | Completed |
| Add silent-failure fallback for DynamoDB timeout in autocomplete Lambda | Search Engineering | P1 | 2025-03-15 | Completed |
| Add DynamoDB partition-level throttling alert | SRE | P1 | 2025-03-22 | Completed |
| Evaluate DAX caching layer to absorb hot-key traffic | Search Engineering | P2 | 2025-04-15 | In Progress |

## Lessons Learned

- **What went well**: Root cause identified within 13 minutes. Emergency fix was deployable within 90 minutes.
- **What went poorly**: The autocomplete service returned 503 instead of silently degrading. Users saw an error state for a non-critical feature.
- **What was lucky**: The viral search trend was temporary; traffic subsided on its own after ~2 hours, which aligned with the fix deployment window.
