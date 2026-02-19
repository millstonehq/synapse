---
id: SOP-026
type: sop
title: Investigate Stock Mismatch SOP
status: draft
owner: DevOps Lead
created: '2025-03-11T00:37:36.858Z'
updated: '2025-05-26T21:27:31.490Z'
tags:
  - sop
  - inventory-management
summary: Investigate Stock Mismatch SOP
related_process: PROCESS-014
related_systems:
  - SYSTEM-013
example: true
---

## Preconditions

- A stock mismatch has been detected: system quantity for a SKU does not match the physical count or the quantity reported by a warehouse management system
- The affected SKU, warehouse, and approximate magnitude of the discrepancy are known
- An incident or investigation ticket has been opened referencing the SKU and warehouse
- Access to the inventory platform stock movement logs for the affected SKU is available

## Materials/Access

- Read access to the Inventory API to query current quantities and movement history
- Access to the Stock Movement Log query interface (Inventory Admin Portal > Reports > Movement History)
- Access to the affected WMS or warehouse management system to query their internal records
- Incident ticket number
- Access to #inventory-incidents for coordination

## Procedure

1. Query the current inventory API record for the affected SKU and warehouse: capture `on_hand_qty`, `reserved_qty`, `available_qty`, and `updated_at`.
2. Query the stock movement log for the SKU and warehouse for the past 7 days, sorted by `occurred_at` descending. Export the full result set.
3. Reconstruct the expected quantity by starting from the oldest movement record in the export and summing all `quantity_delta` values in chronological order. Compare the reconstructed total to `on_hand_qty`.
4. If the reconstructed total does not match `on_hand_qty`, there is a system integrity issue. Escalate to the Inventory Platform Engineer immediately before continuing.
5. Compare the system quantity to the WMS-reported quantity or physical count. Identify the timestamp of the last point where quantities were known to agree (use the movement log and WMS history to find this).
6. List all movement events that occurred between the last-known-good timestamp and now in both systems. Identify any events present in one system but not the other — these are the candidates for the root cause.
7. Categorize the root cause: sync lag (event not yet processed), duplicate event (event processed twice), missing event (event lost in transit), or manual adjustment error.
8. Document findings in the incident ticket and propose a corrective adjustment quantity and justification.
9. Obtain approval from the Inventory Operations Lead before applying any corrective adjustment.

## Validation

- After applying the corrective adjustment, the system quantity matches the WMS quantity or physical count within 0.1%
- The corrective adjustment record appears in the stock movement log with the incident ticket reference
- Running the quantity reconstruction from the movement log now produces a result matching `on_hand_qty`
- No additional mismatch alerts fire for the same SKU within 24 hours of the correction

## Rollback

1. If the corrective adjustment was applied in error, immediately halt any related order fulfillment that may use the corrected quantity.
2. Document the erroneous adjustment `movement_id` in the incident ticket.
3. Apply a reversing adjustment equal and opposite to the erroneous one, referencing the incident ticket and the original erroneous `movement_id`.
4. Confirm the reversal in the movement log and verify the quantity has returned to the pre-correction value.
5. Restart the investigation from step 5 with revised information.
