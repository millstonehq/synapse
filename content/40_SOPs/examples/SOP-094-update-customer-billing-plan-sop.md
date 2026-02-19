---
id: SOP-094
type: sop
title: Update Customer Billing Plan SOP
status: approved
owner: DevOps Lead
created: '2024-01-06T16:16:51.053Z'
updated: '2025-09-23T00:25:23.259Z'
tags:
  - sop
  - billing-engine
summary: Update Customer Billing Plan SOP
related_process: PROCESS-057
related_systems:
  - SYSTEM-049
example: true
---

## Preconditions

- A plan change request has been approved through the Billing Plan Configuration Process
- The new billing plan is active and validated in the production Billing Engine
- The account ID and the target plan ID are confirmed and documented in the change request
- If the change is mid-cycle, a pro-ration calculation has been reviewed and approved by Finance Operations

## Materials/Access

- Write access to the billing account management module (role: `billing-account-manager`)
- The approved plan change request ticket (ticket ID)
- Access to the billing admin console
- Read access to the billing database to verify the change post-execution

## Procedure

1. Confirm the plan change request ticket is approved and contains: account ID, current plan ID, new plan ID, effective date, and pro-ration handling (immediate or next cycle).
2. Log in to the Billing Engine admin console and navigate to the customer account by account ID.
3. Review the current plan assignment and billing history to confirm the account's current state before making changes.
4. Click **Change Plan**, select the new plan ID, set the effective date, and select the pro-ration handling method per the approved request.
5. Review the plan change preview: confirm the new plan name, effective date, pro-ration credit (if applicable), and the next invoice estimate.
6. Submit the plan change. The system will create a plan assignment record and schedule any pro-ration entries.
7. Verify the account now shows the new plan ID in the account overview.
8. If the change is effective immediately, confirm that any pro-ration credit has been applied to the account balance.
9. Update the plan change request ticket with the new plan assignment record ID and mark as completed.

## Validation

- The customer account shows the new plan ID effective from the correct date
- If pro-ration was applied, the credit amount matches the pre-approved calculation
- The next billing cycle preview on the account reflects the new plan's pricing
- A `billing.plan.changed` event is present in the billing event bus for the account

## Rollback

1. If a plan change was made in error, navigate to the account's plan assignment history in the billing admin console.
2. Click **Revert Plan Assignment** and select the previous plan record to restore.
3. Confirm the effective date for the revert and submit.
4. If pro-ration credits were applied for the erroneous change, void those credits per the Process Billing Credit SOP rollback procedure.
5. Update the change request ticket with the revert record and notify the requester.
