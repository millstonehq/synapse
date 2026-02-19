---
id: SOP-011
type: sop
title: Reset Compromised User Credentials SOP
status: deprecated
owner: DevOps Lead
created: '2024-08-24T02:07:38.368Z'
updated: '2026-11-01T21:35:35.647Z'
tags:
  - sop
  - user-authentication
summary: Reset Compromised User Credentials SOP
related_process: PROCESS-009
related_systems:
  - SYSTEM-010
example: true
---

## Preconditions

- A security alert or report has been received indicating a specific user account may be compromised
- The affected user's account identifier (email or user ID) is confirmed
- You have access to the identity management admin console or equivalent CLI tooling
- The on-call security engineer has been notified and is aware of the action being taken
- An incident ticket has been created to track this action

## Materials/Access

- Admin access to the identity management system (Okta, Auth0, or equivalent)
- Access to the authentication service admin API with credentials reset permissions
- Access to the session store admin interface (Redis CLI or admin panel) for session invalidation
- Incident ticket number for audit trail reference
- Secure out-of-band communication channel to notify the affected user

## Procedure

1. Lock the affected user account in the identity management admin console to immediately prevent new logins while the reset is being performed.
2. Revoke all active sessions for the user by executing a global session invalidation in the session store using the user's identifier.
3. Revoke all active OAuth access tokens and refresh tokens issued to the user by calling the token revocation endpoint for each registered OAuth client.
4. Generate a secure, time-limited password reset link (expires in 2 hours) from the identity management system.
5. Notify the affected user via a verified out-of-band channel (phone or secondary email on file) with the password reset link and instructions; do not send via the potentially compromised channel.
6. If MFA devices may be compromised, also reset the user's MFA enrollment and require re-enrollment upon next login.
7. Re-enable the user account once the user confirms they have successfully reset their credentials.
8. Document all actions taken in the incident ticket with timestamps.

## Validation

- Confirm the user's account status shows as active in the identity management system after the reset cycle completes
- Verify that all previous sessions for the user appear as invalidated in the session store
- Confirm the user can successfully log in with their new credentials and complete MFA enrollment
- Check authentication logs to confirm no residual tokens signed with the old credentials are being accepted
- Verify the incident ticket has been updated with all action timestamps and the ticket is assigned for post-incident review

## Rollback

1. If the user reports being incorrectly locked out, re-enable the account immediately in the identity management admin console.
2. If the password reset link expired before use, generate a new reset link and re-send it via the out-of-band channel.
3. If MFA re-enrollment fails due to device issues, temporarily grant a bypass code with a 24-hour expiry via the identity management system.
4. If session invalidation caused downstream service disruptions, escalate to the Platform Lead and open a separate incident for service recovery.
5. Document all rollback actions in the original incident ticket with reasoning.
