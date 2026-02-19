---
id: SOP-021
type: sop
title: Reconcile Inventory Discrepancy SOP
status: approved
owner: SRE Lead
created: '2025-04-09T02:00:25.656Z'
updated: '2026-08-17T18:07:24.470Z'
tags:
  - sop
  - inventory-management
summary: Reconcile Inventory Discrepancy SOP
related_process: PROCESS-017
related_systems:
  - SYSTEM-011
example: true
---

## Preconditions

- A discrepancy has been identified between the physical stock count and the inventory system record in [[SYSTEM-011|Inventory Management System]]
- The affected SKU(s) and warehouse location(s) are known and documented
- A recount of the affected items has been completed by a second staff member to confirm the discrepancy is real
- No active receiving or picking operations are in progress for the affected SKU(s)

## Materials/Access

- Inventory Management System access with the Inventory Adjustment role
- The completed physical recount sheet (signed by both counters)
- The discrepancy report generated from [[SYSTEM-011|Inventory Management System]] showing the system-on-hand quantity
- Access to the receiving and shipment logs for the affected SKU(s) covering the relevant time window

## Procedure

1. Open [[SYSTEM-011|Inventory Management System]] and navigate to the Inventory Adjustment module for the affected SKU and location.
2. Record the system-on-hand quantity and the physically counted quantity on the discrepancy resolution form before making any changes.
3. Review the receiving log for the past 30 days for the SKU: check for any receipts that were scanned but not fully processed, or any returns that were restocked without a system update.
4. Review the shipment and pick log for the same period: identify any shipments that were completed in the physical warehouse but not confirmed in the system, or any cancelled picks where items were returned to shelf without reversing the reservation.
5. If an unprocessed transaction is found in steps 3 or 4, complete that transaction in the system (confirm receipt, confirm shipment, or reverse the reservation) and recheck the system-on-hand quantity.
6. If no unprocessed transaction explains the discrepancy, create a manual inventory adjustment in the system for the difference, selecting the reason code that best describes the cause (e.g., "Damage/Write-off", "Cycle Count Correction", "Receiving Error", "Unknown Shrinkage").
7. Attach the signed physical recount sheet and the discrepancy resolution form as supporting documents to the adjustment record.
8. Notify the Inventory Manager via the standard channel, providing the SKU, location, adjustment quantity, reason code, and adjustment record ID.

## Validation

- The system-on-hand quantity for the affected SKU and location now matches the signed physical recount sheet.
- The adjustment record is saved in [[SYSTEM-011|Inventory Management System]] with a valid reason code and attached supporting documents.
- No open reservations or pending transactions remain for the affected SKU that would cause the quantity to drift again immediately.
- The Inventory Manager has acknowledged the notification and the adjustment record ID.

## Rollback

1. If the adjustment was entered with an incorrect quantity or wrong SKU, open the adjustment record in [[SYSTEM-011|Inventory Management System]] and create a reversing adjustment for the same quantity with reason code "Adjustment Error — Reversal".
2. Attach a note to both the original and reversing adjustment records explaining the error and referencing the other record's ID.
3. Re-enter the correct adjustment using the accurate quantity, correct SKU, and correct location, attaching the original recount sheet.
4. Notify the Inventory Manager of the correction, providing both adjustment record IDs (original, reversal, and corrected) and a brief explanation of the error.
