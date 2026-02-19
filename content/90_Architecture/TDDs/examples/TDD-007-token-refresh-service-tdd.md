---
id: TDD-007
type: tdd
title: Token Refresh Service TDD
status: approved
owner: Tech Lead
created: '2025-11-04T21:35:27.377Z'
updated: '2025-12-04T16:20:28.489Z'
tags:
  - tdd
  - user-authentication
summary: Token Refresh Service TDD
related_adrs:
  - ADR-0007
  - ADR-0009
example: true
---

## Summary

Design a Token Refresh Service that handles refresh token rotation, access token re-issuance, and refresh token revocation. The service implements the token lifecycle decisions from [[ADR-0007|ADR-0007: Use JWTs Over Opaque Tokens]] — refresh tokens are opaque, single-use, and stored in the session backend described in [[ADR-0009|ADR-0009: Choose Redis for Session Storage]]. The service must handle 500 refresh token redemptions per second at peak with sub-50ms P99 latency.

## Overview

The Token Refresh Service is a dedicated microservice extracted from the OAuth Authorization Server to isolate the high-frequency, latency-sensitive refresh token redemption path. Separating this concern allows independent scaling and simpler reasoning about the single-use enforcement logic.

Key design principles:
- **Single-use enforcement**: Each refresh token can be redeemed exactly once. Concurrent redemption attempts for the same token are handled with optimistic locking; the second attempt returns an error and triggers a family revocation (security measure against token theft).
- **Token family tracking**: Refresh tokens are organized into families (one per authorization grant). Reuse of a previously consumed token revokes all tokens in the family, providing theft detection.
- **Atomic rotation**: New refresh token issuance and old token invalidation occur in a single Redis transaction to prevent gaps or duplicates.

## Architecture

- **Redemption Handler**: Accepts `POST /token` with `grant_type=refresh_token`. Validates token existence and single-use state atomically using Redis `SET NX` (set-if-not-exists) to prevent concurrent redemption races.
- **Token Family Manager**: Tracks token lineage using Redis sets keyed by family ID. On suspicious reuse detection, calls the revocation endpoint to invalidate all family members.
- **Access Token Issuer**: Issues new RS256-signed JWTs with fresh claims fetched from the User Directory Service. Claims are cached per-user for 30 seconds to reduce User Directory load during burst refresh scenarios.
- **Refresh Token Generator**: Generates cryptographically random 256-bit tokens (base64url-encoded) and stores them in Redis with a 30-day TTL and family/user metadata.
- **Revocation Publisher**: Publishes revocation events to the token blocklist Redis set (as defined in ADR-0007) so that any access tokens issued from a revoked family are rejected at validation time.

## Information Model

- **RefreshToken**: Token string (opaque), user ID, family ID, parent token ID, issued-at, expiry, redeemed-at (null if not yet redeemed)
- **TokenFamily**: Family ID, user ID, root token ID, member token IDs, revoked-at (null if active)
- **AccessTokenClaims**: Cached claim set per user (sub, org_id, roles, permissions, mfa_amr) with 30-second TTL

## Interfaces

- `POST /token` (grant_type=refresh_token) — Redeem a refresh token; returns new access token and rotated refresh token
- `POST /token/revoke` — Revoke a refresh token (and optionally its entire family)
- `GET /token/introspect` — Check whether a refresh token is active (used by admin tooling)

## Files and Layout

```
token-refresh-service/
├── cmd/refresh/
│   └── main.go
├── internal/
│   ├── handler/
│   │   └── token_handler.go     # Redemption and revocation handlers
│   ├── redemption/
│   │   └── redeemer.go          # Single-use atomic redemption logic
│   ├── family/
│   │   └── manager.go           # Token family tracking and reuse detection
│   ├── issuer/
│   │   └── access_token.go      # JWT issuance with claim caching
│   ├── store/
│   │   └── redis_store.go       # Redis operations for token state
│   └── revocation/
│       └── publisher.go         # Blocklist publication
└── deploy/
    └── helm/
```

## Work Plan

1. **Phase 1 — Redis token store**: Implement token creation, single-use redemption (SET NX), and expiry. Unit tests for concurrent redemption. Target: Week 1.
2. **Phase 2 — Token family tracking**: Implement family ID assignment, lineage tracking, and reuse-triggered family revocation. Target: Week 2.
3. **Phase 3 — Access token issuance**: Integrate User Directory claim fetch with 30-second caching. JWT signing via Vault-managed keys. Target: Week 3.
4. **Phase 4 — Revocation blocklist publication**: Implement blocklist write on family revocation. Integration test with OAuth Authorization Server validation path. Target: Week 4.
5. **Phase 5 — Load testing and hardening**: Load test at 500 RPS, validate P99 < 50ms. Chaos test: Redis node failure during redemption. Target: Week 5.
6. **Phase 6 — Cutover**: Route refresh token redemption traffic from OAuth Authorization Server to this service. Monitor for 2 weeks before decommissioning old path. Target: Week 7.

## Risks and Mitigations

- **Risk**: Redis unavailability prevents all token refreshes. Mitigation: Circuit breaker that fails fast (3s timeout); access tokens have 15-minute expiry, providing a grace window during brief Redis outages.
- **Risk**: Concurrent redemption race during network retry could trigger false family revocation. Mitigation: SET NX with a 5-second expiry on the redemption lock; retried requests within 5 seconds return a 429 rather than triggering revocation.
- **Risk**: Token family reuse detection generates false positives for mobile clients on poor networks. Mitigation: Log reuse events and monitor for false positive rate before auto-revocation; initial phase will alert-only.
