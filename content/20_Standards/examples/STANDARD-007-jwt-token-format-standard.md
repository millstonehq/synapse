---
id: STANDARD-007
type: standard
title: JWT Token Format Standard
status: draft
owner: Head of Engineering
created: '2025-04-29T17:58:47.217Z'
updated: '2026-08-26T13:46:43.174Z'
tags:
  - standard
  - user-authentication
summary: JWT Token Format Standard
related_policies:
  - POLICY-009
  - POLICY-008
example: true
related_systems:
  - SYSTEM-008
  - SYSTEM-006
---

## Area

This standard governs the structure, signing, and validation of JSON Web Tokens (JWTs) used for authentication and authorization across all services operated by the engineering organization. It applies to access tokens, identity tokens, and any other JWT-formatted credential issued or consumed by internal or partner-facing systems.

## Controls

- All JWTs must be signed using RS256 (RSA + SHA-256) or ES256 (ECDSA + SHA-256); symmetric algorithms (HS256) are prohibited for tokens shared across service boundaries
- Required claims: `iss` (issuer URL), `sub` (subject identifier), `aud` (intended audience), `exp` (expiration), `iat` (issued at), `jti` (unique token ID for replay prevention)
- Token expiration (`exp`) must align with the lifetime defined in [[POLICY-009|Session Management Policy]] and [[POLICY-008|Multi-Factor Authentication Policy]]
- The `alg: none` value is explicitly prohibited; services must reject tokens with `alg: none`
- Token payload must not contain sensitive data (passwords, PII beyond identifier) that would be exposed if the token is decoded
- Signing key IDs must be included in the token header (`kid`) to support key rotation without service downtime
- Services must validate all required claims and reject tokens with missing, expired, or mismatched `aud` or `iss` values

## Compliance Mappings

- NIST SP 800-63B: Section 5.1 (Authenticator and Verifier Requirements)
- OAuth 2.0 (RFC 6749) and JWT Best Current Practices (RFC 8725)
- SOC 2 CC6.1: Logical and Physical Access Controls

## Related Policies

- [[POLICY-009|Session Management Policy]]
- [[POLICY-008|Multi-Factor Authentication Policy]]
