---
id: SOP-095
type: sop
title: Investigate Failed Invoice SOP
status: approved
owner: Release Manager
created: '2024-11-20T19:11:53.958Z'
updated: '2025-05-24T03:34:38.337Z'
tags:
  - sop
  - billing-engine
summary: Investigate Failed Invoice SOP
related_process: PROCESS-059
related_systems:
  - SYSTEM-047
example: true
---

## Preconditions

- A failed invoice has been identified in the invoice exception queue or via the `billing.invoice.failed` event
- The invoice ID, account ID, and failure timestamp are known
- The billing platform engineer has read access to billing logs and the usage event query tool

## Materials/Access

- Read access to the billing database (role: `billing-reader`)
- Access to invoice generation logs in the log aggregation system
- Access to the usage event query tool in the Billing Engine admin console
- Access to the invoice exception queue in the billing admin console
- Slack access to #billing-incidents for escalation if needed

## Procedure

1. Open the invoice exception queue and locate the failed invoice record by invoice ID. Note the failure reason code and timestamp.
2. Open the invoice generation log for the account and billing period. Filter by account ID and the invoice's attempted generation timestamp.
3. Identify the error class from the log: schema validation failure, tax calculation error, usage data missing, pricing plan configuration error, or downstream service timeout.
4. For **missing usage data**: check if the usage aggregation job for the account completed successfully. Query the usage event store for the account and period to determine if events were ingested.
5. For **pricing plan errors**: verify the account's active plan assignment is valid at the billing period end date and the plan configuration is complete.
6. For **tax calculation errors**: check the tax calculation service logs for the account. Verify the customer's billing address is complete and the jurisdiction is resolvable.
7. For **schema validation failures**: review the invoice draft in the database for missing required fields and identify the upstream data gap.
8. Once root cause is identified, apply the fix (correct the data gap, trigger a reprocess, or escalate to the relevant service owner) and reprocess the invoice using the **Retry Invoice** function in the admin console.
9. Confirm the reprocessed invoice enters `FINALIZED` status and verify line items are correct.

## Validation

- The invoice is now in `FINALIZED` status in the billing database
- Invoice line items correctly reflect usage and plan charges for the period
- No new failure events for the same invoice are present in the event stream
- If the failure was caused by a systematic data issue, a bug ticket has been filed

## Rollback

1. If the reprocessed invoice generates incorrect amounts, void the invoice using the **Void Invoice** action in the admin console.
2. Document the void reason in the billing audit log.
3. Investigate the reprocessing error, correct the root cause, and re-attempt after validation in staging.
4. Notify Finance Operations if the voided invoice affects revenue recognition for the period.
