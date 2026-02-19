---
id: SOP-001
type: sop
title: Process Daily Payment Settlement SOP
status: deprecated
owner: SRE Lead
created: '2025-07-10T17:57:57.088Z'
updated: '2025-03-07T19:59:35.391Z'
tags:
  - sop
  - payment-processing
summary: Process Daily Payment Settlement SOP
related_process: PROCESS-061
related_systems:
  - SYSTEM-003
example: true
---

## Preconditions

- Gateway settlement files for the previous business day are available in the SFTP drop or via API
- The reconciliation service is running and healthy (check the reconciliation dashboard)
- Finance team has been notified that settlement processing is beginning
- No active payment incident that would affect settlement file completeness
- Database backup for the settlement period has completed successfully

## Materials/Access

- Access to the payment operations dashboard (settlement section)
- SFTP client or API credentials for gateway settlement file retrieval
- Access to the reconciliation service admin console
- Finance Slack channel (#finance-ops) for status updates
- Settlement configuration file specifying expected file formats per gateway

## Procedure

1. Log in to the payment operations dashboard and navigate to the Settlement section; confirm the expected settlement date and gateway list.
2. Trigger or verify the automated settlement file retrieval job; confirm files have been received for all active gateways. If any gateway file is missing, check the gateway status page and contact the gateway account manager.
3. Validate file format and record counts for each settlement file; reject malformed files and alert the Finance team.
4. Initiate the reconciliation run from the admin console by selecting the settlement date and clicking "Run Reconciliation."
5. Monitor the reconciliation progress; verify that the match rate reaches at least 99.5% before proceeding.
6. Review the discrepancy report: categorize each unmatched item as platform-only, gateway-only, or value mismatch.
7. For discrepancies under $1.00, batch into the daily summary report; for discrepancies over $1.00, create individual tickets.
8. Post the reconciliation summary to #finance-ops: match rate, total discrepancy count, and aggregate discrepancy value.
9. Mark the settlement run as complete in the operations dashboard and archive the settlement files.

## Validation

- Reconciliation match rate is 99.5% or higher for the settlement period
- All settlement files from active gateways have been processed without format errors
- Discrepancy tickets have been created for all items exceeding the $1.00 threshold
- Finance team has acknowledged receipt of the reconciliation summary in #finance-ops
- Settlement run is marked complete in the operations dashboard with a completion timestamp

## Rollback

1. If the reconciliation run produces unexpected results, click "Revert Reconciliation" in the admin console to undo ledger updates for the affected settlement date.
2. Notify Finance team in #finance-ops that the settlement run has been reverted and the reason.
3. Investigate the root cause of the incorrect results by reviewing the reconciliation service logs.
4. Correct the configuration or data issue identified and re-run the reconciliation from step 4 of the Procedure.
5. If the issue cannot be resolved within 4 hours, escalate to the Platform Lead and follow the payment outage escalation process.
