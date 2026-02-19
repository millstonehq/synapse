---
id: SOP-023
type: sop
title: Handle Oversold Item SOP
status: review
owner: DevOps Lead
created: '2025-01-20T17:59:41.123Z'
updated: '2026-08-24T16:19:46.424Z'
tags:
  - sop
  - inventory-management
summary: Handle Oversold Item SOP
related_process: PROCESS-017
related_systems:
  - SYSTEM-015
example: true
---

## Preconditions

- An oversell condition has been identified: one or more orders have been accepted for a SKU where the confirmed available quantity is zero or negative
- The affected SKU and warehouse are known and documented in the incident ticket
- The order management team has been notified and has placed a hold on new orders for the affected SKU pending resolution
- On-call engineer for inventory is available to assist with any system-level interventions

## Materials/Access

- Read access to the inventory API to query current stock levels and recent movement history
- Access to the order management system to view and update affected orders
- Access to the Inventory Admin Portal with stock-adjustment permissions
- Incident ticket number for traceability
- Access to #inventory-incidents Slack channel

## Procedure

1. Query the inventory API for the affected SKU and warehouse: confirm current `available_qty`, `reserved_qty`, and `on_hand_qty`, and note each value.
2. Pull the stock movement log for the SKU for the past 24 hours. Identify the sequence of events that led to the negative available quantity (look for race condition in reservation vs. adjustment, sync lag, or a missing deduction event).
3. Determine the actual physical quantity available by contacting the Warehouse Operations Lead for a manual count or checking the latest cycle count result.
4. Post findings in #inventory-incidents: SKU, affected orders, physical quantity confirmed, and root cause hypothesis.
5. For each affected order, work with the order management team to triage: if physical stock exists and can fulfill, reserve that stock explicitly; if no stock exists, identify which orders cannot be fulfilled.
6. Apply a manual inventory adjustment in the admin portal to correct `on_hand_qty` to the verified physical count; reference the incident ticket number in the adjustment reason field.
7. Coordinate with customer support on the communication plan for any orders that cannot be fulfilled (cancellation, backorder, substitute).
8. Remove the order hold for the SKU once the quantity is corrected and the fulfillment plan is confirmed.
9. File a post-incident note in the incident ticket documenting root cause and the quantity correction applied.

## Validation

- Inventory API returns a non-negative `available_qty` for the affected SKU after the adjustment
- All affected orders are in a confirmed state (either fulfilled, backordered with customer notification, or cancelled)
- The stock movement log shows the manual adjustment with the incident ticket reference
- No new oversell alerts have fired for the SKU within 30 minutes of resolution
- Warehouse Operations Lead has confirmed the corrected physical quantity

## Rollback

1. If the manual adjustment was applied in error (wrong SKU or wrong quantity), do not apply a second adjustment immediately.
2. Query the movement log to confirm the erroneous adjustment entry and its `movement_id`.
3. Contact the Inventory Platform Engineer to apply a corrective adjustment equal and opposite to the error, referencing both the incident ticket and the erroneous `movement_id`.
4. Verify the corrected quantity in the inventory API matches the known physical count.
5. Update the incident ticket with details of the correction and notify the order management team of the final confirmed quantity.
