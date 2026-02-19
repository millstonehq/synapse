---
id: FLOW-005
type: flow
title: User Login Flow
status: approved
owner: QA Lead
created: '2025-12-29T21:37:23.525Z'
updated: '2026-06-12T21:45:49.458Z'
tags:
  - flow
  - user-authentication
summary: User Login Flow
feature_area: User Authentication
related_prds:
  - PRD-009
example: true
---

## Steps

### Step 1: Enter Email Address

The user navigates to the login page and enters their email address. The system looks up the account associated with the email to determine which authentication pathway applies. If the organization has SSO enforcement configured (see [[PRD-009|SSO Self-Service Configuration PRD]]), the user is redirected to the SSO flow instead of the credential entry page. If the email matches no account, a generic "check your email" message is shown to prevent user enumeration.

### Step 2: Credential Verification

For password-based login, the user enters their password. The system validates the credential against the stored hash (bcrypt, cost 12). On failure, the failed attempt counter is incremented. After 10 failed attempts within 15 minutes, the account is temporarily locked and the user is directed to the password reset flow. On success, the system checks whether multi-factor authentication is required.

### Step 3: MFA Challenge

If the user has MFA enrolled and the risk score (from Adaptive MFA) indicates a challenge is required, the user is presented with their preferred factor challenge — TOTP code, SMS OTP, email OTP, or WebAuthn assertion. The user has 60 seconds to complete a TOTP/OTP challenge or 5 minutes for WebAuthn. Failed challenges increment a separate MFA attempt counter. On successful MFA completion, the flow proceeds to session creation.

### Step 4: Session and Token Issuance

The authentication service calls the Session Management Service to create a new session record. The session token is set as an HttpOnly, Secure, SameSite=Strict cookie. The OAuth Authorization Server issues an access token (15-minute JWT) and a refresh token (30-day opaque token). The user is redirected to their intended destination or the default dashboard.

### Step 5: Post-Login Enrollment Prompt

If the user successfully logs in but has not enrolled in MFA, they are shown a non-blocking prompt recommending MFA enrollment. If the organization has an MFA enforcement policy with a grace period that has not yet expired, the prompt is more prominent and includes a countdown to the enforcement date. Users who dismiss the prompt are shown it again on their next login.

## Expected Results

- User is authenticated and redirected to their destination within 3 seconds of completing credentials
- Session cookie is set with correct security attributes (HttpOnly, Secure, SameSite=Strict)
- Access token is available in the application for API calls
- Failed login attempts are rate-limited and logged
- MFA enrollment prompt shown to unenrolled users

## User Info

| Field | Value |
|-------|-------|
| Role | End user (free tier, paid, or enterprise) |
| Permissions | Unauthenticated at start; authenticated after completion |
| Test account | test-user@example.com (password: use test credential store) |
| Environment | Production, staging (separate test accounts per environment) |
| MFA status | Variable — test with both MFA-enrolled and non-enrolled accounts |
