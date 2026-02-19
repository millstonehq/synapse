---
id: SOP-008
type: sop
title: Handle Duplicate Payment SOP
status: approved
owner: DevOps Lead
created: '2025-07-16T15:07:57.562Z'
updated: '2025-11-21T13:28:23.665Z'
tags:
  - sop
  - payment-processing
summary: Handle Duplicate Payment SOP
related_process: PROCESS-001
related_systems:
  - SYSTEM-005
example: true
---

## Preconditions

- A duplicate payment has been identified: two or more transactions for the same amount, same payment method, and same merchant within a short time window (typically < 5 minutes)
- At least one of the transactions has been captured (settled) at the gateway
- The customer or merchant has reported the duplicate, or it was detected by automated duplicate monitoring
- The duplicate detection is confirmed against the idempotency store — the transactions must have different idempotency keys to be considered a true system-level duplicate

## Materials/Access

- Access to the payment admin console to view transaction details and initiate refunds
- Access to the idempotency store query tool to check key usage history
- Access to payment service logs to trace the duplicate origination
- Access to the gateway portal to confirm both transactions are reflected in the gateway ledger
- #payments-oncall Slack channel for coordination if escalation is needed

## Procedure

1. Retrieve both transaction records from the admin console; confirm they share the same payment method token, amount, currency, and merchant ID.
2. Check the idempotency store: if both transactions share the same idempotency key, this is an idempotency system failure — escalate immediately to the payments on-call engineer.
3. If transactions have different idempotency keys, this is a client-side duplicate submission; proceed with the standard resolution steps.
4. Confirm with the gateway portal that both transactions were captured; if only one was captured, void the uncaptured authorization.
5. Determine which transaction to retain as the authoritative charge: typically the first by timestamp; confirm with the merchant if ambiguous.
6. Initiate a full refund for the duplicate transaction from the admin console, using the refund reason code "duplicate_charge."
7. Notify the customer via the platform's notification service that a duplicate charge was detected and a refund has been initiated.
8. Notify the merchant via webhook or email with both transaction IDs, the refund amount, and the expected customer credit timeline.
9. Document findings in the duplicate transaction ticket: root cause (client retry, idempotency failure, etc.), action taken, and refund transaction ID.

## Validation

- Refund for the duplicate transaction is in `pending_refund` or `refunded` status in the ledger
- Customer has received a notification confirming the refund
- The retained authoritative transaction remains in `captured` status without modification
- Gateway portal confirms only one net charge for the disputed amount after the refund
- Duplicate ticket is documented with root cause and linked to both transaction IDs

## Rollback

1. If the wrong transaction was refunded (the duplicate was retained and the original refunded), immediately initiate a new refund for the remaining duplicate transaction.
2. Contact the merchant to explain the correction and provide both refund transaction IDs.
3. Update the ticket with the correction details and timeline.
4. Escalate to Finance Analyst if the net customer balance after corrections requires a ledger adjustment.
5. File a bug report for any idempotency-related root cause with full details for engineering investigation.
