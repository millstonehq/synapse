---
id: WIKI-006
type: wiki
title: OAuth Flow - Implementation Details
status: approved
owner: User Team
created: '2025-10-14T21:10:23.553Z'
updated: '2025-09-24T07:23:08.697Z'
tags:
  - wiki
  - user-authentication
summary: OAuth Flow - Implementation Details
source_repo: https://git.example.com/acme/oauth-flow
commit_sha: 40629147e9e1585be16a0b217e0dc68eecdb981e
generated_at: '2025-01-02T20:09:05.593Z'
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
importance: high
example: true
---

## Overview

This page documents the implementation details of the OAuth 2.1 Authorization Code Flow with PKCE as implemented in the `oauth-flow` repository. It covers the entry point, key packages, state management, and token issuance logic. The implementation conforms to RFC 9700 (OAuth 2.1 draft) and RFC 7636 (PKCE).

This page was auto-generated from repository analysis. For the authorization server system overview, see the OAuth Authorization Server system doc. For the original design rationale, see the related ADRs.

## Entry Point

`cmd/oauth-server/main.go` initializes the HTTP server with the following startup sequence:

1. Load configuration from environment variables and validate required fields
2. Initialize Redis connection pool for authorization code and state storage
3. Load JWT signing keys from HashiCorp Vault (RS256, 2048-bit RSA)
4. Initialize JWKS cache with background refresh on a 1-hour interval
5. Register route handlers: `/authorize`, `/token`, `/introspect`, `/userinfo`, `/.well-known/openid-configuration`, `/.well-known/jwks.json`
6. Start HTTP server on `:8080` with a 30-second graceful shutdown timeout

## Key Packages

### `internal/handler/authorize`

Handles `GET /authorize` requests. Validates required OAuth parameters (response_type, client_id, redirect_uri, scope, state, code_challenge, code_challenge_method). On success, redirects the user to the login service with a signed request context. On error, returns an OAuth error response to the redirect URI.

### `internal/handler/token`

Handles `POST /token` requests. Supports `authorization_code`, `refresh_token`, and `client_credentials` grant types. For `authorization_code`: validates the authorization code from Redis, verifies PKCE code_verifier against stored code_challenge, issues access token and refresh token. Codes are single-use and deleted on first exchange.

### `internal/token`

JWT issuance and validation logic:

```go
type TokenClaims struct {
    Sub       string   `json:"sub"`
    Aud       []string `json:"aud"`
    Scope     string   `json:"scope"`
    ClientID  string   `json:"client_id"`
    SessionID string   `json:"sid"`
}
```

Access tokens are RS256-signed JWTs with a 15-minute expiry. Refresh tokens are opaque random strings stored in Redis with a 30-day expiry and single-use enforcement.

### `internal/client`

Registered OAuth client definitions loaded from a database at startup. Clients have defined redirect URI allowlists, allowed grant types, and token lifetime overrides.

## Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| `github.com/go-jose/go-jose/v3` | v3.0.3 | JWT signing and validation |
| `github.com/redis/go-redis/v9` | v9.3.0 | Authorization code and refresh token storage |
| `github.com/hashicorp/vault/api` | v1.12.0 | Signing key retrieval |
| `github.com/prometheus/client_golang` | v1.18.0 | Metrics instrumentation |

## Generation Notes

Generated from commit `4062914` on the `main` branch. The generator analyzed Go source files and extracted package structure and interface definitions. Manual review is recommended for security-critical token validation logic.
