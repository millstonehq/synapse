---
id: WIKI-042
type: wiki
title: Auth Tokens - Lifecycle and Revocation
status: approved
owner: User Team
created: '2024-04-22T11:37:44.855Z'
updated: '2025-08-06T16:04:21.327Z'
tags:
  - wiki
  - user-authentication
summary: Auth Tokens - Lifecycle and Revocation
source_repo: https://git.example.com/acme/auth-tokens
commit_sha: b190ff5200891d2b193a29dbab5b7e80d69138dd
generated_at: '2025-03-05T17:22:21.844Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: claude-3-sonnet
example: true
---

## Overview

This page documents the lifecycle of authentication tokens issued by the platform — access tokens, refresh tokens, and authorization codes — including how they are created, validated, expired, and revoked. Understanding token lifecycle is important for developers building integrations and for on-call engineers diagnosing authentication issues.

The platform issues three types of tokens in the OAuth 2.1 flow: short-lived JWT access tokens (15 minutes), long-lived opaque refresh tokens (30 days), and ephemeral authorization codes (60 seconds). Each has distinct storage, validation, and revocation semantics.

## Architecture

The token lifecycle is managed across two services and one shared data store:

- **OAuth Authorization Server**: Issues all token types at the `/token` endpoint. Signs access tokens with an RS256 key from Vault. Stores authorization codes and refresh tokens in Redis.
- **Token Refresh Service**: Handles refresh token redemption and rotation. Enforces single-use semantics and token family tracking for theft detection.
- **Redis Cluster**: Stores authorization codes (60-second TTL), refresh tokens (30-day TTL), and the access token revocation blocklist (entries have TTL equal to token remaining lifetime).

## Key Components

### Access Token Lifecycle

Access tokens are RS256-signed JWTs with a 15-minute expiry. They are self-contained: resource servers validate them locally using the JWKS endpoint without contacting the authorization server. The lifecycle:

1. **Issued**: After successful authentication or refresh token redemption. Contains `sub`, `aud`, `scope`, `exp`, `jti`, `roles`, `permissions`, `sid` claims.
2. **Validated**: By resource servers on every API request. Validation checks: signature (JWKS), `exp` (not expired), `nbf` (not before), `aud` (correct audience), `jti` (not on revocation blocklist).
3. **Expired**: After 15 minutes. The `exp` claim is the authoritative expiry. No server-side cleanup is needed.
4. **Revoked early**: If revocation is triggered (logout, password change, admin action), the `jti` is written to the Redis revocation blocklist with a TTL equal to the remaining token lifetime. Resource servers check the blocklist on every validation.

### Refresh Token Lifecycle

Refresh tokens are opaque 256-bit random strings stored in Redis with a 30-day TTL. The lifecycle:

1. **Issued**: Alongside the access token after successful authentication. Stored in Redis with user ID, family ID, and expiry.
2. **Redeemed**: By the client via `POST /token?grant_type=refresh_token`. Single-use enforcement: the Token Refresh Service uses Redis `SET NX` to mark the token as consumed atomically.
3. **Rotated**: On every redemption, a new refresh token is issued and the old one is invalidated. The new token inherits the family ID of the original grant.
4. **Revoked on family reuse**: If a token in a family is redeemed after it has already been used (possible sign of token theft), all tokens in the family are revoked. The user is required to re-authenticate.
5. **Expired**: After 30 days. Redis TTL handles cleanup automatically.

## Configuration

| Config Key | Default | Description |
|-----------|---------|-------------|
| `ACCESS_TOKEN_TTL_MINUTES` | 15 | Access token expiry |
| `REFRESH_TOKEN_TTL_DAYS` | 30 | Refresh token expiry |
| `AUTHORIZATION_CODE_TTL_SECONDS` | 60 | Authorization code expiry |
| `REVOCATION_BLOCKLIST_KEY_PREFIX` | `revoked:` | Redis key prefix for access token blocklist |

## Dependencies

| Dependency | Purpose |
|-----------|---------|
| Redis 7 Cluster | Refresh token storage, authorization code storage, revocation blocklist |
| HashiCorp Vault | JWT signing key (RS256) storage and rotation |
| JWKS Endpoint | Public key distribution for resource server validation |

## Generation Notes

Generated from commit `b190ff5` on the `main` branch. The generator analyzed Go source files in the `auth-tokens` repository, extracting token store implementations and lifecycle state machine logic. Manual review is recommended for security-critical revocation semantics.
