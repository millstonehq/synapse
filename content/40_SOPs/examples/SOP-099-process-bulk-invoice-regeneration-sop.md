---
id: SOP-099
type: sop
title: Process Bulk Invoice Regeneration SOP
status: approved
owner: DevOps Lead
created: '2025-01-16T03:17:52.087Z'
updated: '2025-03-10T22:33:22.819Z'
tags:
  - sop
  - billing-engine
summary: Process Bulk Invoice Regeneration SOP
related_process: PROCESS-059
related_systems:
  - SYSTEM-047
example: true
---

## Preconditions

- A bulk invoice regeneration has been approved by the Engineering Manager and Finance Operations
- The scope of regeneration is clearly defined: affected account IDs, billing period, and the reason (pricing bug fix, tax rate correction, data fix)
- The original invoices are in `FINALIZED` status (voided invoices are handled separately)
- A staging test of the regeneration has been performed and validated against expected outputs

## Materials/Access

- Write access to the billing bulk operations module (role: `billing-bulk-operator`)
- The approved bulk regeneration request (ticket ID)
- Access to the billing admin console for bulk operations
- Read access to the billing database to validate regeneration results
- Finance Operations contact for post-regeneration sign-off

## Procedure

1. Confirm the approved request contains: account ID list or filter criteria, affected billing period, root cause justification, expected change per invoice, and Finance Operations approval.
2. Log in to the billing admin console and navigate to **Bulk Operations > Invoice Regeneration**.
3. Upload the account ID list or enter the filter criteria (e.g., all accounts on plan `PLAN-XYZ` billed in `2025-10`).
4. Click **Preview** to generate a regeneration preview showing original and new amounts per account. Download the preview CSV.
5. Review the preview CSV: verify that the per-invoice delta matches the expected change from the approved request. Flag any outliers.
6. Submit the preview to Finance Operations for review. Do not proceed until Finance confirms the preview is correct.
7. Once Finance approves the preview, click **Execute Regeneration**. The system will void original invoices and generate corrected replacements.
8. Monitor the bulk operation status until it reaches `COMPLETE`. Note the count of voided and regenerated invoices.
9. Run a post-regeneration spot check: select 5 random accounts from the affected list and verify the new invoice amounts in the billing admin console.
10. Post in #billing-operations: "Bulk invoice regeneration complete. [N] invoices regenerated for period [PERIOD]. Request ref: [ID]."

## Validation

- All original invoices in the affected set are in `VOIDED` status
- Replacement invoices are in `FINALIZED` status with correct amounts
- Finance Operations confirms the regeneration delta is reflected in the revenue reconciliation report
- No new errors in the invoice exception queue related to the regenerated accounts

## Rollback

1. If regeneration produced incorrect results, do not proceed with payment collection for the affected accounts.
2. Void the incorrectly regenerated invoices using the billing admin console bulk void operation.
3. Restore the original invoices from the voided state (use the **Reinstate Invoice** function if available, otherwise escalate to the Billing Platform Engineer for manual restoration from audit log).
4. Investigate the regeneration error, fix the root cause, and re-validate in staging before re-attempting.
