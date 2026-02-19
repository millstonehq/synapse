---
id: SOP-012
type: sop
title: Rotate JWT Signing Keys SOP
status: approved
owner: SRE Lead
created: '2025-08-09T15:24:15.407Z'
updated: '2026-06-30T22:43:34.833Z'
tags:
  - sop
  - user-authentication
summary: Rotate JWT Signing Keys SOP
related_process: PROCESS-012
related_systems:
  - SYSTEM-009
example: true
---

## Preconditions

- The rotation is scheduled (90-day interval reached) or has been triggered by a suspected key compromise
- An approved change ticket exists for this rotation
- The new key pair has been pre-generated in the HSM or secrets manager
- The Platform Lead has been notified and the on-call engineer is available
- No active incidents are in progress that depend on the authentication service

## Materials/Access

- Access to the secrets manager (AWS Secrets Manager, Vault, or equivalent) with write permissions to the JWT key path
- Access to the authentication service configuration in the deployment system
- `kubectl` or equivalent deployment tooling configured for the production cluster
- Access to the JWKS endpoint URL to validate key publication
- Change ticket ID for audit annotation

## Procedure

1. Verify the new key pair exists in the secrets manager and confirm the key ID (`kid`) is unique and does not conflict with any currently published key.
2. Update the authorization server configuration to add the new key to the JWKS endpoint alongside the existing key; both keys must be published simultaneously during the transition period.
3. Deploy the updated configuration to the authorization server using a rolling restart to avoid downtime.
4. Verify the JWKS endpoint returns both the old and new key IDs by calling `GET /.well-known/jwks.json` and confirming both `kid` values are present.
5. Update the authorization server signing configuration to use the new key for all newly issued tokens while still accepting tokens signed with the old key.
6. Monitor the authentication service error rate and token validation metrics for 30 minutes to confirm no validation failures.
7. After waiting for the maximum token lifetime to elapse (ensuring no valid tokens with the old key remain active), remove the old key from the JWKS configuration and deploy the update.
8. Confirm the old key is no longer in the JWKS endpoint and revoke it from the secrets manager.
9. Update the key inventory record with the new key ID and next rotation due date, then close the change ticket.

## Validation

- JWKS endpoint returns only the new key ID after old key removal is deployed
- Authentication smoke tests pass: issue a new token and validate it successfully against the JWKS endpoint
- Authentication error rate remains below baseline SLO threshold after old key removal
- Secrets manager shows the old key as revoked/deleted
- Key inventory document reflects the updated rotation date and new key ID

## Rollback

1. If token validation errors spike after the new key is made the signing key, immediately restore the old key as the active signing key in the authorization server configuration and redeploy.
2. If the JWKS endpoint fails to return the new key, revert the configuration to the pre-rotation state and redeploy; validate JWKS before retrying.
3. If the new key cannot be retrieved from the secrets manager, escalate to the Security Engineer to investigate secrets manager access; do not proceed with rotation until access is confirmed.
4. Document the rollback actions in the change ticket and reschedule the rotation after root cause is identified.
