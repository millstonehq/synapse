---
id: FLOW-006
type: flow
title: Password Reset Flow
status: approved
owner: QA Lead
created: '2024-06-20T20:56:02.741Z'
updated: '2025-03-23T08:54:43.485Z'
tags:
  - flow
  - user-authentication
summary: Password Reset Flow
feature_area: User Authentication
related_prds:
  - PRD-008
example: true
---

## Steps

### Step 1: Request Password Reset

The user navigates to the password reset page and enters their email address. The system looks up the account. Regardless of whether the email is registered, the system responds with "If an account exists with this email, you will receive a reset link shortly." This prevents user enumeration. For a registered account, a password reset token (random 256-bit, base64url-encoded, 15-minute TTL) is generated, stored in Redis, and a reset link is sent to the user's verified email address.

### Step 2: Email Delivery and Link Click

The user receives an email containing the reset link. The email includes the requestor's IP address and browser information as a security notice. The link is valid for 15 minutes and is single-use. The user clicks the link, which opens the password reset page in their browser. The system validates the token from the URL query parameter against the Redis store.

### Step 3: New Password Entry

The user is prompted to enter and confirm a new password. The system enforces the password policy: minimum 12 characters, at least one uppercase, one lowercase, one digit. The system checks the new password against a list of 100,000 common passwords (HIBP-style local blocklist) and rejects matches. The system also checks that the new password is not identical to the previous password hash.

### Step 4: Password Update and Session Invalidation

Upon successful password validation, the system updates the stored password hash. All existing sessions for the account are immediately invalidated (deleted from the Session Management Service). Refresh tokens associated with the account are revoked. The user is redirected to the login page with a success message and must log in again with the new password.

### Step 5: Security Notification

The user receives a confirmation email informing them that their password was changed, including the IP address and timestamp of the change. The email includes a link to report the change as unauthorized if they did not initiate the reset. If the link is clicked, the account is flagged for security review and the new password is invalidated.

## Expected Results

- Reset link delivered to verified email within 30 seconds
- Single-use token enforced: clicking a used link shows an error directing user to request a new one
- All existing sessions invalidated within 30 seconds of password change
- User redirected to login page after successful reset
- Security notification email sent to the account's verified email address

## User Info

| Field | Value |
|-------|-------|
| Role | End user with forgotten or compromised password |
| Permissions | Unauthenticated at start |
| Test account | test-reset@example.com (configured with a valid email in test environment) |
| Environment | Staging (email delivery via test inbox); production (real email delivery) |
| Prerequisites | User must have a verified email address on the account |
