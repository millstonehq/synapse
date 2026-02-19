---
id: SOP-087
type: sop
title: Debug Customer Session Issue SOP
status: approved
owner: DevOps Lead
created: '2024-06-05T13:30:47.986Z'
updated: '2026-07-16T16:37:22.804Z'
tags:
  - sop
  - customer-portal
summary: Debug Customer Session Issue SOP
related_process: PROCESS-049
related_systems:
  - SYSTEM-041
example: true
---

## Preconditions

- A customer session issue has been reported: unexpected logout, session not persisting, or "not authenticated" errors on authenticated routes
- The affected customer account ID and approximate time of the issue are known
- On-call engineer or tier-2 support has opened an investigation ticket

## Materials/Access

- Access to portal application logs in Datadog/Kibana filtered by customer account ID
- Access to the Redis session store (read-only) for session inspection
- Access to the identity provider (SSO/OAuth) admin console
- Browser developer tools for reproducing the issue in a test environment

## Procedure

1. Confirm the customer's reported symptoms by attempting to reproduce the session issue in the staging environment using a test account with the same configuration (SSO provider, account tier, browser).
2. In Datadog, filter portal API logs by the customer's account ID and the reported time window; look for `401 Unauthorized` or `session_expired` events.
3. Check the session expiry configuration: verify `SESSION_TTL` in the portal configuration matches the expected value and has not been inadvertently reduced.
4. Inspect the Redis session store for the customer's session key (prefix: `portal:session:[account-id]`); check whether the session exists and its TTL value.
5. If the session is missing or expired unexpectedly, check whether a portal deployment or Redis restart occurred during the customer's session.
6. If the customer uses SSO, check the identity provider admin console for authentication errors or token expiry issues on the customer's account.
7. If the issue is a known bug (e.g., session not renewed on activity), apply the workaround: manually extend the session TTL in Redis using `EXPIRE portal:session:[account-id] [TTL]`.
8. If the root cause is a configuration error, open a change ticket to correct the configuration and redeploy.
9. Notify the customer of the resolution and, if applicable, ask them to log back in and confirm the issue is resolved.

## Validation

- Customer can log in and maintain their session for the expected TTL without unexpected logouts
- Portal API logs show no `401` errors for the customer's account in the 10 minutes following the fix
- Session key in Redis shows the correct TTL value
- If SSO-related, identity provider shows successful token issuance for the account

## Rollback

1. If a configuration change to session TTL or cookie settings was applied and caused new session issues, revert the configuration via the change management process.
2. Flush the affected session keys in Redis to force a clean re-authentication for affected customers.
3. Notify impacted customers that they will need to log in again.
4. Verify session behavior is normal after the revert by testing in staging before confirming resolution.
