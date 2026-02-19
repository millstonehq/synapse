---
id: WIKI-008
type: wiki
title: JWT Claims - Reference Guide
status: approved
owner: User Team
created: '2024-02-07T02:10:56.611Z'
updated: '2026-10-05T18:33:30.035Z'
tags:
  - wiki
  - user-authentication
summary: JWT Claims - Reference Guide
source_repo: https://git.example.com/acme/jwt-claims
commit_sha: cff8859ca669c87f63eb9610ef02a874d0f38cfa
generated_at: '2026-11-30T16:25:20.125Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: gpt-4o
importance: medium
example: true
---

## Overview

This page is the reference guide for JWT claims used in access tokens and ID tokens issued by the OAuth Authorization Server. It documents every claim, its type, source, and usage across resource servers. All tokens are RS256-signed JWTs. Access tokens have a 15-minute expiry; ID tokens have a 60-minute expiry.

This page was auto-generated from `jwt-claims` repository analysis. Resource servers should validate the `iss`, `aud`, `exp`, and `nbf` claims on every request, then extract the relevant claims for authorization decisions.

## Architecture

JWT claims are assembled by the `internal/token/claims.go` package in the OAuth Authorization Server. Claims are grouped into three categories:

- **Standard claims** (RFC 7519): `sub`, `iss`, `aud`, `exp`, `nbf`, `iat`, `jti`
- **Profile claims** (OIDC Core 1.0): `name`, `email`, `email_verified`, `picture`
- **Custom platform claims**: `org_id`, `roles`, `permissions`, `mfa_amr`, `sid`

## Key Components

### Standard Claims

| Claim | Type | Description |
|-------|------|-------------|
| `sub` | string | User ID (UUID v4). Stable across logins. |
| `iss` | string | Token issuer URI: `https://auth.example.com` |
| `aud` | string[] | Intended audience. Must match the resource server's configured audience. |
| `exp` | number | Expiry timestamp (Unix epoch). Reject tokens where `exp < now`. |
| `nbf` | number | Not-before timestamp. Reject tokens where `nbf > now`. |
| `iat` | number | Issued-at timestamp. |
| `jti` | string | JWT ID — unique per token, used for revocation lookups. |

### Custom Platform Claims

| Claim | Type | Description |
|-------|------|-------------|
| `org_id` | string | Organization UUID the user authenticated under. |
| `roles` | string[] | List of role names assigned to the user in the org. |
| `permissions` | string[] | Flattened list of permissions derived from roles. |
| `mfa_amr` | string[] | Authentication methods used (e.g., `["pwd","totp"]`). |
| `sid` | string | Session ID. Matches the session in the Session Management Service. |

## Configuration

Claim assembly is controlled by the `CLAIMS_INCLUDE_PERMISSIONS` and `CLAIMS_INCLUDE_ROLES` feature flags. By default both are enabled. Disabling `CLAIMS_INCLUDE_PERMISSIONS` reduces token size for high-frequency service account tokens that rely on server-side permission checks.

## Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| `github.com/go-jose/go-jose/v3` | v3.0.3 | JWT signing and serialization |
| `github.com/lestrrat-go/jwx/v2` | v2.0.19 | JWKS key set management |

## Generation Notes

Generated from commit `cff8859` on the `main` branch. The generator extracted claim definitions from struct tags and inline comments in the claims assembly package. Manual review is recommended for custom claim semantics.
