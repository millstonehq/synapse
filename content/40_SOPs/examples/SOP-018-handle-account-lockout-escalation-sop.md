---
id: SOP-018
type: sop
title: Handle Account Lockout Escalation SOP
status: approved
owner: DevOps Lead
created: '2024-05-25T12:41:24.738Z'
updated: '2026-09-18T14:30:00.061Z'
tags:
  - sop
  - user-authentication
summary: Handle Account Lockout Escalation SOP
related_process: PROCESS-008
related_systems:
  - SYSTEM-010
example: true
---

## Preconditions

- A user or their manager has escalated an account lockout that cannot be resolved through self-service
- The escalating party's identity has been verified through the standard support verification process
- The lockout has not been triggered by a confirmed active security incident (if so, do not unlock without CISO authorization)
- An escalation ticket has been created and linked to the affected user's account

## Materials/Access

- Admin access to the identity management system with account unlock permissions
- Access to the authentication logs to review the lockout reason and source IPs
- Escalation ticket ID
- User identity verification record confirming the requestor's identity

## Procedure

1. Pull the account's authentication log for the past 24 hours, filtering for `user_id: <affected-user>`. Identify the timestamp, source IPs, and failure reason that triggered the lockout.
2. Determine the lockout cause: normal threshold exceeded by the legitimate user (fat-finger scenario), targeted brute force against this account, or automated system using stale credentials.
3. If the lockout was caused by a targeted attack, do NOT unlock the account; escalate to the security on-call engineer and follow the brute force investigation process (SOP-013).
4. If the lockout was caused by the user or an automated system with stale credentials, verify the requestor's identity using two verification factors (e.g., manager confirmation + employee ID).
5. Unlock the account in the identity management admin console. Do not reset the password at this step unless the user also requests a password reset.
6. Advise the user of the lockout cause. If it was stale credentials (e.g., a mobile app or script using old credentials), direct them to update the credentials in the relevant system.
7. Set a 60-minute watch on the account in the authentication logs; if the account is re-locked within that window, escalate to the security team as a likely ongoing attack.
8. Update the escalation ticket with the unlock action, verification method used, and lockout root cause.

## Validation

- Account status shows "active" in the identity management system
- User confirms they can successfully log in after the unlock
- Authentication logs show a successful login from an expected IP range post-unlock
- No re-lock event within the 60-minute monitoring window

## Rollback

1. If the account is re-locked within 60 minutes, re-lock it and escalate immediately to the security on-call engineer for investigation.
2. If the unlock was performed in error (wrong account), re-lock the erroneously unlocked account immediately and notify the security team.
3. If the unlock exposes a vulnerability (account resumes attack activity), re-lock and open an incident ticket.
4. Document all actions in the escalation ticket including timestamps and outcome.
