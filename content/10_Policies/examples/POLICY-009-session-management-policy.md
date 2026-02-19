---
id: POLICY-009
type: policy
title: Session Management Policy
status: draft
owner: CTO
created: '2025-08-14T07:33:08.712Z'
updated: '2025-08-27T17:05:37.370Z'
tags:
  - policy
  - user-authentication
summary: Session Management Policy
example: true
related_standards:
  - STANDARD-011
  - STANDARD-009
---

## Scope

This policy governs the creation, maintenance, and termination of authenticated sessions across all web applications, APIs, and mobile clients operated by the engineering organization. It applies to both human user sessions and machine-to-machine sessions established via OAuth flows or service tokens.

## Rationale

- Session hijacking and token theft remain active attack vectors; proper session controls limit blast radius of credential theft
- Indefinitely valid sessions increase risk as they cannot be invalidated after a user's access is revoked
- Consistent session timeout and invalidation behavior across services prevents security gaps at integration boundaries
- Regulatory frameworks require that session data be protected and that sessions expire after periods of inactivity

## Policy Statements

- User sessions must have an absolute maximum lifetime of 24 hours regardless of activity
- Sessions must expire after 30 minutes of inactivity for standard users; 15 minutes for privileged users
- Session identifiers must be cryptographically random with a minimum of 128 bits of entropy
- Session tokens must be invalidated immediately upon user logout, password change, or administrative revocation
- Session data must not be stored on the client in a format that reveals server-side state or user privileges
- Concurrent session limits must be enforced: standard users may have up to 5 active sessions; privileged accounts no more than 2
- All session creation and termination events must be logged per [[STANDARD-009|Password Hashing Standard]] and applicable logging standards

## Related Standards

- [[STANDARD-011|OAuth Scope Naming Standard]]
- [[STANDARD-009|Password Hashing Standard]]
