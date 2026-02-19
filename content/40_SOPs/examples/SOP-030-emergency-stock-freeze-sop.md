---
id: SOP-030
type: sop
title: Emergency Stock Freeze SOP
status: draft
owner: SRE Lead
created: '2024-11-05T04:16:28.168Z'
updated: '2026-01-25T12:25:19.214Z'
tags:
  - sop
  - inventory-management
summary: Emergency Stock Freeze SOP
related_process: PROCESS-018
related_systems:
  - SYSTEM-012
example: true
---

## Preconditions

- An emergency condition has been identified that requires halting all inventory mutations: examples include a data corruption event, a runaway automated process writing incorrect quantities, a regulatory hold, or a critical system integrity failure
- The incident has been escalated to the SRE Lead and the Engineering Manager is aware
- An incident ticket has been opened with the reason for the freeze and the scope (single SKU, warehouse, or all inventory)
- The business impact of halting inventory writes has been communicated to the order management and operations teams

## Materials/Access

- Access to the Inventory Admin Portal with emergency freeze permissions (requires SRE Lead or Engineering Manager role)
- Access to #inventory-incidents for status communication
- `kubectl` access to the `inventory` namespace for service-level interventions if needed
- Incident ticket number

## Procedure

1. Post in #inventory-incidents: "Emergency stock freeze initiated. Reason: [brief description]. Scope: [all/warehouse-id/sku-id]. Incident: [ticket number]."
2. Log in to the Inventory Admin Portal and navigate to Emergency Operations > Stock Freeze.
3. Select the freeze scope: All Warehouses, Single Warehouse (enter warehouse ID), or Single SKU (enter SKU and warehouse ID). Apply the narrowest scope that addresses the incident.
4. Click "Apply Freeze" and confirm the action. The system will return a freeze confirmation token; record this token in the incident ticket.
5. Verify the freeze is active: attempt a test stock movement via the API for an affected SKU. The API should return HTTP 423 (Locked) with a freeze reference in the response body.
6. Notify the order management and warehouse operations teams that inventory writes are frozen for the scoped items. Provide estimated duration if known.
7. Investigate and resolve the root cause of the emergency condition while the freeze is in place.
8. When the root cause is resolved and data integrity is confirmed, obtain SRE Lead approval to lift the freeze. Proceed to Rollback (Step 1 is the lift procedure).

## Validation

- Inventory API returns HTTP 423 for mutation requests (POST, PATCH, DELETE) on frozen SKUs or warehouses
- Read requests (GET) continue to function normally during the freeze
- The freeze event appears in the inventory audit log with the initiator identity, scope, and timestamp
- The order management team confirms they have received notification of the freeze scope
- No new incorrect quantity writes are occurring for the frozen scope

## Rollback

1. To lift the freeze: in the Inventory Admin Portal, navigate to Emergency Operations > Stock Freeze, locate the active freeze by its confirmation token, and click "Lift Freeze". Confirm the action.
2. Verify the freeze is lifted: retry the test stock movement from Procedure step 5. The API should now return the normal response instead of HTTP 423.
3. Monitor the stock movement log for the previously frozen scope: confirm that legitimate writes are resuming and no anomalous write patterns are occurring.
4. Post in #inventory-incidents: "Stock freeze lifted at [timestamp]. Incident [ticket number] resolved. Normal operations resumed."
5. Update the incident ticket with full timeline, root cause, and freeze duration. Schedule a post-incident review within 5 business days.
