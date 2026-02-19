---
id: SOP-022
type: sop
title: Process Bulk Stock Import SOP
status: review
owner: DevOps Lead
created: '2025-09-29T01:23:56.053Z'
updated: '2026-11-09T20:12:46.321Z'
tags:
  - sop
  - inventory-management
summary: Process Bulk Stock Import SOP
related_process: PROCESS-018
related_systems:
  - SYSTEM-015
example: true
---

## Preconditions

- The import file has been provided in the approved CSV format with all required columns: `sku_id`, `warehouse_id`, `quantity`, `unit_cost`, `received_at`
- All SKU identifiers in the import file have been validated against the SKU registry and confirmed as active
- The target warehouse is in `active` status in the inventory platform
- Import file row count has been confirmed by the requester and matches the expected record count
- No ongoing sync operations are in progress for the target warehouse (check the sync status dashboard)

## Materials/Access

- Access to the Inventory Admin Portal with bulk-import role permissions
- Import file in approved CSV format (max 100,000 rows per file; split larger files)
- Warehouse ID and import batch reference number from the requester
- Access to the Inventory Operations Slack channel (#inventory-ops) for status updates
- Access to Grafana inventory dashboard to monitor import progress

## Procedure

1. Log in to the Inventory Admin Portal and navigate to Bulk Operations > Stock Import.
2. Select the target warehouse from the dropdown and enter the import batch reference number provided by the requester.
3. Upload the CSV import file. The system will run a pre-flight validation; wait for the validation summary to appear before proceeding.
4. Review the pre-flight validation summary. If any rows are flagged with errors, download the error report, correct the source file, and restart from step 2. Do not proceed with a file that has errors.
5. If pre-flight validation passes, click "Start Import" and confirm in the dialog. Note the import job ID displayed on screen.
6. Monitor import progress in the admin portal. For imports over 10,000 rows, post the job ID in #inventory-ops so the team is aware of the operation.
7. Once the import job status shows "Completed", download the import results report and verify that processed count equals the expected row count.
8. Post the import results summary in #inventory-ops: batch reference, warehouse, row count, completion time.
9. Notify the requester that the import is complete and share the results report.

## Validation

- Import results report shows "Completed" status with zero failed rows
- Spot-check 5 randomly selected SKUs from the import file: verify their `on_hand_qty` in the inventory API matches the imported quantity
- Confirm that the import event appears in the stock movement log for the target warehouse with the correct batch reference
- Check that no stock level threshold alerts were incorrectly triggered by the import
- Verify the total imported quantity matches the requester's expected total

## Rollback

1. If the import has completed but the data is incorrect, do not attempt an in-place correction. Contact the Inventory Platform Engineer to initiate a bulk reversal.
2. Inventory Platform Engineer uses the import job ID to query all movement records created by the job and generates a reversal file with negated quantities.
3. Submit the reversal file through the Bulk Operations portal using the same procedure, referencing the original batch ID in the new batch reference.
4. Validate that stock quantities for affected SKUs have returned to pre-import levels by spot-checking the same 5 SKUs used in validation.
5. Notify the requester of the rollback and request a corrected import file before re-running.
