---
id: REFERENCE-003
type: reference
title: OWASP Authentication Cheat Sheet Reference
status: published
owner: Security Team
created: '2024-05-30T19:13:28.377Z'
updated: '2026-11-12T00:33:10.509Z'
tags:
  - reference
  - user-authentication
summary: OWASP Authentication Cheat Sheet Reference
upstream_url: https://docs.example.com/owasp-authentication-cheat-sheet-reference
last_synced: '2026-02-08T08:12:17.269Z'
attribution: W3C
license: CC BY-SA 4.0
category: other
example: true
---

## Overview

The OWASP Authentication Cheat Sheet provides a concise reference for implementing secure authentication. This page summarizes the most relevant controls for the platform's authentication implementation and maps each control to its current implementation status. The original cheat sheet is maintained at [https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html).

The platform's authentication implementation is reviewed against this reference annually and during significant authentication system changes. Deviations from OWASP guidance require a documented exception with compensating controls.

## Password Storage

OWASP recommends using adaptive hashing algorithms with a work factor appropriate to prevent brute force attacks. The platform uses **bcrypt with cost factor 12**, which requires approximately 300ms per hash on current hardware. This meets the OWASP recommendation and provides 2^12 iterations of cost.

Key controls in the platform implementation:

- Passwords are never stored in plaintext; bcrypt hashes are stored in a separate schema with column-level encryption at rest
- Password hashing occurs on the application tier, not the database tier
- Password comparison uses constant-time comparison to prevent timing attacks
- Salt is generated per-password (bcrypt includes salt in the hash output)

## Authentication Protections

OWASP recommends multiple defenses against automated authentication attacks. The platform implements the following:

- **Rate limiting**: 10 failed attempts per 15 minutes per account; 30 requests per 10 minutes per IP address
- **Account lockout**: Temporary lockout (30 minutes) after rate limit breach; lockout notification sent to account email
- **CAPTCHA**: Progressive CAPTCHA challenge after 3 consecutive failures from the same IP
- **Credential stuffing detection**: Heuristic detection of distributed attacks across multiple accounts from multiple IPs
- **Secure password reset**: Tokens are random (256-bit), short-lived (15 minutes), single-use, and sent to the verified email only

## Multi-Factor Authentication

OWASP recommends MFA for all accounts. Platform status:

- TOTP (RFC 6238) — Implemented; 79.4% enrollment rate
- WebAuthn / FIDO2 — Implemented; passkeys and security keys supported
- SMS OTP — Implemented; OWASP notes SMS is the weakest MFA channel due to SIM-swap risk; platform has a roadmap to reduce SMS share
- Backup codes — Implemented; 8 single-use codes, hashed storage

## Session Management

OWASP session management controls and platform implementation status:

- Session IDs are cryptographically random (256-bit) — Implemented
- Sessions are regenerated on authentication (prevents session fixation) — Implemented
- Session cookies use HttpOnly, Secure, SameSite=Strict — Implemented
- Absolute timeout enforced (8 hours default) — Implemented
- Idle timeout enforced (30 minutes default) — Implemented
- Sessions are invalidated on logout (server-side deletion from Redis) — Implemented

## Transport Security

All authentication traffic uses TLS 1.2 or higher. TLS 1.0 and 1.1 are disabled. HTTP requests are redirected to HTTPS. The platform uses HSTS with a 1-year max-age and includeSubDomains. Certificate pinning is not used (mobile apps use platform certificate transparency monitoring instead).
