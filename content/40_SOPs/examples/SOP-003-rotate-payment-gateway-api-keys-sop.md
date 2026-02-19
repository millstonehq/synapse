---
id: SOP-003
type: sop
title: Rotate Payment Gateway API Keys SOP
status: approved
owner: DevOps Lead
created: '2024-01-03T02:12:11.301Z'
updated: '2026-07-27T16:30:11.285Z'
tags:
  - sop
  - payment-processing
summary: Rotate Payment Gateway API Keys SOP
related_process: PROCESS-061
related_systems:
  - SYSTEM-003
example: true
---

## Preconditions

- The gateway account portal is accessible and credentials for the account admin are available
- The secrets management system (e.g., AWS Secrets Manager or HashiCorp Vault) is healthy and accessible
- No active payment incident in progress that depends on the gateway being rotated
- A maintenance window has been scheduled and communicated to the on-call engineer
- The current API key's last rotation date has been confirmed from the secrets audit log

## Materials/Access

- Gateway account portal admin credentials (stored in secrets manager, not hardcoded)
- Access to the secrets management system with write permissions for the payment gateway secret path
- Access to the payment service deployment dashboard to verify key propagation
- Access to #payments-oncall Slack channel for coordination
- The runbook identifier for this gateway in case rollback is needed

## Procedure

1. Log in to the gateway account portal and navigate to the API credentials section; note the current key ID for rollback reference.
2. Generate a new API key in the gateway portal; do not yet deactivate the existing key. Copy the new key value to a temporary secure location (do not store in clipboard longer than needed).
3. Update the secret in the secrets management system: navigate to the payment gateway secret path and create a new version with the new key value.
4. Trigger a rolling restart of the payment service pods to pick up the new secret version; monitor the restart progress in the deployment dashboard.
5. Send a test transaction through the gateway using the payment service's health check endpoint; confirm the transaction succeeds with an authorization response.
6. Verify transaction logs show the new key ID in the authorization headers (check the gateway portal's API log section).
7. After 15 minutes of successful transactions with the new key, deactivate the old API key in the gateway portal.
8. Update the key rotation record in the secrets audit log with the rotation date, rotated-by identity, and gateway name.
9. Post completion in #payments-oncall: "Gateway API key rotation for [gateway-name] complete. Old key deactivated."

## Validation

- Payment service logs show successful transactions using the new key with no authentication errors
- Gateway portal shows the old key as inactive and the new key as active
- Secrets management system shows the new key version as current with the rotation timestamp
- No payment failure alerts fired during or after the rotation
- Key rotation record is updated in the audit log

## Rollback

1. If the new key causes authentication failures, immediately re-activate the old key in the gateway portal (do not delete it until confirmed working).
2. Revert the secret in the secrets management system to the previous version using the version ID noted in step 1.
3. Trigger a rolling restart of the payment service to pick up the reverted secret.
4. Confirm successful transactions are processing with the old key via the health check endpoint.
5. Document the failed rotation in the incident log with error details and notify the DevOps Lead for root cause investigation.
