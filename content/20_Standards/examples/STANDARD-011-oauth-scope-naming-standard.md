---
id: STANDARD-011
type: standard
title: OAuth Scope Naming Standard
status: draft
owner: Security Lead
created: '2025-05-19T08:00:23.692Z'
updated: '2025-02-17T16:05:04.308Z'
tags:
  - standard
  - user-authentication
summary: OAuth Scope Naming Standard
related_policies:
  - POLICY-008
  - POLICY-006
example: true
related_systems:
  - SYSTEM-010
  - SYSTEM-008
---

## Area

This standard defines the naming conventions and semantic meaning of OAuth 2.0 scopes used across all authorization servers and resource servers operated by the engineering organization. Consistent scope naming enables predictable access control, reduces integration friction for partners, and simplifies audit of granted permissions.

## Controls

- Scopes must follow the pattern `<resource>:<action>` using lowercase snake_case, for example: `user:read`, `orders:write`, `admin:manage`
- Wildcard scopes (e.g., `*` or `admin:*`) are prohibited in partner-facing OAuth clients and require CISO review for internal service accounts
- Scope names must be documented in the authorization server's discovery endpoint with human-readable descriptions
- Read and write operations must use separate scopes; a scope granting write must not implicitly grant read of a different resource class
- Scopes that grant administrative or privileged access must include the `admin` prefix and must require MFA per [[POLICY-008|Multi-Factor Authentication Policy]]
- Deprecated scopes must be maintained for a minimum of 90 days after successor scopes are published, with migration documentation provided to affected clients
- Scope grants must follow the principle of least privilege; authorization servers must not issue scopes broader than explicitly requested by the client

## Compliance Mappings

- OAuth 2.0 RFC 6749: Section 3.3 (Access Token Scope)
- NIST SP 800-63C: Section 5 (Federation and Assertions)
- SOC 2 CC6.3: Role-Based Access Controls

## Related Policies

- [[POLICY-008|Multi-Factor Authentication Policy]]
- [[POLICY-006|Authentication Data Handling Policy]]
