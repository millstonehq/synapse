---
id: SOP-015
type: sop
title: Revoke All Active Sessions SOP
status: proposed
owner: Release Manager
created: '2024-12-27T15:47:30.139Z'
updated: '2025-12-07T16:20:39.810Z'
tags:
  - sop
  - user-authentication
summary: Revoke All Active Sessions SOP
related_process: PROCESS-011
related_systems:
  - SYSTEM-009
example: true
---

## Preconditions

- A decision has been made by the CISO or Director of Engineering to perform a global session revocation (examples: confirmed credential database breach, widespread account compromise, critical security patch requiring forced re-authentication)
- The incident ticket authorizing this action has been created and approved
- The on-call engineering team has been assembled and is ready to respond to the expected spike in re-authentication traffic
- Communications team is prepared to notify users of the forced logout

## Materials/Access

- Admin access to the session store (Redis admin console or equivalent)
- Admin access to the OAuth token store for access token and refresh token revocation
- Access to the authentication service admin API
- Incident ticket ID authorizing the action
- Runbook for authentication service capacity monitoring during re-authentication surge

## Procedure

1. Announce the planned revocation in the #auth-incidents channel with the incident ticket ID and expected user impact before executing any actions.
2. Execute a global session flush on the session store: `FLUSHDB` on the session Redis database, or use the authorization server's admin API `POST /admin/sessions/revoke-all` endpoint.
3. Revoke all active OAuth refresh tokens by calling the token store's bulk revocation endpoint; confirm the count of revoked tokens matches the expected active token count.
4. Deploy a configuration update to increment the global session version counter in the authorization server, which will invalidate all cached JWT validations and force re-authentication.
5. Monitor the login endpoint for the expected surge in authentication requests; confirm the authentication service autoscaling triggers appropriately.
6. Verify that previously active sessions no longer work by testing with a known active session token and confirming a 401 response.
7. Monitor authentication error rate and login latency during the re-authentication surge for 30 minutes.
8. Post a status update in the #auth-incidents channel confirming revocation completion and monitoring status.

## Validation

- All previously active session identifiers return 401 when presented to any protected endpoint
- OAuth refresh tokens issued before the revocation are rejected by the token endpoint
- Authentication service error rate remains within SLO bounds during the re-authentication surge
- New logins succeed and issue fresh session tokens after revocation

## Rollback

1. Global session revocation cannot be rolled back; if this action was taken in error, immediately communicate to users that a forced logout occurred and allow them to re-authenticate normally.
2. If the re-authentication surge causes authentication service overload, scale up authentication service replicas immediately: `kubectl scale deployment/auth-service --replicas=10 -n auth`.
3. If autoscaling is insufficient, enable the authentication service rate limiter in degraded mode to protect the service and extend the re-authentication window.
4. Document the reason for the global revocation, the timeline, and user impact in the incident ticket for post-incident review.
