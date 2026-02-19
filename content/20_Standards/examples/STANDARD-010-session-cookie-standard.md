---
id: STANDARD-010
type: standard
title: Session Cookie Standard
status: review
owner: Security Lead
created: '2025-05-11T13:20:32.741Z'
updated: '2026-11-05T17:23:24.761Z'
tags:
  - standard
  - user-authentication
summary: Session Cookie Standard
related_policies:
  - POLICY-010
  - POLICY-007
example: true
related_systems:
  - SYSTEM-007
  - SYSTEM-009
---

## Area

This standard governs the attributes, naming conventions, and security properties of cookies used to store session identifiers and authentication tokens in browser-based applications. It applies to all web applications that use cookies as part of their session management or authentication mechanism.

## Controls

- Session cookies must set the `HttpOnly` attribute to prevent JavaScript access and reduce XSS exposure
- Session cookies must set the `Secure` attribute to ensure transmission only over HTTPS connections
- The `SameSite=Strict` or `SameSite=Lax` attribute must be set on all session cookies; `SameSite=None` requires explicit justification and CISO approval
- Cookie names for session identifiers must use a consistent prefix (`__Secure-` for HTTPS-only, or application-specific prefix) to prevent collision across paths
- Session cookie `Max-Age` or `Expires` must align with the session lifetime defined in [[POLICY-010|OAuth Token Lifecycle Policy]] and [[POLICY-007|Password Complexity and Rotation Policy]]
- The `Domain` attribute should be omitted or scoped to the specific application domain; overly broad domain scoping is prohibited
- Persistent cookies (remember-me functionality) must use a separate, rotated token and must be invalidated on password change or explicit logout

## Compliance Mappings

- OWASP Session Management Cheat Sheet (cookie security attributes)
- NIST SP 800-63B: Section 7.1 (Session Management)
- SOC 2 CC6.7: Transmission and Disclosure of Information

## Related Policies

- [[POLICY-010|OAuth Token Lifecycle Policy]]
- [[POLICY-007|Password Complexity and Rotation Policy]]
