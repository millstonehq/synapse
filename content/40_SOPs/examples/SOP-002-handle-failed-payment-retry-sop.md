---
id: SOP-002
type: sop
title: Handle Failed Payment Retry SOP
status: approved
owner: Release Manager
created: '2024-07-30T10:45:37.858Z'
updated: '2025-08-18T13:17:28.377Z'
tags:
  - sop
  - payment-processing
summary: Handle Failed Payment Retry SOP
related_process: PROCESS-005
related_systems:
  - SYSTEM-002
example: true
---

## Preconditions

- The failed payment transaction ID is known and available
- The transaction is in a `failed` or `pending_retry` state in the payment ledger
- The failure is not due to a permanent decline reason (e.g., stolen card, invalid card number)
- No active payment gateway outage that would cause retries to fail immediately
- The retry is within the merchant's configured retry window (typically 7 days from original attempt)

## Materials/Access

- Access to the payment admin console (transaction detail view)
- Access to the payments observability dashboard to monitor retry outcomes
- The transaction ID and original error code for the failed payment
- Slack access to #payments-oncall for escalation if retries continue to fail

## Procedure

1. Open the payment admin console and search for the transaction ID; review the transaction detail page including the failure reason code and gateway response.
2. Confirm the failure reason is retryable: soft declines (insufficient funds, do-not-honor, try-again) are retryable; hard declines (stolen card, invalid account, fraud block) are not.
3. For non-retryable failures, update the transaction status to `permanently_failed`, notify the merchant via webhook, and close this SOP.
4. Verify that the idempotency key for the retry attempt is distinct from the original; generate a new idempotency key using the format `{original_txn_id}-retry-{attempt_number}`.
5. In the admin console, click "Queue Retry" and confirm the retry parameters: amount, currency, payment method token, and target gateway.
6. Monitor the retry attempt in the observability dashboard; confirm the gateway response within 30 seconds.
7. If the retry succeeds, confirm the transaction status updates to `captured` and the merchant webhook is delivered.
8. If the retry fails again, check the retry attempt count against the merchant's maximum retry policy; if the limit is reached, mark as `permanently_failed` and notify the merchant.
9. Document the retry outcome in the transaction notes field with the retry timestamp and outcome reason code.

## Validation

- Transaction status in the ledger reflects the correct terminal state (`captured` or `permanently_failed`)
- Merchant has received a webhook notification for the final outcome
- Retry attempt is recorded in the transaction history with distinct idempotency key
- No duplicate charges appear on the customer's payment method
- Observability dashboard shows the transaction in the correct state

## Rollback

1. If a retry incorrectly created a duplicate charge, immediately initiate a refund for the duplicate transaction via the admin console.
2. Notify the merchant of the duplicate and the refund initiation via the #payments-oncall Slack channel.
3. Document the duplicate in the incident log with the original and duplicate transaction IDs.
4. Investigate the idempotency store to determine why the duplicate was not prevented; file a bug ticket with full details.
5. Monitor the refund status to confirm the customer is credited within the expected gateway timeline.
