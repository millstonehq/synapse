---
id: SOP-029
type: sop
title: Inventory Cache Invalidation SOP
status: draft
owner: Release Manager
created: '2024-08-11T21:28:14.432Z'
updated: '2026-04-02T01:59:07.247Z'
tags:
  - sop
  - inventory-management
summary: Inventory Cache Invalidation SOP
related_process: PROCESS-015
related_systems:
  - SYSTEM-014
example: true
---

## Preconditions

- A cache invalidation need has been identified: the inventory cache is serving stale data that does not reflect the current state in the database
- The affected cache scope is known: single SKU, warehouse-level, or full cache
- The Inventory Platform Engineer and on-call engineer are aware of the operation
- Full cache invalidation has been approved by the Engineering Manager due to the risk of temporary cache miss spike and increased database load

## Materials/Access

- Redis CLI or access to the Redis management console for the inventory cache cluster
- Access to the inventory-cache service admin endpoint (internal only, require VPN)
- Access to Grafana: Inventory Cache dashboard showing hit rate, miss rate, and Redis memory
- `kubectl` access to the `inventory` namespace (for cache service pod management if needed)
- Access to #inventory-ops for status updates

## Procedure

1. Confirm the scope of the invalidation needed: single SKU (targeted), warehouse (scoped), or all inventory cache keys (full). Start with the smallest scope that addresses the issue.
2. Open the Grafana Inventory Cache dashboard and record current cache hit rate and Redis memory usage as baseline.
3. For targeted single-SKU invalidation: call the inventory-cache admin endpoint `POST /admin/invalidate?sku_id=[SKU_ID]&warehouse_id=[WAREHOUSE_ID]`. Confirm 200 response.
4. For warehouse-scoped invalidation: call `POST /admin/invalidate?warehouse_id=[WAREHOUSE_ID]`. This invalidates all keys for the warehouse. Monitor cache miss rate in Grafana; expect a temporary spike as keys are repopulated.
5. For full cache invalidation: post in #inventory-ops that a full cache flush is starting. Call `POST /admin/invalidate/all`. Monitor the database connection pool in Grafana — if connections approach 80% utilization, pause and allow the cache to partially repopulate before continuing.
6. Wait for the cache hit rate to recover to within 10% of baseline (typically 2-5 minutes for targeted, 10-20 minutes for full flush).
7. Spot-check 3 SKUs by querying the inventory API and comparing responses to the database directly: confirm cache is now serving correct data.
8. Post confirmation in #inventory-ops: scope of invalidation, duration, and confirmation that hit rate has recovered.

## Validation

- Grafana cache hit rate has recovered to within 10% of pre-invalidation baseline
- Database connection pool utilization has returned to normal range
- The specific SKU(s) or warehouse(s) that prompted the invalidation now return correct quantities from the inventory API
- No new stale data complaints from dependent services within 30 minutes of invalidation completion
- Redis memory usage is stable (no unexpected memory growth following repopulation)

## Rollback

1. Cache invalidation itself cannot be "rolled back" — once cache keys are deleted, they will be repopulated from the database on the next request.
2. If the invalidation caused unexpected database overload, scale the inventory service to add more pods to distribute cache-miss load: `kubectl scale deployment/inventory-api -n inventory --replicas=[N+2]`.
3. If incorrect data was in the database (not the cache), the cache invalidation will cause the bad database data to be served more widely. In this case, halt by re-enabling the cache write-through bypass and escalate to the Inventory Platform Engineer to fix the database data.
4. Once the database data is corrected, perform a targeted invalidation to flush the newly-populated bad cache entries.
5. Reduce replicas back to normal after load subsides.
