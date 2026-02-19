---
id: ADR-0007
type: adr
title: Use JWTs Over Opaque Tokens
status: approved
owner: Staff Engineer
created: '2024-05-01T16:27:42.386Z'
updated: '2025-10-30T21:55:45.099Z'
tags:
  - adr
  - user-authentication
summary: Use JWTs Over Opaque Tokens
example: true
---

## Context

The platform's OAuth Authorization Server needs to issue access tokens to clients. We must choose between two approaches: self-contained JSON Web Tokens (JWTs) and opaque random tokens that require introspection. This decision affects performance, security properties, revocation semantics, and the complexity of resource server implementation.

Our system has approximately 40 internal microservices that act as resource servers validating tokens on every authenticated API call. At peak load, this represents approximately 5,000 token validations per second across the fleet. Several resource servers are latency-sensitive and cannot afford an additional network round-trip for introspection on every request.

We also have an active threat model that includes token theft. The security team requires that stolen tokens be revocable within seconds in high-risk scenarios (suspected breach, user-reported compromise). This is a harder requirement to satisfy with JWTs, which are stateless and cannot be revoked without a blocklist.

## Decision

We will use **RS256-signed JWTs** as access tokens with a short expiry (15 minutes) and a **token revocation blocklist** in Redis for high-priority revocations. Refresh tokens will remain opaque random strings stored in Redis.

The JWT signing key is a 2048-bit RSA key pair managed in HashiCorp Vault, rotated quarterly with a 7-day overlap period. Resource servers validate tokens locally using the JWKS endpoint, with a maximum 1-hour JWKS cache TTL. The Redis blocklist is checked on every validation via a synchronous Redis GET; the blocklist is expected to be sparse (only revoked tokens before expiry).

## Consequences

**Positive:**
- Resource servers validate tokens locally without a network call to the authorization server, enabling sub-millisecond validation at scale
- JWT claims (user ID, org, roles, permissions) are available directly in the token, eliminating separate user info lookups for most request types
- Industry-standard format with broad library support across all languages used in the platform

**Negative:**
- JWTs cannot be revoked before expiry without a blocklist; the 15-minute expiry window means compromised tokens remain valid up to 15 minutes after revocation unless the blocklist is consulted
- The Redis blocklist adds a synchronous dependency to every token validation — if Redis is unavailable, we must choose between failing open (security risk) or failing closed (availability risk)
- Token size is larger than opaque tokens (~500 bytes vs. ~32 bytes), increasing request header sizes

**Neutral:**
- The 15-minute access token expiry is a deliberate balance between security (short window for compromised tokens) and performance (fewer refresh calls)
- Refresh token rotation (rotate on use) is implemented to limit refresh token theft exposure

## Alternatives Considered

**Opaque tokens with introspection**:
- Pro: Instant revocation by deleting the token record; smaller token size; no blocklist complexity
- Con: Every token validation requires a network call to the introspection endpoint, adding 5-20ms of latency to every authenticated API call across 5,000 TPS — this is not acceptable for latency-sensitive services
- Rejected because: Introspection latency overhead at our scale is unacceptable

**Opaque tokens with local caching of introspection results**:
- Pro: Reduces introspection call frequency; effectively similar performance to JWTs
- Con: Cached introspection results have the same revocation delay problem as JWTs, but with more implementation complexity; cache invalidation on revocation requires a separate notification channel
- Rejected because: Adds complexity without a clear advantage over JWTs with a blocklist
