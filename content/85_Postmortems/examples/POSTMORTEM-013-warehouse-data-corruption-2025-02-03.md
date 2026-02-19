---
id: POSTMORTEM-013
type: postmortem
title: Warehouse Data Corruption 2025-02-03
status: proposed
owner: On-Call Engineer
created: '2024-09-22T21:14:27.057Z'
updated: '2025-05-29T18:08:49.381Z'
tags:
  - postmortem
  - inventory-management
summary: Warehouse Data Corruption 2025-02-03
incident_number: INC-264
severity: SEV-4
incident_date: '2024-05-12'
detection_time: '2024-09-04T23:33:08.477Z'
resolution_time: '2024-08-25T07:47:31.241Z'
total_duration: ~1 hour
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-024
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On February 3, 2025, a malformed EDI 846 transmission from Warehouse G caused incorrect stock quantity deltas to be applied to 147 SKUs. The malformation was a missing segment terminator in a batch of 312 EDI transactions, which caused the parser to mis-read unit-of-measure fields and apply case-quantity deltas (24x) instead of each-quantity deltas for a subset of records. Affected stock levels were overstated by factors of 12-24x.

The corruption was detected 6 hours later by the nightly automated reconciliation job, which flagged 147 SKUs with >10% variance against Warehouse G's reported physical counts. Correct stock levels were restored by replaying the affected event log segment after the EDI parser was patched.

## Timeline

- **02:15** - Warehouse G transmits malformed EDI 846 batch (missing segment terminator in transaction 184 of 312)
- **02:17** - EDI adapter parses batch; mis-parses unit_of_measure for transactions 184-312 due to parser state error from missing terminator
- **02:18** - 147 stock increase events with inflated deltas (24x) published to event bus and applied to stock projections
- **02:20** - Sync completes without error; parser does not raise a schema validation error because numeric fields are within valid range
- **08:14** - Nightly reconciliation job runs; 147 SKUs flagged with >10% variance against Warehouse G physical count
- **08:19** - `inventory_reconciliation_high_variance` alert fires; on-call engineer acknowledges
- **08:35** - On-call reviews reconciliation output; identifies all 147 affected SKUs are from Warehouse G's 02:15 transmission
- **08:47** - Root cause confirmed: malformed EDI batch; on-call escalates to Inventory Engineering
- **09:10** - EDI parser bug identified and patched in development environment
- **09:45** - Corrected parser deployed; affected event log segment re-processed
- **10:12** - All 147 stock levels corrected; reconciliation re-run confirms zero variance

## Impact

- **Duration**: ~8 hours from corruption to full correction
- **SKUs affected**: 147 (all at Warehouse G)
- **Stock overstatement**: 12-24x actual quantities during the window
- **Orders impacted**: 3 orders were confirmed for items that were effectively out-of-stock; all 3 were fulfilled from Warehouse B inventory
- **Revenue impact**: No cancellations; expedited fulfilment from alternate warehouse
- **Detection gap**: 6-hour window between corruption and detection

## Root Cause Analysis

1. **Missing segment terminator not caught by pre-processing validation**: The EDI adapter's pre-processing validation checked for document-level structural integrity (ISA/IEA envelope) but did not validate individual segment terminators within transaction sets. A missing terminator caused the parser to enter an incorrect state, treating the remainder of the batch as a continuation of the prior transaction.

2. **Unit-of-measure field not validated against business rules**: The normalization layer accepted any valid numeric value in the UOM field without cross-referencing the SKU's registered unit of measure. A cross-reference check would have flagged that a retail consumer product's stock event was using CASE as its unit, which is atypical for this category of SKU.

## Resolution

1. Patched EDI parser to validate segment terminators per transaction set boundary
2. Added UOM cross-reference validation in the normalization layer
3. Re-processed affected event log segment with corrected parser
4. Verified all 147 stock levels against Warehouse G physical count

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add per-transaction-set segment terminator validation to EDI parser | Inventory Engineering | P1 | 2025-02-07 | Completed |
| Add UOM cross-reference validation against SKU registry in normalization layer | Inventory Engineering | P1 | 2025-02-07 | Completed |
| Reduce reconciliation frequency for high-risk warehouses from nightly to every 4 hours | SRE | P2 | 2025-02-14 | In progress |
| Add EDI batch rejection and alerting for malformed transmissions | Inventory Engineering | P2 | 2025-02-14 | Pending |

## Lessons Learned

- **What went well**: Event sourcing architecture enabled full recovery by replaying corrected events. No data was permanently lost.
- **What went poorly**: The 6-hour detection gap is too long for a corruption of this magnitude. Per-warehouse reconciliation frequency needs to be shorter for high-volume partners.
- **What was lucky**: The corruption was an overstatement (excess stock) rather than an understatement. Orders continued to be fulfilled; an understatement of the same magnitude would have triggered stockout alerts and potentially blocked orders.
