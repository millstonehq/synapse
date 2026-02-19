---
id: PRD-006
type: prd
title: Passwordless Authentication PRD
status: approved
owner: Product Manager
created: '2025-02-03T22:25:04.463Z'
updated: '2026-12-15T02:58:06.658Z'
tags:
  - prd
  - user-authentication
summary: Passwordless Authentication PRD
related_tdds:
  - TDD-007
  - TDD-009
example: true
related_standards:
  - STANDARD-009
---

## Summary

Passwordless Authentication eliminates the need for users to create and remember passwords by providing magic link (email) and passkey (WebAuthn) login options. This feature reduces account takeover risk by removing the password attack surface and improves login conversion by reducing credential-related friction.

The initiative targets all user tiers. Passwordless will be available as an opt-in initially, with a path to making it the recommended default for new sign-ups within 12 months.

## Goals

- Reduce password-related account takeovers by 70% among enrolled users within 6 months of GA
- Improve new user sign-up conversion by 15% by reducing password creation friction
- Achieve 50% voluntary adoption of passwordless login among active users within 12 months
- Eliminate password reset support tickets for passwordless-enrolled users

## In Scope

- Magic link login via verified email address (15-minute expiry, single-use)
- WebAuthn passkey login for supported browsers and operating systems
- Opt-in enrollment UI in user account settings
- Post-enrollment prompt on next login for users who have not enrolled
- Passkey management (view, rename, remove registered passkeys)
- Fallback to magic link when passkey is unavailable on current device
- Admin console visibility into passwordless adoption rates per organization

## Out of Scope

- SMS OTP as a passwordless sole factor (security decision; see ADR-0008)
- Forced migration of existing users to passwordless in this phase
- Passwordless for service accounts or API keys
- Magic link login for users without a verified email address

## Users and Flows

End users (both free tier and paid) interact with passwordless through the login and sign-up flows. A user who has enrolled in passwordless sees a "Send me a link" button on the login page instead of a password field. They receive an email with a one-click login link that opens a browser session and completes authentication without any further input.

Enterprise users with passkeys registered can authenticate by clicking "Use passkey" on the login page and completing the biometric or PIN challenge on their device. The experience is particularly streamlined on mobile, where the platform passkey is available via Face ID, Touch ID, or device PIN.

Admin users in the organization management console can view passwordless adoption metrics (percentage of users enrolled, login method breakdown) and optionally enforce passwordless as a requirement for their organization.

## Requirements

- The magic link must be a single-use, time-limited URL containing a signed JWT with a Redis-backed nonce for replay prevention
- Magic link expiry is 15 minutes; the user is shown the remaining time and can request a new link
- WebAuthn passkey registration must follow FIDO2 Level 2 requirements
- Users must have a verified email address to enable magic link login
- Users can have multiple passkeys registered (for different devices)
- Removing the last passkey when no password is set must prompt the user to set a password first or add another factor
- Rate limiting must prevent more than 3 magic link requests per email address per 10 minutes
- All passwordless authentication events must be logged with IP address and user agent
- The feature must be controllable via a feature flag at the organization level for gradual rollout

## KPIs

- **Passwordless adoption rate**: Target 50% of active users enrolled within 12 months of GA
- **Magic link success rate**: Target > 98% of issued links successfully redeemed (measures email delivery and UX quality)
- **Passkey success rate**: Target > 99.5% of passkey authentication attempts succeed
- **Account takeover reduction**: Target 70% reduction in ATO incidents among passwordless-enrolled users

## Information Architecture

- User account settings page: /settings/security — passwordless enrollment and passkey management
- Admin console: /admin/organizations/{id}/security — org-level passwordless adoption metrics and policy
- API: POST /auth/passwordless/initiate, POST /auth/passwordless/magic-link/redeem, POST /auth/passwordless/webauthn/challenge, POST /auth/passwordless/webauthn/verify
- Technical design: [[TDD-009|Passwordless Login Flow TDD]], [[TDD-007|Token Refresh Service TDD]]

## Data Model

- **PasskeyCredential**: credential_id, user_id, public_key, sign_count, registered_at, last_used_at, device_name
- **MagicLinkNonce**: nonce, user_id, issued_at, expires_at, redeemed_at, source_ip
- **PasswordlessEnrollment**: user_id, methods_enrolled (array), enrolled_at, last_passwordless_login_at

## Non-Functional

- Magic link email must be delivered within 30 seconds in P90 of cases
- Passkey authentication must add no more than 200ms to P99 login latency
- System must support 10,000 concurrent magic link requests without degradation
- Magic link nonce store must be backed up; loss of Redis data means issued but unredeemed links become invalid (acceptable, user can request a new link)

## Constraints

- Magic links must use HTTPS exclusively; HTTP links must redirect to HTTPS before nonce redemption
- WebAuthn origin binding means passkeys are non-transferable between environments (prod/staging)
- Magic link emails must include plain-text alternative for email clients that block HTML

## Risks

- **Risk**: Low email deliverability causes magic links to land in spam folders, degrading conversion. Mitigation: Use a dedicated "authentication" sending domain with strict SPF/DKIM/DMARC; monitor delivery rates via SendGrid webhooks.
- **Risk**: Browser/OS passkey support inconsistency causes failures for some users. Mitigation: Always offer magic link as a fallback; instrument browser capability detection to identify unsupported environments.
- **Risk**: Users who enroll in passwordless and lose access to their email account cannot log in. Mitigation: Enforce email verification before enabling passwordless; prompt users to add a passkey as a second-factor backup.
- **Risk**: 15-minute magic link window is too short for users with slow email delivery. Mitigation: Email is typically delivered in < 30 seconds; the 15-minute window provides 30x headroom; link can be re-requested if expired.

## Milestones

### M1: Magic Link Beta (Month 1-2)
#### Deliverables
- Magic link generation, delivery, and redemption backend
- Opt-in enrollment UI in account settings
- Feature flag for internal users only
- Monitoring dashboard for magic link delivery and redemption rates

#### Acceptance Criteria
- Magic link P90 delivery time < 30 seconds in production
- Single-use enforcement validated: redeemed links rejected on replay
- 0 new login paths that bypass rate limiting

### M2: Passkey Support + Public Beta (Month 3-4)
#### Deliverables
- WebAuthn passkey registration and authentication
- Passkey management UI (view, rename, delete)
- Fallback to magic link when passkey unavailable
- Expanded beta to 10,000 volunteer users

#### Acceptance Criteria
- Passkey authentication success rate > 99.5% in beta
- Passkey flow works on Chrome, Safari, Firefox, and iOS/Android native browsers
- Magic link adoption rate > 40% among beta users after 2 weeks

### M3: General Availability (Month 5)
#### Deliverables
- Remove beta flag; available to all users
- Post-login enrollment prompt for unenrolled users
- Admin console passwordless adoption metrics
- Updated support documentation and help center articles

#### Acceptance Criteria
- Passwordless available to 100% of users
- Enrollment rate among prompted users > 25%
- Zero P1/P2 incidents in first 2 weeks post-GA
