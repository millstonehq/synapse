---
id: FLOW-007
type: flow
title: MFA Enrollment Flow
status: approved
owner: QA Lead
created: '2024-10-03T07:43:15.139Z'
updated: '2025-06-05T19:34:24.163Z'
tags:
  - flow
  - user-authentication
summary: MFA Enrollment Flow
feature_area: User Authentication
related_prds:
  - PRD-007
example: true
---

## Steps

### Step 1: Initiate MFA Enrollment

The user navigates to the security settings page (or is prompted via the post-login enrollment nudge). They are presented with three factor options: Authenticator App (TOTP), SMS OTP, and Security Key / Passkey (WebAuthn). The user selects their preferred option. The system verifies that the user's current session is fresh (issued within the last 10 minutes); if not, the user is prompted to re-enter their password before proceeding with enrollment.

### Step 2: Factor-Specific Setup

For **Authenticator App (TOTP)**: The system generates a unique TOTP secret and displays it as a QR code and a plain-text backup code. The user scans the QR code with their authenticator app (Google Authenticator, Authy, 1Password, etc.). The secret is not stored until enrollment is confirmed in Step 3.

For **SMS OTP**: The user enters their mobile phone number. The system sends a 6-digit verification code via SMS (10-minute TTL). The user enters the code to verify phone ownership. The phone number is stored (masked in the UI) after successful verification.

For **WebAuthn Passkey**: The browser triggers the WebAuthn `navigator.credentials.create()` API. The user completes the platform authenticator challenge (Face ID, Touch ID, Windows Hello, or PIN). The resulting credential public key is returned to the server for storage.

### Step 3: Confirmation Challenge

After factor setup, the user must complete one successful authentication challenge with the new factor before enrollment is finalized. For TOTP, the user enters a fresh 6-digit code from their authenticator app. For SMS, a new verification code is sent. For WebAuthn, a new assertion challenge is issued. This confirmation ensures the factor is working correctly before it is marked as enrolled.

### Step 4: Backup Codes

After successful confirmation, the user is shown a set of 8 single-use backup codes. The user is instructed to store these codes securely — they can be used to recover account access if the primary MFA factor is unavailable (e.g., lost phone). The backup codes are hashed and stored server-side. The user must acknowledge viewing the codes before proceeding.

### Step 5: Enrollment Complete

The MFA factor is marked as enrolled in the user's profile. The user is redirected back to security settings, which now show the enrolled factor. The system sends a confirmation email informing the user that MFA has been enabled on their account, including the date, time, and IP address of enrollment.

## Expected Results

- Factor successfully enrolled after confirmation challenge
- Backup codes generated and acknowledged by user
- Confirmation email sent to user's verified email address
- MFA required on next login attempt (with a 60-second grace period for the current session)
- Factor visible in security settings with masked details (last 4 digits of phone, device name for passkey)

## User Info

| Field | Value |
|-------|-------|
| Role | Authenticated end user (any tier) |
| Permissions | Must be authenticated with a fresh session (< 10 min old) |
| Test account | test-mfa-enroll@example.com (clean state, no MFA enrolled) |
| Environment | Staging (SMS via test number +1-555-000-0000); staging WebAuthn uses virtual authenticator |
| Prerequisites | User must be logged in and have a verified email address |
