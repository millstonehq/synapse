---
id: SOP-028
type: sop
title: Archive Discontinued SKU SOP
status: approved
owner: DevOps Lead
created: '2025-12-09T18:04:36.508Z'
updated: '2025-09-04T09:18:50.016Z'
tags:
  - sop
  - inventory-management
summary: Archive Discontinued SKU SOP
related_process: PROCESS-014
related_systems:
  - SYSTEM-015
example: true
---

## Preconditions

- The SKU has been in `discontinued` status for a minimum of 90 days
- On-hand quantity for the SKU is confirmed as zero across all warehouses
- No open purchase orders, pending receipts, or unfulfilled order line items reference the SKU
- Archival has been approved by the Inventory Operations Lead and the relevant Product Manager
- The SKU's movement log retention period has been verified against the Warehouse Data Retention Policy

## Materials/Access

- Access to the Inventory Admin Portal with SKU management permissions
- Approved archival request (ticket number from the product team)
- Access to the SKU Registry Service to confirm cross-system status
- Read access to the order management system to verify no open orders reference the SKU

## Procedure

1. Query the inventory API for the SKU status: confirm `status: discontinued`, `on_hand_qty: 0`, and `reserved_qty: 0` across all warehouses.
2. Query the order management system for any open order line items referencing this SKU. If any are found, stop and escalate to the Product Manager and order management team before proceeding.
3. Query the purchasing system for any open purchase orders referencing this SKU. If any are found, stop and obtain cancellation confirmation before proceeding.
4. In the Inventory Admin Portal, navigate to SKU Management, search for the SKU, and open the SKU record.
5. Click "Request Archive" and enter the archival ticket number in the reason field. The system will perform a final pre-archive validation check.
6. If the pre-archive validation passes, confirm the archival action. The SKU status will change to `archived` and it will be suppressed from active API responses.
7. Verify in the SKU Registry Service that the SKU status is reflected as archived in the registry within 5 minutes (sync may have a brief lag).
8. Notify the requester and update the archival ticket as completed.

## Validation

- Inventory API query for the archived SKU returns a 404 on the active SKU endpoint
- SKU Registry Service reflects `status: archived` for the SKU
- Stock movement log for the SKU is still accessible via the audit log endpoint (confirm data has not been deleted)
- No active replenishment signals or threshold alerts reference the archived SKU
- The archival record appears in the SKU change history with the correct approver and timestamp

## Rollback

1. If a SKU is archived in error, open a priority incident ticket referencing the SKU ID and the erroneous archival timestamp.
2. Contact the Inventory Platform Engineer to revert the SKU status from `archived` to `discontinued` via the admin API.
3. Confirm the SKU appears again in the active SKU endpoint before notifying any affected teams.
4. Investigate why the archival pre-conditions were met incorrectly (e.g., an order was placed after the pre-check) and apply process guardrails to prevent recurrence.
5. Update the incident ticket with findings and close once SKU is confirmed operational.
