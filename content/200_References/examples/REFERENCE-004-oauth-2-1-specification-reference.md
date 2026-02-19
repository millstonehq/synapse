---
id: REFERENCE-004
type: reference
title: OAuth 2.1 Specification Reference
status: draft
owner: Engineering Team
created: '2024-09-20T19:32:06.669Z'
updated: '2026-07-11T21:13:38.442Z'
tags:
  - reference
  - user-authentication
summary: OAuth 2.1 Specification Reference
upstream_url: https://docs.example.com/oauth-2-1-specification-reference
last_synced: '2025-01-26T05:59:26.369Z'
attribution: NIST
license: CC BY-SA 4.0
category: tutorial
example: true
---

## Overview

OAuth 2.1 consolidates OAuth 2.0 (RFC 6749) with security best practices from subsequent RFCs and BCP documents. This reference page summarizes the key differences between OAuth 2.0 and 2.1, and documents how the platform's OAuth Authorization Server conforms to the OAuth 2.1 draft specification (draft-ietf-oauth-v2-1). The authoritative specification is available at [https://www.ietf.org/archive/id/draft-ietf-oauth-v2-1-12.txt](https://www.ietf.org/archive/id/draft-ietf-oauth-v2-1-12.txt).

The platform's implementation targets OAuth 2.1 compliance. This reference is used during implementation review to verify conformance with the specification.

## Key Changes from OAuth 2.0 to 2.1

OAuth 2.1 removes several features that were considered insecure in practice and mandates security measures that were previously optional:

- **PKCE is required for all clients**: In OAuth 2.0, PKCE (RFC 7636) was optional and typically only recommended for public clients. OAuth 2.1 mandates PKCE for all authorization code grant flows, including confidential clients. Platform implementation: PKCE is required for all `/authorize` requests.
- **Implicit grant removed**: The implicit grant type (`response_type=token`) is removed. Applications must use the authorization code flow. Platform implementation: Implicit grant is not supported.
- **Resource Owner Password Credentials grant removed**: The ROPC grant is removed as it requires the client to handle user credentials directly. Platform implementation: ROPC is not supported.
- **Redirect URI must be an exact match**: OAuth 2.1 prohibits wildcard or pattern-matched redirect URIs. Platform implementation: Redirect URIs are validated as exact string matches against the registered allowlist.
- **Bearer tokens must not be passed in query parameters**: Tokens in URL query parameters are logged by servers and proxies. Platform implementation: Bearer tokens in query parameters are rejected with HTTP 400.

## Grant Types

The platform supports the following OAuth 2.1 grant types:

| Grant Type | Use Case | PKCE Required |
|-----------|----------|---------------|
| Authorization Code | User-facing applications | Yes (always) |
| Client Credentials | Service-to-service | N/A (no user) |
| Refresh Token | Token renewal | N/A (uses existing grant) |
| Device Authorization | CLI and TV apps | N/A (device flow) |

## Token Specifications

- **Access tokens**: RS256-signed JWTs, 15-minute expiry. Audience (`aud`) claim must match the resource server's configured identifier. Resource servers validate tokens locally using the JWKS endpoint.
- **Refresh tokens**: Opaque 256-bit random strings, 30-day expiry, single-use (rotated on each redemption). Stored in Redis.
- **Authorization codes**: Opaque 128-bit random strings, 60-second expiry, single-use. Stored in Redis.

## Scopes

The platform uses a `resource:action` scope format (e.g., `users:read`, `billing:write`). Scopes are validated at authorization request time and embedded in the access token `scope` claim. Resource servers validate that the token scope includes the required permission for the operation.

## Client Registration

All OAuth clients must be registered before use. Client registration stores: client ID, client secret (hashed, for confidential clients), allowed grant types, redirect URI allowlist, allowed scopes, and token lifetime overrides. Public clients (SPAs, mobile apps) use PKCE without a client secret.
