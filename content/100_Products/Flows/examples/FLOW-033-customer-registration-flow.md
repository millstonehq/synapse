---
id: FLOW-033
type: flow
title: Customer Registration Flow
status: proposed
owner: QA Lead
created: '2024-08-03T11:28:54.440Z'
updated: '2025-11-03T05:12:06.911Z'
tags:
  - flow
  - customer-portal
summary: Customer Registration Flow
feature_area: Customer Portal
related_prds:
  - PRD-041
example: true
---

## Steps

### Step 1: Navigate to Registration Page

The user arrives at the Customer Portal landing page and clicks the "Create Account" link in the top navigation or on the login modal. They are taken to the registration form at `/portal/register`. Any previously entered email address passed via query parameter (e.g., from a marketing email) is pre-populated in the email field.

### Step 2: Enter Account Details

The user fills in the required fields: first name, last name, email address, and password. A password strength indicator updates in real time as the user types. The form validates that the email address is not already associated with an existing account and that the password meets the minimum requirements (8 characters, at least one number and one special character) before allowing submission.

### Step 3: Accept Terms and Submit

The user reviews a summary of the Terms of Service and Privacy Policy, each linked to their full text in a new tab. After checking the acceptance checkbox, the "Create Account" button becomes active. On submission, the system creates the account record, assigns the default `customer` role, and triggers a verification email to the provided address.

### Step 4: Email Verification

The user receives a verification email within two minutes containing a single-use confirmation link valid for 24 hours. Clicking the link marks the account as verified and redirects the user to the Customer Portal dashboard with a welcome banner. If the link has expired, the user is prompted to request a new verification email from the login page.

### Step 5: Profile Completion (Optional)

After first login, the user is presented with an optional profile completion prompt asking for a phone number and preferred contact method. This step can be skipped and completed later from the Account Settings page. Completing the profile unlocks features such as SMS order notifications and faster support ticket routing.

## Expected Results

- A new customer account is created with status `pending_verification` immediately after form submission
- A verification email is delivered to the provided address within two minutes
- Account status transitions to `active` upon successful email link click
- The user is redirected to the Customer Portal dashboard and sees a personalised welcome message
- The new account appears in the Customer Portal admin view with the correct role and creation timestamp

## User Info

| Field | Value |
|-------|-------|
| Role | Unauthenticated visitor (pre-registration) |
| Permissions | None prior to registration; `customer` role granted on account creation |
| Test account | new-reg-test@example.com (use a unique email per test run) |
| Environment | Staging |
| Related PRD | [[PRD-041|Customer Portal PRD]] |
