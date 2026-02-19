---
id: TDD-010
type: tdd
title: Auth Rate Limiter TDD
status: approved
owner: Senior Engineer
created: '2024-04-27T22:41:40.250Z'
updated: '2025-12-23T17:17:25.939Z'
tags:
  - tdd
  - user-authentication
summary: Auth Rate Limiter TDD
related_adrs:
  - ADR-0007
  - ADR-0009
example: true
---

## Summary

Design a layered rate limiting system for the authentication service that protects against credential stuffing, brute force attacks, and denial-of-service via authentication endpoints. The rate limiter uses Redis (as specified in [[ADR-0009|ADR-0009: Choose Redis for Session Storage]]) for distributed counter storage and integrates into the request pipeline upstream of token issuance (covered by [[ADR-0007|ADR-0007: Use JWTs Over Opaque Tokens]]). The design supports three limit scopes: per-IP, per-account, and per-organization.

## Overview

The Auth Rate Limiter is a middleware component that applies sliding window rate limits at multiple scopes before authentication logic is executed. Using a sliding window algorithm (as opposed to a fixed window) prevents burst exploitation at window boundaries.

Key design principles:
- **Layered limits**: IP limits catch volumetric attacks from individual hosts; account limits prevent targeted brute force; org limits prevent attackers from distributing attacks across many accounts in one org
- **Sliding window via Redis sorted sets**: Each rate limit window is implemented as a Redis sorted set (sorted by timestamp); old entries are pruned atomically to maintain the window
- **Fail-open on Redis unavailability**: If Redis is unreachable, rate limiting is disabled and requests are allowed through to preserve availability; an alert fires immediately
- **Lockout with exponential backoff**: After exceeding the account rate limit, subsequent attempts are rejected with increasing delay headers to signal the expected retry window

## Architecture

- **IP Rate Limiter**: Per-IP address (or /24 subnet for shared IPs), sliding window of 30 requests per 10 minutes. Uses Redis sorted set keyed by `ratelimit:ip:{ip_address}`. Returns 429 with `Retry-After` header on breach.
- **Account Rate Limiter**: Per-account (email/user ID), sliding window of 10 failed attempts per 15 minutes. Triggered only on failed authentication; successful logins do not consume account quota. Lockout is account-specific (does not block other accounts from the same IP).
- **Org Rate Limiter**: Per-organization, sliding window of 500 authentication attempts per minute. Protects against distributed attacks targeting many accounts within one enterprise org. Applied at the SAML/OIDC callback level for SSO flows.
- **Allowlist**: IP allowlist for internal service accounts and known-good partner IPs. Stored in Redis as a set; bypasses all rate limits.
- **Rate Limit Headers**: All responses include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers per RFC 6585 conventions.

## Information Model

- **RateLimitWindow**: Key (scope + identifier), sorted set of request timestamps, window duration, limit count
- **RateLimitDecision**: Allowed (bool), remaining quota, reset time, scope that triggered the limit (if denied)
- **AllowlistEntry**: IP or CIDR range, label, added-by, added-at, expiry (null for permanent)
- **RateLimitViolation**: Scope, identifier, limit, actual count, timestamp, source IP, user agent (for security monitoring)

## Interfaces

- Rate limiting is applied as middleware via a `RateLimitMiddleware(handler http.Handler) http.Handler` function — not an external endpoint
- `GET /admin/ratelimit/allowlist` — List IP allowlist entries
- `POST /admin/ratelimit/allowlist` — Add an IP or CIDR to the allowlist
- `DELETE /admin/ratelimit/allowlist/{id}` — Remove an allowlist entry
- `GET /admin/ratelimit/status?identifier=` — Check current rate limit state for a given identifier (for support tooling)
- `POST /admin/ratelimit/reset?identifier=` — Reset rate limit counters for an identifier (for support tooling, requires elevated auth)

## Files and Layout

```
auth-service/
└── internal/
    ├── ratelimit/
    │   ├── middleware.go          # HTTP middleware integration point
    │   ├── ip_limiter.go          # Per-IP sliding window
    │   ├── account_limiter.go     # Per-account failed attempt tracking
    │   ├── org_limiter.go         # Per-org sliding window
    │   ├── allowlist.go           # IP/CIDR allowlist management
    │   ├── store.go               # Redis sorted set operations
    │   └── headers.go             # RFC 6585 response header generation
    └── handler/
        └── ratelimit_admin.go     # Admin API for allowlist and status
```

## Work Plan

1. **Phase 1 — Redis sorted set store**: Implement the core sliding window algorithm in Redis (ZADD + ZREMRANGEBYSCORE + ZCARD in a pipeline). Unit tests with mock Redis. Target: Week 1.
2. **Phase 2 — IP rate limiter**: Implement per-IP limiter with /24 subnet aggregation and `Retry-After` header. Target: Week 1.
3. **Phase 3 — Account rate limiter**: Implement per-account failed attempt limiter with exponential lockout headers. Requires integration with the authentication result to distinguish success vs. failure. Target: Week 2.
4. **Phase 4 — Org rate limiter**: Implement per-org limiter for SSO flows. Target: Week 2.
5. **Phase 5 — Allowlist and admin API**: Implement IP allowlist with Redis backing and admin management endpoints. Target: Week 3.
6. **Phase 6 — Load testing and tuning**: Validate rate limit accuracy under 2,000 RPS. Tune window sizes and limits based on observed legitimate traffic patterns. Target: Week 4.

## Risks and Mitigations

- **Risk**: Redis unavailability disables rate limiting, exposing endpoints to brute force. Mitigation: Alert immediately on Redis unavailability; the fail-open behavior is a documented, deliberate tradeoff favoring availability; investigate adding an in-memory fallback for the IP limiter only.
- **Risk**: Overly aggressive account limits lock out legitimate users (e.g., users who fat-finger password on multiple devices simultaneously). Mitigation: 10-attempt threshold over 15 minutes is conservative; monitor lockout rate in the first month and adjust threshold if false-positive rate exceeds 0.1% of daily active users.
- **Risk**: Attackers use IPv6 addresses to bypass /24 subnet aggregation. Mitigation: Extend subnet aggregation to /48 for IPv6; monitor IPv6 traffic share and refine if needed.
