---
id: ADR-0008
type: adr
title: Implement Passwordless Authentication
status: approved
owner: Tech Lead
created: '2025-11-19T10:41:56.627Z'
updated: '2025-03-10T08:35:25.981Z'
tags:
  - adr
  - user-authentication
summary: Implement Passwordless Authentication
example: true
---

## Context

Password-based authentication is the dominant source of account compromise on the platform. An analysis of security incidents over the past 12 months shows that 78% of account takeovers involved stolen or reused passwords. The platform's current credential stuffing mitigation (rate limiting + CAPTCHA) reduces automated attacks but does not address the underlying vulnerability of password reuse.

Additionally, user research shows that password friction is the leading cause of checkout abandonment and sign-up drop-off. 31% of users who begin registration abandon before completing it, and exit surveys cite password creation requirements as the top frustration.

The security team and product team have independently identified passwordless authentication as a priority: security wants to eliminate password-based account compromise, and product wants to reduce sign-up and login friction. This decision documents our chosen approach.

We evaluated three passwordless approaches: magic links (email OTP), WebAuthn passkeys, and SMS OTP as sole factor. Each has different tradeoffs for security, usability, and delivery reliability.

## Decision

We will implement **magic links (email OTP)** as the primary passwordless method with **WebAuthn passkeys** as the preferred secure alternative for users who opt in. SMS OTP will not be offered as a passwordless sole factor due to SIM-swap vulnerability.

Magic links: A time-limited (15-minute), single-use URL containing a signed JWT is sent to the user's verified email address. The link contains a `nonce` claim that is validated against a Redis store on redemption, providing single-use enforcement.

Passkeys: WebAuthn Level 2 credentials stored on the user's device/platform (not a hardware token). The MFA Gateway Service's existing WebAuthn implementation will be extended to support passkey-based primary authentication.

Existing password-based authentication remains available and is not deprecated. Users may opt into passwordless and can revert at any time.

## Consequences

**Positive:**
- Eliminates password-based account takeover for enrolled users
- Reduced login friction expected to improve sign-up conversion and returning-user login time
- Passkeys are phishing-resistant by design (WebAuthn origin binding)
- No new infrastructure required: magic links use the existing email delivery pipeline; passkeys use the existing WebAuthn implementation in the MFA Gateway

**Negative:**
- Magic link delivery depends on email deliverability; users with unreliable email access will have degraded experience
- Magic link security is bounded by the user's email account security; a compromised email account can be used to authenticate
- Passkey adoption will be slow initially; requires user education and a fallback path for lost devices
- Increased complexity in the authentication flow state machine (more pathways to test and maintain)

**Neutral:**
- Password-based authentication remains available; adoption of passwordless is voluntary
- Users must have a verified email address to use magic links; this is already required for account creation

## Alternatives Considered

**SMS OTP as sole factor**:
- Pro: Simple implementation, familiar to users
- Con: Vulnerable to SIM-swap attacks; SMS delivery reliability issues already documented in POSTMORTEM-007; not recommended by NIST SP 800-63B for new implementations
- Rejected because: Security posture is worse than current password + MFA for users who already have MFA enrolled

**Passkeys only (no magic links)**:
- Pro: Highest security (phishing-resistant); no email dependency
- Con: Passkey adoption is still nascent; users on older devices or shared devices cannot use passkeys; forcing passkeys would reduce accessibility
- Rejected because: Too restrictive for broad rollout; magic links provide a universally accessible passwordless option
