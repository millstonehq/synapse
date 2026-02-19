---
id: SOP-019
type: sop
title: Update OAuth Client Configuration SOP
status: approved
owner: SRE Lead
created: '2025-03-05T00:54:34.230Z'
updated: '2025-10-24T08:49:15.972Z'
tags:
  - sop
  - user-authentication
summary: Update OAuth Client Configuration SOP
related_process: PROCESS-008
related_systems:
  - SYSTEM-007
example: true
---

## Preconditions

- A request to modify an OAuth client's configuration (redirect URIs, allowed scopes, client secret, grant types) has been submitted and approved
- The change has been reviewed by the Platform Lead or Security Engineer if it expands the client's granted scopes or redirect URIs
- An approved change ticket exists for the configuration update
- The requesting team's identity has been verified and their ownership of the client record confirmed

## Materials/Access

- Admin access to the authorization server administration console or OAuth client registry
- Access to the secrets manager if the update involves rotating the client secret
- The OAuth client ID being modified
- Change ticket ID for audit reference

## Procedure

1. Log in to the authorization server administration console and locate the OAuth client record by client ID.
2. Review the current configuration and document the existing values (redirect URIs, scopes, grant types) in the change ticket before making any modifications.
3. Apply the approved configuration changes as specified in the change ticket. For redirect URI additions, confirm each new URI matches the application's registered domain; wildcard URIs are prohibited.
4. If the update includes a scope expansion, verify that the expanded scopes align with the OAuth Scope Naming Standard before saving.
5. If the update involves rotating the client secret, generate a new secret in the secrets manager and update the client record in the authorization server. Do not delete the old secret until the client confirms the new secret is in use.
6. Save the updated configuration and confirm the changes are reflected in the client record.
7. Notify the client's owning team to validate their integration in the staging environment using the updated configuration.
8. After the owning team confirms the update is working, delete the old client secret from the secrets manager (if rotated) and close the change ticket.

## Validation

- OAuth client record reflects all changes as specified in the change ticket
- The owning team's staging integration test confirms the updated configuration functions correctly
- If the secret was rotated, the old secret is confirmed deleted from the secrets manager
- Authorization flows using the updated client complete successfully (authorization code exchange or client credentials flow as applicable)

## Rollback

1. If the configuration update breaks the client's authentication flow, revert the client record to the previously documented values using the snapshot captured in step 2.
2. If the client secret rotation causes integration failures, re-add the old secret to the secrets manager and restore it in the client record while the owning team investigates.
3. Document all rollback actions in the change ticket with timestamps and root cause.
4. If the rollback reveals a security concern (e.g., scope was incorrectly expanded), notify the Security Engineer immediately.
