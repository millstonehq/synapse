---
id: SOP-092
type: sop
title: Handle Billing Discrepancy SOP
status: approved
owner: Release Manager
created: '2024-11-26T12:23:43.240Z'
updated: '2026-03-10T23:07:35.508Z'
tags:
  - sop
  - billing-engine
summary: Handle Billing Discrepancy SOP
related_process: PROCESS-058
related_systems:
  - SYSTEM-050
example: true
---

## Preconditions

- A billing discrepancy has been identified: either by a customer dispute, an automated reconciliation alert, or internal Finance review
- The disputed invoice ID and account ID are known
- The billing platform engineer has read access to the billing database, usage event logs, and invoice generation logs

## Materials/Access

- Read access to the billing database (role: `billing-reader`)
- Access to the usage event query tool in the Billing Engine admin console
- Access to invoice generation logs in the centralized log system (Kibana or equivalent)
- Dispute ticket ID in the support ticketing system
- Access to the billing run dashboard for the relevant billing period

## Procedure

1. Open the dispute ticket and record the account ID, invoice ID, disputed amount, and the customer's stated reason for the dispute.
2. In the Billing Engine admin console, open the invoice by ID and review all line items, applied discounts, and tax charges.
3. Export the raw usage events for the account and billing period using the usage event query tool. Verify the event count and aggregate usage values match what is reflected in the invoice.
4. Check the invoice generation log for the account and period: confirm no errors or warnings were logged during generation, and that the pricing plan version used matches the active plan at billing time.
5. If a discrepancy is found between usage events and the invoice, determine whether the source is a metering issue, a pricing calculation bug, or a tax rate error.
6. Document the root cause in the dispute ticket with supporting log evidence.
7. If the invoice is incorrect, calculate the correct amount and prepare a credit memo request: specify the credit amount, the reason, and the invoice it corrects. Submit to Finance Operations for approval.
8. Once the credit is approved and applied, update the dispute ticket with the outcome and notify the customer support agent to close the dispute with the customer.

## Validation

- The corrected billing amount matches the expected amount calculated from raw usage events
- Credit memo is reflected in the customer's account balance in the billing system
- Dispute ticket is closed with root cause documented
- If the discrepancy was caused by a platform bug, a bug ticket has been filed with the root cause

## Rollback

1. If a credit was applied incorrectly, navigate to the customer account in the billing admin console and locate the credit memo.
2. Click **Void Credit** and confirm the void action. This reverses the balance adjustment.
3. Notify Finance Operations of the voided credit so ledger entries can be corrected.
4. Re-investigate the discrepancy with the corrected understanding and reopen the dispute ticket if needed.
