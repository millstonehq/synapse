---
id: TDD-006
type: tdd
title: Federated Identity Gateway TDD
status: review
owner: Principal Engineer
created: '2024-09-05T09:04:23.667Z'
updated: '2026-03-01T16:16:57.113Z'
tags:
  - tdd
  - user-authentication
summary: Federated Identity Gateway TDD
related_adrs:
  - ADR-0007
  - ADR-0008
example: true
---

## Summary

Design a Federated Identity Gateway that allows enterprise customers to authenticate users through their own identity providers (IdPs) via SAML 2.0 and OIDC, while issuing platform-standard JWTs as defined in [[ADR-0007|ADR-0007: Use JWTs Over Opaque Tokens]]. The gateway normalizes assertions from heterogeneous IdPs into a consistent claim set and enforces platform authentication policies including MFA step-up. This design implements the federated authentication capability required for enterprise SSO and supports the passwordless initiative described in [[ADR-0008|ADR-0008: Implement Passwordless Authentication]].

## Overview

The Federated Identity Gateway is a stateless service that sits between external identity providers and the platform's token issuance layer. It handles the SAML/OIDC protocol exchange, validates assertions, maps external claims to platform claims, and delegates token issuance to the OAuth Authorization Server.

Key design principles:
- **Protocol isolation**: SAML 2.0 and OIDC protocol handling is encapsulated in provider-specific adapters behind a common `IdentityAssertion` interface
- **Stateless federation**: No session state is held between IdP callbacks; state continuity is managed via signed request parameters
- **Claim normalization**: All IdP-specific claim formats are normalized to the platform claim schema before reaching the token issuance layer
- **Tenant isolation**: Each organization's IdP configuration is loaded per-request from a tenant registry; configuration changes take effect within 60 seconds

## Architecture

- **Protocol Adapters**: Separate adapters for SAML 2.0 (`internal/saml`) and OIDC (`internal/oidc`). SAML adapter handles SP-initiated and IdP-initiated flows, XML signature validation, and attribute mapping. OIDC adapter handles authorization code exchange, state/nonce validation, and ID token verification.
- **Claim Mapper**: Per-tenant claim mapping rules transform IdP-specific attribute names to platform claim names. Rules are stored in the tenant configuration database and cached in memory with a 60-second TTL.
- **Assertion Validator**: Validates assertion signature, expiry, audience, and destination. Enforces replay prevention using a Redis store for assertion IDs.
- **Token Bridge**: After claim normalization, calls the OAuth Authorization Server's token endpoint with a pre-validated assertion grant to receive a platform access token and refresh token.

## Information Model

- **TenantIdPConfig**: Tenant ID, protocol (SAML/OIDC), entity ID or issuer, metadata URL or inline metadata, claim mapping rules, MFA requirement
- **IdentityAssertion**: Normalized claims (sub, email, name, groups, custom attributes), issuer, issued-at, raw assertion for audit
- **FederationSession**: Short-lived (5-minute TTL) Redis record storing in-flight federation state (relay state, nonce, PKCE verifier) keyed by opaque state parameter
- **AssertionReplay**: Redis set of seen assertion IDs with TTL equal to assertion validity period

## Interfaces

- `POST /saml/acs` — SAML Assertion Consumer Service endpoint; receives IdP-initiated assertions and SP-initiated responses
- `GET /oidc/callback` — OIDC authorization code callback; exchanges code for tokens
- `GET /saml/metadata` — Serves SP metadata XML for IdP configuration
- `POST /admin/tenants/{id}/idp` — Admin API for registering and updating tenant IdP configurations
- `GET /admin/tenants/{id}/idp/test` — Admin API for testing IdP configuration before activation

## Files and Layout

```
federated-identity-gateway/
├── cmd/gateway/
│   └── main.go              # Entry point, dependency injection
├── internal/
│   ├── adapter/
│   │   ├── saml/            # SAML 2.0 SP adapter
│   │   └── oidc/            # OIDC RP adapter
│   ├── claims/
│   │   └── mapper.go        # Claim normalization and mapping
│   ├── validation/
│   │   └── assertion.go     # Assertion validation, replay prevention
│   ├── bridge/
│   │   └── token_bridge.go  # Delegates to OAuth Authorization Server
│   ├── tenant/
│   │   └── registry.go      # Tenant IdP config store and cache
│   └── handler/
│       ├── saml_handler.go
│       └── oidc_handler.go
└── deploy/
    ├── helm/                # Kubernetes Helm chart
    └── terraform/           # Infrastructure definitions
```

## Work Plan

1. **Phase 1 — OIDC adapter**: Implement OIDC RP flow (authorization code + PKCE), claim normalization, and token bridge. Deploy behind feature flag. Target: Week 2.
2. **Phase 2 — SAML adapter**: Implement SAML 2.0 SP-initiated flow, XML signature validation using `xmlsec`, and claim mapping. Target: Week 5.
3. **Phase 3 — Tenant admin API**: Implement IdP registration, metadata fetch, and configuration test endpoint. Target: Week 7.
4. **Phase 4 — IdP-initiated SAML**: Extend SAML adapter to support IdP-initiated flows. Target: Week 9.
5. **Phase 5 — Hardening**: Replay prevention, rate limiting per tenant, circuit breaker on metadata fetches. Load test and security review. Target: Week 11.
6. **Phase 6 — GA rollout**: Enable for all enterprise tenants. Monitor federation error rates and claim mapping coverage. Target: Week 12.

## Risks and Mitigations

- **Risk**: SAML 2.0 XML parsing is a historically high-risk attack surface (XXE, signature wrapping). Mitigation: Use a hardened SAML library (crewjam/saml) with XXE protection enabled; conduct a dedicated security review of the SAML adapter before Phase 3.
- **Risk**: Claim mapping rules may be incomplete for some IdPs, causing login failures. Mitigation: Provide a claim mapping test tool and a fallback that passes unmapped claims through as custom attributes.
- **Risk**: IdP metadata URLs may be slow or unavailable, causing login timeouts. Mitigation: Cache metadata aggressively (1-hour TTL) with a circuit breaker; allow inline metadata upload as a fallback.
- **Risk**: Per-tenant configuration cache invalidation could cause stale config to persist for up to 60 seconds after an update. Mitigation: Provide a manual cache invalidation endpoint for emergency config changes.
