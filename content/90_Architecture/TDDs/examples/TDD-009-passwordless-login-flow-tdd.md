---
id: TDD-009
type: tdd
title: Passwordless Login Flow TDD
status: draft
owner: Principal Engineer
created: '2025-08-16T17:46:40.317Z'
updated: '2026-08-06T16:32:54.090Z'
tags:
  - tdd
  - user-authentication
summary: Passwordless Login Flow TDD
related_adrs:
  - ADR-0007
  - ADR-0008
example: true
---

## Summary

Design the end-to-end passwordless login flow that implements magic links and passkey authentication as decided in [[ADR-0008|ADR-0008: Implement Passwordless Authentication]]. The flow produces platform access tokens as specified in [[ADR-0007|ADR-0007: Use JWTs Over Opaque Tokens]]. This TDD covers the state machine, security properties, and implementation of both the magic link and WebAuthn passkey pathways.

## Overview

Passwordless login replaces the password collection step with either a magic link sent to a verified email address or a WebAuthn passkey assertion. Both pathways converge on the same token issuance path used by password-based authentication.

Key design principles:
- **Single-use enforcement**: Magic links contain a signed nonce that is consumed on first use; replayed links return an error
- **Short-lived challenge window**: Magic links expire in 15 minutes; WebAuthn challenges expire in 5 minutes
- **Device continuity**: Successful passkey authentication registers the device credential in the user's profile, enabling seamless re-authentication on the same device
- **Graceful degradation**: If magic link delivery fails, the user is shown a retry option; if WebAuthn is unavailable, a fallback to magic link is offered automatically

## Architecture

- **Login Initiation Handler**: Accepts the user's email, looks up the account, determines the preferred passwordless method (passkey if registered, magic link if not), and initiates the appropriate challenge.
- **Magic Link Generator**: Creates a signed JWT with `nonce`, `user_id`, `exp` (15 minutes), and `typ: magic-link` claims. Stores the nonce in Redis with a 15-minute TTL. Dispatches the link via the email delivery service.
- **Magic Link Redemption Handler**: Validates the magic link JWT signature and expiry, verifies the nonce against Redis (single-use), and proceeds to session and token issuance.
- **WebAuthn Challenge Handler**: Issues a WebAuthn authentication challenge (random 32-byte challenge, 5-minute TTL in Redis) for the user's registered credential public keys.
- **WebAuthn Assertion Handler**: Validates the WebAuthn assertion (signature, challenge binding, origin, counter), then proceeds to token issuance.
- **Token Issuance Bridge**: Shared component used by both pathways to create a session in the Session Management Service and issue access + refresh tokens via the OAuth Authorization Server.

## Information Model

- **MagicLinkNonce**: Nonce string (32-byte random), user ID, issued-at, redeemed-at, IP address at issuance
- **WebAuthnChallenge**: Challenge bytes (32-byte random), user ID, credential IDs (to limit assertion to registered keys), issued-at, expiry
- **PasskeyCredential**: Credential ID (WebAuthn), user ID, public key (COSE format), sign count, registered-at, last-used-at, device name
- **PasswordlessAttemptLog**: User ID, method (magic-link/passkey), outcome (success/failure/expired), IP, user agent, timestamp

## Interfaces

- `POST /auth/passwordless/initiate` — Start a passwordless login; returns method type and delivery confirmation
- `POST /auth/passwordless/magic-link/redeem` — Redeem a magic link token; returns authorization code for token exchange
- `POST /auth/passwordless/webauthn/challenge` — Get a WebAuthn authentication challenge for a user's registered credentials
- `POST /auth/passwordless/webauthn/verify` — Verify a WebAuthn assertion; returns authorization code for token exchange
- `GET /auth/passkeys` — List registered passkeys for the authenticated user
- `DELETE /auth/passkeys/{id}` — Remove a registered passkey

## Files and Layout

```
auth-service/
└── internal/
    ├── passwordless/
    │   ├── initiator.go          # Login initiation, method selection
    │   ├── magic_link/
    │   │   ├── generator.go      # Nonce generation and link signing
    │   │   └── redeemer.go       # Nonce validation and redemption
    │   ├── webauthn/
    │   │   ├── challenger.go     # Challenge generation
    │   │   └── asserter.go       # Assertion validation
    │   └── token_bridge.go       # Session + token issuance after verification
    └── handler/
        └── passwordless_handler.go
```

## Work Plan

1. **Phase 1 — Magic link generation and delivery**: Implement nonce generation, JWT signing, Redis storage, and email dispatch. Unit tests for nonce single-use enforcement. Target: Week 2.
2. **Phase 2 — Magic link redemption and token issuance**: Implement redemption handler, token bridge integration, and session creation. End-to-end test of full magic link flow. Target: Week 3.
3. **Phase 3 — WebAuthn challenge and assertion**: Implement WebAuthn challenge generation and assertion validation using the existing MFA Gateway WebAuthn library. Target: Week 5.
4. **Phase 4 — Passkey management API**: Implement passkey registration, listing, and deletion endpoints. Target: Week 6.
5. **Phase 5 — Beta rollout**: Enable for 500 internal users behind a feature flag. Instrument attempt rates, success rates, and delivery latency. Target: Week 7.
6. **Phase 6 — GA**: Remove feature flag after 2-week stable beta period. Target: Week 10.

## Risks and Mitigations

- **Risk**: Magic link email delivery delays cause poor user experience and support tickets. Mitigation: Implement a "resend link" option that rate-limits to 1 resend per minute; monitor email delivery latency via SendGrid webhooks.
- **Risk**: Magic link JWTs leaked via email forwarding or log exposure. Mitigation: 15-minute TTL limits exposure window; single-use enforcement prevents replay; links are HTTPS-only with SameSite cookie binding.
- **Risk**: WebAuthn sign counter validation fails for users with multiple synced passkeys. Mitigation: Follow FIDO2 recommendation to treat counter = 0 as a valid passkey-type credential and skip counter enforcement for synced credentials.
