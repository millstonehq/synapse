---
id: SOP-025
type: sop
title: Run Nightly Inventory Sync SOP
status: approved
owner: Release Manager
created: '2024-09-25T08:40:12.816Z'
updated: '2025-04-14T01:29:12.536Z'
tags:
  - sop
  - inventory-management
summary: Run Nightly Inventory Sync SOP
related_process: PROCESS-018
related_systems:
  - SYSTEM-011
example: true
---

## Preconditions

- The nightly sync job is scheduled for 02:00 UTC; this SOP covers both automated runs and manual reruns when the automated job fails
- All warehouse connections in the inventory platform show `connected` status before the sync window opens
- No bulk import or large-scale adjustment operations are in progress that could interfere with sync consistency
- The previous nightly sync completed successfully (check the sync history dashboard); if it did not, escalate before running again
- On-call engineer has been notified if this is a manual rerun

## Materials/Access

- Access to the Inventory Sync Admin dashboard
- Access to Grafana for monitoring sync throughput and lag metrics
- Access to #inventory-ops for status updates
- SSH or `kubectl` access to the sync job pods (for log inspection only)
- Sync job configuration file location: `inventory-sync-service/config/nightly-sync.yaml`

## Procedure

1. Log in to the Inventory Sync Admin dashboard and navigate to Jobs > Nightly Sync.
2. If running manually: verify that no automated run is currently in progress. Click "Run Now" and confirm. Record the job ID displayed.
3. Monitor the sync progress panel: watch warehouse-by-warehouse completion status. Each warehouse should begin processing within 2 minutes of the job start.
4. If any warehouse shows `stalled` (no progress for more than 5 minutes), check the sync service logs: `kubectl logs -n inventory -l app=inventory-sync --since=10m`.
5. Once all warehouses show `completed`, review the sync summary report: note total records processed, records updated, and any skipped or errored records.
6. If skipped or errored records exceed 0.5% of total: do not mark the sync as successful. Investigate the errors in the sync log before proceeding.
7. Download the reconciliation report from the admin dashboard and verify it has been automatically uploaded to the designated reconciliation archive bucket.
8. Post the sync summary in #inventory-ops: job ID, duration, warehouses synced, records processed, error count.

## Validation

- Sync job status shows `completed` for all active warehouses
- Error record count is below 0.5% of total records processed
- Reconciliation report has been generated and is accessible in the archive
- Grafana shows sync consumer lag returning to baseline within 30 minutes of job completion
- Data freshness timestamps in the inventory API are updated to within the sync window for all warehouses

## Rollback

1. The nightly sync is a read-reconcile-update operation; it does not destructively alter inventory records. True rollback is not applicable for a successful sync.
2. If a sync job wrote incorrect data due to a source system error, identify the affected warehouses from the sync error log and raise an incident ticket.
3. Contact the Inventory Platform Engineer to apply targeted adjustments correcting any incorrect quantities, using the sync job ID as the reference.
4. Re-run the nightly sync only after the source data issue has been confirmed as resolved by the warehouse operations team.
5. Notify #inventory-ops of the corrective action taken and the confirmed correct quantities.
