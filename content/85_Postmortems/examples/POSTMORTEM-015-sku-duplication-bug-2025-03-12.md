---
id: POSTMORTEM-015
type: postmortem
title: SKU Duplication Bug 2025-03-12
status: approved
owner: On-Call Engineer
created: '2025-10-01T12:17:15.847Z'
updated: '2026-07-31T00:21:18.672Z'
tags:
  - postmortem
  - inventory-management
summary: SKU Duplication Bug 2025-03-12
incident_number: INC-266
severity: SEV-3
incident_date: '2025-01-09'
detection_time: '2024-08-20T04:32:55.891Z'
resolution_time: '2025-02-17T23:57:24.896Z'
total_duration: ~2 hours
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-026
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On March 12, 2025, a race condition in the SKU Registry Service's bulk import path allowed 23 duplicate SKU records to be created when two concurrent bulk import jobs processed overlapping product catalogs from the same supplier. Each job performed a read-then-insert pattern without a distributed lock, so both jobs independently determined that a SKU did not exist and both proceeded to insert it.

The issue was detected 118 minutes after the imports completed when downstream services returned duplicate SKU matches for 23 products, causing order routing ambiguity. Deduplication was performed using a custom script that retained the older record and merged any stock movements associated with the duplicate into the canonical record.

## Timeline

- **10:15** - Supplier catalog import Job A starts (4,200 SKUs from Supplier X)
- **10:15** - Supplier catalog import Job B starts (3,800 SKUs from Supplier X, partial overlap with Job A)
- **10:17** - Both jobs perform existence checks for the 23 overlapping SKUs; both find no existing record
- **10:18** - Both jobs insert records for the 23 overlapping SKUs; duplicate inserts succeed (no unique constraint on supplier_id + supplier_sku_code at this time)
- **10:45** - Both import jobs complete successfully; no errors reported
- **13:03** - Order routing service returns ambiguous SKU match for product lookup; on-call engineer alerted by order service team
- **13:08** - On-call investigates; discovers 23 SKUs with duplicate records in the registry
- **13:15** - Root cause identified: concurrent bulk imports without concurrency control
- **13:25** - Deduplication script run in staging environment and validated
- **13:47** - Deduplication script run in production; 23 duplicate records merged
- **14:05** - Order routing confirmed returning single match for all 23 products; incident resolved

## Impact

- **Duration**: 118 minutes from duplicate creation to detection; 20 minutes for resolution
- **SKUs affected**: 23 duplicate records across Supplier X catalog
- **Downstream impact**: Order routing service returned ambiguous results for 23 SKUs during the 118-minute window
- **Orders affected**: 4 orders held in routing pending SKU resolution; all released within 25 minutes of deduplication
- **Revenue impact**: 4 orders delayed by ~30 minutes; no cancellations

## Root Cause Analysis

1. **No unique constraint on supplier SKU identity**: The SKU registry table had a primary key on the internal `sku_id` but no unique constraint on `(supplier_id, supplier_sku_code)`. This allowed two concurrent inserts of the same supplier SKU to succeed independently.

2. **No distributed lock on bulk import by supplier**: The bulk import jobs ran concurrently without coordination. For the same supplier's catalog, concurrent jobs are inherently at risk of processing overlapping SKU sets. There was no per-supplier import lock or serialization mechanism.

## Resolution

1. Ran deduplication script to identify, validate, and merge duplicate SKU records
2. Deployed hotfix adding `UNIQUE (supplier_id, supplier_sku_code)` constraint
3. Added per-supplier distributed lock (Redis SETNX with 30-minute TTL) to bulk import scheduler
4. Reprocessed the 4 held orders after deduplication

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add UNIQUE constraint on (supplier_id, supplier_sku_code) to sku table | DBA | P1 | 2025-03-13 | Completed |
| Add per-supplier distributed lock to bulk import scheduler | Inventory Engineering | P1 | 2025-03-17 | Completed |
| Add integration test for concurrent bulk import with overlapping SKUs | QA | P2 | 2025-03-24 | Completed |
| Audit all other write paths in SKU registry for missing uniqueness guards | Principal Engineer | P3 | 2025-04-04 | In progress |

## Lessons Learned

- **What went well**: The deduplication script was written and validated quickly; production correction took only 20 minutes once the approach was confirmed.
- **What went poorly**: A unique constraint on supplier SKU identity is a fundamental data integrity requirement that should have been in the original schema. The gap was not caught in code review.
- **What was lucky**: Only 23 SKUs were affected because the overlapping region of the two import catalogs was small. A full catalog re-import would have produced hundreds of duplicates.
