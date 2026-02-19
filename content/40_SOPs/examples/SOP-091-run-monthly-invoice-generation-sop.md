---
id: SOP-091
type: sop
title: Run Monthly Invoice Generation SOP
status: proposed
owner: Release Manager
created: '2025-09-13T03:34:25.566Z'
updated: '2026-10-13T22:55:15.501Z'
tags:
  - sop
  - billing-engine
summary: Run Monthly Invoice Generation SOP
related_process: PROCESS-070
related_systems:
  - SYSTEM-048
example: true
---

## Preconditions

- Monthly billing cycle scheduler has completed the usage aggregation step with status `AGGREGATION_COMPLETE`
- No active billing holds flagged on more than 1% of the active account population
- Tax rate table was updated within the last 30 days and has been validated by Finance Operations
- The billing service is healthy: error rate below 0.5% and no ongoing incidents in #billing-incidents
- A billing platform engineer is available to monitor the run and respond to failures

## Materials/Access

- Access to the Billing Engine admin console (role: `billing-operator`)
- Access to the billing run dashboard in Grafana
- Access to the invoice exception queue in the Billing Engine admin console
- Slack access to #billing-operations channel
- On-call contact for Finance Operations if escalation is needed

## Procedure

1. Log in to the Billing Engine admin console and navigate to **Billing Runs > New Run**.
2. Select run type **Monthly Invoice Generation**, confirm the billing period (should pre-populate to the just-closed month), and click **Validate Inputs**. Confirm all validations pass before proceeding.
3. Post in #billing-operations: "Starting monthly invoice generation for [MONTH YEAR]. Operator: [your name]."
4. Click **Start Run**. The run will enter `IN_PROGRESS` status. Open the billing run dashboard in Grafana to monitor progress.
5. Monitor the run dashboard: watch `invoices_generated`, `invoices_failed`, and `invoices_pending` counters. If `invoices_failed` exceeds 0.5% of total accounts, pause the run and investigate.
6. When the run reaches `VALIDATION_COMPLETE` status, open the invoice exception queue and review all failed invoices. Resolve or escalate each exception before continuing.
7. Once the exception queue is clear, click **Finalize Run** to transition all validated invoices to `FINALIZED` status.
8. Confirm the `billing.invoice.finalized` events are appearing in the event stream (check the event dashboard for the last 15 minutes).
9. Post in #billing-operations: "Monthly invoice generation for [MONTH YEAR] complete. [N] invoices finalized, [N] exceptions resolved. Run ID: [ID]."

## Validation

- Invoice count in the finalized state matches expected active account count within 0.5%
- No invoices remain in `DRAFT` or `ERROR` status after finalization
- `billing.invoice.finalized` events are present in the event bus for the run period
- Total billed amount for the run is within 10% of the prior month total (flag large deviations for Finance review)
- No new alerts have fired in #billing-incidents during or after the run

## Rollback

1. If a systematic error is detected after finalization (e.g., wrong tax rates applied), post in #billing-incidents: "Invoice generation rollback initiated for [MONTH YEAR]. Reason: [description]."
2. Navigate to the billing run in the admin console and click **Void Run**. This sets all invoices for the run to `VOIDED` status and publishes `billing.invoice.voided` events.
3. Confirm with Finance Operations that the voided run's revenue recognition events have been reversed in the ledger.
4. Investigate and fix the root cause in staging before re-running invoice generation.
5. Re-run the invoice generation procedure from Step 1 after the fix is validated.
