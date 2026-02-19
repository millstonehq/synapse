---
id: POSTMORTEM-012
type: postmortem
title: Stock Oversell Incident 2024-11-25
status: approved
owner: Incident Commander
created: '2024-02-26T19:35:27.615Z'
updated: '2025-04-22T00:35:38.725Z'
tags:
  - postmortem
  - inventory-management
summary: Stock Oversell Incident 2024-11-25
incident_number: INC-263
severity: SEV-1
incident_date: '2025-03-05'
detection_time: '2026-09-26T07:17:12.501Z'
resolution_time: '2025-08-25T02:14:39.256Z'
total_duration: ~30 minutes
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-021
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On November 25, 2024, a race condition in the stock reservation system allowed 312 units of a high-demand product (SKU: HDTV-55-4K) to be oversold during a flash sale event. The race occurred because the reservation check and decrement were not performed atomically — two concurrent requests both read the same available quantity (1) and both succeeded, resulting in a negative available stock balance and 1 unfulfillable order.

The incident was detected 22 minutes after the first oversold order was confirmed when operations staff noticed a negative available quantity in the dashboard. 1 customer received a cancellation notice; the remainder were fulfilled from an emergency inter-warehouse transfer.

## Timeline

- **14:00** - Flash sale begins; product HDTV-55-4K goes on sale; 2,400 concurrent shoppers
- **14:00:42** - First oversell event: two concurrent reservation requests both read available_qty=1 and both decrement, resulting in available_qty=-1
- **14:01** - Order confirmation emails sent to both customers
- **14:22** - Operations staff notices negative available_qty in stock dashboard; alerts on-call engineer
- **14:24** - On-call engineer identifies oversold order pair; escalates to Inventory Engineering
- **14:35** - Root cause confirmed: non-atomic read-check-decrement in reservation path
- **14:47** - Emergency inter-warehouse transfer initiated for 50 units from Warehouse B to cover all oversold orders
- **15:18** - All affected orders confirmed fulfillable; one customer contacted with sincere apology and expedited shipping offer
- **15:30** - Incident closed; hotfix design underway

## Impact

- **Duration**: 22 minutes from first oversell to detection; 90 minutes to full resolution
- **SKUs affected**: 1 (HDTV-55-4K)
- **Oversold units**: 1 unit (one duplicate reservation confirmed)
- **Customers affected**: 1 customer received a cancellation; 1 customer received an apology and upgrade
- **Revenue impact**: No revenue loss; affected order was fulfilled via inter-warehouse transfer with expedited shipping at no customer cost
- **Reputation impact**: 1 customer complaint; operations team sent goodwill voucher

## Root Cause Analysis

1. **Non-atomic reservation**: The stock reservation path used a read-then-update pattern: read `available_qty`, check if `available_qty >= requested_qty`, then perform `UPDATE stock SET reserved_qty = reserved_qty + qty`. Under concurrent load, two requests can both read the same `available_qty` before either decrement is committed, bypassing the availability check.

2. **Missing database-level constraint**: There was no `CHECK (available_qty >= 0)` constraint on the stock levels table, nor was the decrement operation using a conditional update (`UPDATE ... WHERE available_qty >= qty`). The application-layer check was the only guard, and it was not race-safe.

## Resolution

1. Deployed hotfix to reservation path using atomic conditional SQL: `UPDATE stock_levels SET reserved_qty = reserved_qty + ? WHERE sku_id = ? AND location_id = ? AND (on_hand_qty - reserved_qty) >= ?`
2. Added database `CHECK` constraint `available_qty >= 0`
3. Processed emergency inter-warehouse transfer to fulfil oversold order
4. Contacted affected customer and issued goodwill compensation

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Deploy atomic reservation SQL with conditional WHERE clause | Inventory Engineering | P1 | 2024-11-26 | Completed |
| Add CHECK constraint available_qty >= 0 to stock_levels table | DBA | P1 | 2024-11-26 | Completed |
| Add integration test for concurrent reservation race condition | QA | P2 | 2024-12-06 | Completed |
| Load test reservation path at 500 concurrent requests | Inventory Engineering | P2 | 2024-12-10 | Completed |
| Review all other inventory write paths for non-atomic patterns | Principal Engineer | P3 | 2024-12-20 | In progress |

## Lessons Learned

- **What went well**: Operations team detected the negative stock balance quickly using the dashboard. Emergency inter-warehouse transfer covered the oversold order with minimal customer impact.
- **What went poorly**: The non-atomic reservation pattern was a known anti-pattern that slipped through code review. The absence of a database-level constraint allowed negative stock to persist rather than failing fast.
- **What was lucky**: Only 1 unit was oversold during a period of thousands of concurrent requests. With slightly different timing, the impact could have been much larger.
