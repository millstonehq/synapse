---
id: GUIDE-062
type: guide
title: Migrating to Passwordless Authentication Guide
status: draft
owner: Developer Experience
created: '2024-09-11T21:58:16.994Z'
updated: '2026-10-12T13:40:44.544Z'
tags:
  - guide
  - user-authentication
summary: Migrating to Passwordless Authentication Guide
audience: partner
related_systems:
  - SYSTEM-010
  - SYSTEM-006
related_sops:
  - SOP-017
  - SOP-014
example: true
---

## Why Migrate to Passwordless

Passwords are the leading source of account compromise. They are reused across services, phished in social engineering attacks, and exposed in third-party data breaches. Migrating your users to passwordless authentication — magic links or passkeys — eliminates the password attack surface entirely for enrolled users.

Beyond security, passwordless authentication improves user experience. Users no longer need to remember complex passwords, and the login journey is faster: a magic link click or a biometric gesture replaces password entry plus MFA challenge. Early data from our beta shows a 22% improvement in sign-up conversion for flows that use magic links.

This guide walks through the steps to migrate an existing application from password-based authentication to passwordless, covering both the technical integration changes and the user migration strategy.

## Prerequisites

Before beginning the migration, ensure the following are in place:

- All users have a verified email address on their account. Magic links are delivered to the verified email and cannot be used without one.
- Your application uses the platform's standard OAuth 2.1 authorization code flow. Passwordless authentication is initiated via the same `/authorize` endpoint with an additional `login_hint=passwordless` parameter.
- You have tested the passwordless flow in the staging environment with the test accounts provided in the authentication test suite.
- Your application handles the "session expired" state gracefully, since passwordless sessions expire on the same schedule as password-based sessions.

## Step-by-Step Migration

Follow these steps to add passwordless as an option (not a replacement) for your users:

1. **Enable the passwordless feature flag**: In the Organization Security Settings, navigate to Authentication Methods and enable Passwordless. This makes the option available to your users but does not enforce it.

2. **Update your login page**: Add a "Send me a login link" button alongside your existing password form. This button should initiate the passwordless flow. The button text should be clear: avoid jargon like "magic link" in the user-facing UI.

3. **Integrate the magic link initiation endpoint**: When the user clicks the passwordless button, call `POST /auth/passwordless/initiate` with the user's email. The response confirms that a link has been sent (or that the email was not found — same message to prevent enumeration).

4. **Handle the magic link callback**: Magic links redirect to your application's `redirect_uri` with an authorization code, just like the standard OAuth flow. Your existing token exchange code requires no changes — use the same `POST /token` call with `grant_type=authorization_code`.

5. **Add passkey registration (optional)**: After a user's first passwordless login, prompt them to register a passkey for future logins. Passkeys eliminate even the email step. Call `POST /auth/passwordless/webauthn/challenge` and handle the browser's `navigator.credentials.create()` response.

6. **Communicate the change to users**: Send an email campaign explaining the new login option. Highlight the security and convenience benefits. Link to a help article that explains what passwordless is and what to do if they don't receive a link.

## Common Questions

**What if a user doesn't receive the magic link?**
The login page should include a "Resend link" button that sends a new link (rate-limited to once per minute). The old link is invalidated when a new one is issued. In rare cases, email deliverability issues may delay the link; advise users to check their spam folder and add the sending domain to their safe senders list.

**Can users still use their password after enabling passwordless?**
Yes. Passwordless is an additional login method, not a replacement, unless you explicitly enforce passwordless-only in your organization policy. Users can choose between methods on the login page.

**What happens if a passkey user gets a new device?**
Passkeys registered on one device are not automatically available on a new device (unless synced via iCloud Keychain or Google Password Manager). Users should register passkeys on each new device. They can always fall back to magic link login if they have not registered a passkey on the current device.

## Next Steps

- Review the Passwordless Authentication PRD for the full feature scope
- Read the Passwordless Login Flow TDD for technical implementation details
- Contact the Developer Experience team in #platform-auth if you encounter integration issues
- Once you've validated passwordless in staging, use the organization policy settings to optionally enforce passwordless for new users while grandfathering existing password users
