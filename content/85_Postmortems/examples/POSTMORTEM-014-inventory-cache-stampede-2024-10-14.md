---
id: POSTMORTEM-014
type: postmortem
title: Inventory Cache Stampede 2024-10-14
status: approved
owner: Incident Commander
created: '2025-04-23T09:16:34.688Z'
updated: '2025-09-05T15:34:26.017Z'
tags:
  - postmortem
  - inventory-management
summary: Inventory Cache Stampede 2024-10-14
incident_number: INC-265
severity: SEV-3
incident_date: '2025-10-20'
detection_time: '2025-09-19T11:34:05.621Z'
resolution_time: '2025-01-26T09:22:30.194Z'
total_duration: ~2 hours
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-025
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On October 14, 2024, a planned Redis cluster failover for maintenance triggered a cache stampede on the Stock Level Calculator's query cache. When the new Redis primary came online with an empty cache, approximately 4,200 concurrent requests for stock level data all simultaneously hit the PostgreSQL database, causing connection pool exhaustion and a 28-minute degradation in stock level query performance.

The incident was detected by automated alerting when PostgreSQL active connection count exceeded 90% of the pool maximum. Query P95 spiked from 88ms to 8.4 seconds during the peak stampede window. Resolution required rate-limiting inbound query traffic and waiting for the cache to warm up organically.

## Timeline

- **14:00** - Planned Redis maintenance failover begins; primary node replaced
- **14:02** - New primary comes online with empty cache; all keys expired
- **14:03** - First batch of cache misses; requests fall through to PostgreSQL
- **14:04** - Connection pool utilization reaches 60%; query latency increases to 1.2s P95
- **14:06** - `stock_level_query_p95_high` alert fires; on-call acknowledges
- **14:08** - Connection pool utilization reaches 90%; `stock_level_db_pool_high` alert fires
- **14:10** - On-call identifies cache miss storm; begins rate-limiting inbound traffic via API gateway
- **14:18** - Traffic rate limiting in effect; PostgreSQL connection pool stabilizes at 75%
- **14:25** - Cache warm-up progressing; hit rate recovering to 40%
- **14:52** - Cache hit rate exceeds 90%; query P95 returns to baseline (81ms)
- **15:05** - Rate limiting removed; full traffic restored
- **16:03** - Incident formally closed after 1-hour stable monitoring window

## Impact

- **Duration**: 28 minutes of significant degradation (query P95 > 1s); 62 minutes to full recovery
- **Queries affected**: All stock level queries during the cache miss window
- **Peak query P95**: 8.4 seconds (vs 88ms baseline)
- **Connection pool peak**: 94% utilization (94 of 100 connections active)
- **Downstream impact**: Real-time stock dashboard showed degraded response times; order service experienced timeout warnings but no failures due to its 10-second timeout configuration
- **Revenue impact**: No orders blocked; downstream services degraded but functional

## Root Cause Analysis

1. **No cache warm-up before failover**: The Redis failover procedure did not include a cache warm-up step. The new primary started cold, guaranteeing a 100% miss rate during the high-traffic period immediately after failover. The failover was scheduled during business hours rather than an off-peak window.

2. **No thundering herd protection**: The query cache had no probabilistic early expiration or lock-based cache fill mechanism. When a key expired (or was absent), all concurrent requests for the same key simultaneously queried the database rather than one request fetching while others waited.

## Resolution

1. Applied API gateway rate limiting to reduce inbound stock level query rate to 30% of normal
2. Waited for organic cache warm-up to recover hit rate above 90%
3. Removed rate limiting once database load normalized
4. Documented revised maintenance procedure requiring off-peak failover windows

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Implement probabilistic early expiration (PER) to prevent thundering herd on cache expiry | Inventory Engineering | P1 | 2024-10-21 | Completed |
| Restrict Redis maintenance failovers to off-peak hours (02:00-05:00 UTC) | SRE | P1 | 2024-10-18 | Completed |
| Add pre-failover cache warm-up script to Redis maintenance runbook | SRE | P2 | 2024-10-25 | Completed |
| Add circuit breaker on stock level query path to shed load before pool exhaustion | Inventory Engineering | P2 | 2024-11-04 | In progress |

## Lessons Learned

- **What went well**: On-call detected the connection pool spike quickly and correctly identified the root cause (cache miss storm) within 4 minutes. Rate limiting was an effective immediate mitigation.
- **What went poorly**: The maintenance failover was scheduled during business hours without accounting for the cache cold-start effect. The lack of thundering herd protection was a known gap that had not been prioritized.
- **What was lucky**: The order service's 10-second timeout configuration absorbed the worst of the degradation without surfacing errors to customers.
