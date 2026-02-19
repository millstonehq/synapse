---
id: CAPABILITY-005
type: capability
title: Authentication Security Capability
status: proposed
owner: VP Engineering
created: '2025-05-24T17:37:14.233Z'
updated: '2026-11-01T18:19:13.066Z'
tags:
  - capability
  - user-authentication
summary: Authentication Security Capability
evidence_links:
  - STANDARD-012
  - STANDARD-009
  - STANDARD-010
example: true
---

## Domain

- Credential security (password hashing, storage, breach detection)
- Multi-factor authentication (TOTP, SMS OTP, WebAuthn, backup codes)
- Brute force and credential stuffing protection (rate limiting, CAPTCHA, lockout)
- Token security (JWT signing key management, rotation, revocation)
- Session security (HttpOnly/Secure cookies, CSRF protection, session fixation prevention)

## Maturity (0-5)

- Credential security: 4/5 - Passwords hashed with bcrypt (cost 12); breach detection via HIBP blocklist on password set; no proactive credential exposure monitoring (e.g., dark web monitoring) yet
- Multi-factor authentication: 4/5 - TOTP, SMS OTP, WebAuthn, and backup codes supported; adaptive MFA (risk-based challenge decisions) in PRD stage
- Brute force protection: 3/5 - Per-IP and per-account rate limiting implemented; CAPTCHA on login page; org-level rate limits not yet shipped
- Token security: 4/5 - RS256 JWT signing with quarterly key rotation; 15-minute access token TTL; revocation blocklist in Redis; JWKS endpoint for public key distribution
- Session security: 4/5 - HttpOnly/Secure/SameSite=Strict cookies; CSRF protection via state parameter in OAuth flows; concurrent session limits enforced; session hijacking protection via device fingerprint binding (in development)

## Metrics

- JWT key rotation frequency: quarterly (target: quarterly minimum)
- MFA enrollment rate: 79.4% of active users
- Credential stuffing blocked per day: ~12,000 attempts (rate limiting + CAPTCHA)
- Account lockout rate: 0.01% of DAU (low false positive rate)
- Time to revoke a compromised token: < 30 seconds (blocklist propagation to all Redis nodes)

## Evidence Links

- [[STANDARD-012|MFA Requirements Standard]] — Standard defining required MFA controls
- [[STANDARD-009|Authentication Credential Standard]] — Standard for password and credential requirements
- [[STANDARD-010|Token Security Standard]] — Standard for JWT and session token security properties

## Notes

- SMS OTP remains in use for 39% of MFA-enrolled users; SIM-swap vulnerability is a known risk; SMS reduction roadmap is being developed
- Dark web credential monitoring is not implemented; this is a gap in the credential security maturity score
- WebAuthn passkey adoption growing from 9%; expected to become the dominant factor within 18 months
