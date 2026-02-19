---
id: SOP-004
type: sop
title: Investigate Stuck Transaction SOP
status: approved
owner: DevOps Lead
created: '2024-12-08T06:49:57.483Z'
updated: '2025-06-04T15:33:38.883Z'
tags:
  - sop
  - payment-processing
summary: Investigate Stuck Transaction SOP
related_process: PROCESS-003
related_systems:
  - SYSTEM-002
example: true
---

## Preconditions

- The transaction ID is known and the transaction is confirmed to be in a stuck state (e.g., `pending`, `processing`, or `authorization_pending` for longer than the expected timeout)
- Standard transaction timeout thresholds: authorization > 30 seconds, capture > 60 seconds, refund > 5 minutes
- Access to the payment admin console and transaction database is available
- The transaction is not part of an active mass-scale incident (if it is, follow the outage escalation process instead)

## Materials/Access

- Payment admin console with transaction detail and override capabilities
- Read access to the payment service database for transaction state queries
- Gateway portal access to check the gateway-side transaction status
- Access to payment service logs in the log aggregation system
- #payments-oncall Slack channel for escalation

## Procedure

1. Open the payment admin console and navigate to the transaction detail page; record the current state, last state transition timestamp, and last gateway interaction timestamp.
2. Compare the gateway-side transaction status (from the gateway portal) with the platform-side status; discrepancies indicate a state synchronization failure.
3. Check the payment service logs for the transaction ID; look for error messages, timeout events, or missing webhook callbacks from the gateway.
4. If the gateway shows the transaction as completed (authorized or captured) but the platform shows it as stuck, trigger a manual state sync from the admin console.
5. If the gateway shows the transaction as failed but the platform shows it as pending, update the platform status to `failed` via the admin console override function and queue a retry if appropriate.
6. If the gateway shows the transaction as pending, check for gateway-side processing delays using the gateway status page; wait for the gateway SLA timeout before taking action.
7. After resolving the state discrepancy, verify the customer and merchant receive the correct status notification via webhook.
8. Document the investigation findings in the transaction notes field: root cause, action taken, and resolution timestamp.

## Validation

- Transaction is in a terminal state (`captured`, `failed`, or `refunded`) in both the platform and gateway systems
- State transition is recorded in the transaction history with the correct timestamp and actor
- Customer and merchant webhooks have been delivered for the resolved state
- No duplicate transactions were created during the investigation
- Transaction notes field contains a summary of the issue and resolution

## Rollback

1. If an incorrect state override was applied, immediately contact the payments on-call engineer via #payments-oncall.
2. Use the admin console audit log to identify the incorrect override and the previous correct state.
3. Apply a corrective state override to return the transaction to the correct state, documenting the reason.
4. Verify with the gateway portal that the platform state now matches the gateway state.
5. If financial impact occurred (e.g., incorrect capture or refund), escalate to Finance Analyst for ledger adjustment.
