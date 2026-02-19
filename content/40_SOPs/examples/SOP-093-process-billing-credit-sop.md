---
id: SOP-093
type: sop
title: Process Billing Credit SOP
status: approved
owner: Release Manager
created: '2025-12-09T01:12:10.408Z'
updated: '2026-11-07T08:02:17.684Z'
tags:
  - sop
  - billing-engine
summary: Process Billing Credit SOP
related_process: PROCESS-059
related_systems:
  - SYSTEM-048
example: true
---

## Preconditions

- A credit authorization has been approved by the Engineering Manager (for credits above $1,000) or by the Customer Support team lead (for credits up to $1,000)
- The account ID, credit amount, currency, and reason code are documented in the credit authorization record
- The billing platform engineer has write access to the billing credit module

## Materials/Access

- Write access to the billing credit module in the Billing Engine admin console (role: `billing-credit-operator`)
- The approved credit authorization record (ticket ID or approval email)
- Access to the customer account in the billing admin console
- Slack access to #billing-operations for notifications

## Procedure

1. Verify the credit authorization is complete: confirm the account ID, credit amount, currency, reason code, and approver name are all present and the authorization is within the last 5 business days.
2. Log in to the Billing Engine admin console and navigate to the customer account by account ID.
3. Click **Issue Credit** and enter the credit amount, currency, reason code, and the authorization reference number from the approval record.
4. Review the credit preview: confirm the amount, currency, and the next invoice the credit will be applied against.
5. Submit the credit. The system will create a credit memo record and adjust the account's credit balance.
6. Verify the credit appears in the account's credit balance on the account overview page.
7. Confirm that a `billing.credit.issued` event has been published to the billing event bus (check the event monitor for the account ID).
8. Post in #billing-operations: "Credit issued for account [ID]: [AMOUNT] [CURRENCY], reason: [CODE]. Auth ref: [REF]."
9. Update the credit authorization ticket with the credit memo ID and mark it as processed.

## Validation

- Credit memo record is present in the billing database with status `ACTIVE`
- Customer account balance reflects the issued credit
- `billing.credit.issued` event is present in the event bus for the account
- Credit authorization ticket is closed with the credit memo ID attached
- Finance Operations ledger entry for the credit is created (verify with Finance if credit is above $1,000)

## Rollback

1. If a credit was issued in error, navigate to the credit memo in the billing admin console using the credit memo ID.
2. Click **Void Credit Memo** and enter the reason for voiding.
3. Confirm that the account credit balance is reduced by the voided amount.
4. Notify Finance Operations to reverse any ledger entries associated with the voided credit.
5. Update the original authorization ticket with the void record and notify the approver.
