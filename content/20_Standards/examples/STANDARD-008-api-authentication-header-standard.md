---
id: STANDARD-008
type: standard
title: API Authentication Header Standard
status: draft
owner: Head of Engineering
created: '2025-07-21T16:32:51.678Z'
updated: '2025-06-25T03:13:57.619Z'
tags:
  - standard
  - user-authentication
summary: API Authentication Header Standard
related_policies:
  - POLICY-008
  - POLICY-009
example: true
related_systems:
  - SYSTEM-008
  - SYSTEM-010
---

## Area

This standard defines the required HTTP header format and authentication schemes for all API requests that require authentication. It applies to all internal service-to-service APIs, external partner APIs, and public-facing API endpoints operated by the engineering organization.

## Controls

- Bearer token authentication must use the `Authorization: Bearer <token>` header format as specified in RFC 6750
- API keys passed in headers must use the `X-API-Key` header; API keys must never be passed as URL query parameters
- Services must reject requests that include both `Authorization` and `X-API-Key` headers to avoid ambiguous authentication
- The `Authorization` header value must not be logged in its entirety; only the scheme prefix (e.g., `Bearer`) may appear in logs
- Services must return HTTP 401 (Unauthorized) for missing or invalid credentials, and HTTP 403 (Forbidden) for valid credentials with insufficient permissions
- All API authentication must be validated server-side; client-provided claims about identity or permissions must not be trusted without cryptographic verification
- Machine-to-machine flows using OAuth client credentials must include an explicit `aud` claim matching the target service identifier

## Compliance Mappings

- OWASP API Security Top 10: API2 (Broken Authentication)
- NIST SP 800-53: IA-8 (Identification and Authentication — Non-Organizational Users)
- SOC 2 CC6.1: Logical Access Controls

## Related Policies

- [[POLICY-008|Multi-Factor Authentication Policy]]
- [[POLICY-009|Session Management Policy]]
