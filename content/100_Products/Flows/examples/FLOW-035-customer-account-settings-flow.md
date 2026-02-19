---
id: FLOW-035
type: flow
title: Customer Account Settings Flow
status: accepted
owner: QA Engineer
created: '2025-04-18T12:51:04.764Z'
updated: '2025-09-06T10:33:51.421Z'
tags:
  - flow
  - customer-portal
summary: Customer Account Settings Flow
feature_area: Customer Portal
related_prds:
  - PRD-041
example: true
---

## Steps

### Step 1: Navigate to Settings

User clicks their avatar or name in the portal navigation bar and selects "Settings", or navigates directly to `/settings`. The Settings page loads, displaying four sections: Profile, Notifications, Communication, and Security.

### Step 2: Edit a profile field

User clicks into the "Display Name" or "Email" field, makes a change, and clicks "Save Changes" in the Profile section. The portal sends an `UpdateProfileSettings` GraphQL mutation. The form shows a loading spinner on the Save button while the request is in flight.

### Step 3: Toggle a notification preference

User navigates to the Notifications section. User toggles "Email Digest" off or mutes a notification category (e.g., "Promotions"). Each toggle auto-saves using an `UpdateNotificationSettings` mutation. A brief "Saved" checkmark confirms the change.

### Step 4: Change password

User navigates to the Security section and clicks "Change Password". A modal opens with fields for Current Password, New Password, and Confirm New Password. User fills in the fields and clicks "Update Password". The portal sends a `ChangePassword` mutation. On success, the modal closes and a success toast appears.

## Expected Results

- Profile changes are reflected immediately on the Settings page and on the dashboard (display name in the header)
- Notification preference changes take effect for the next notification delivery
- Password change requires the correct current password; an incorrect current password returns a clear error message ("Incorrect current password")
- All changes emit a `settings.changed` audit event to the portal event bus

## User Info

| Field | Value |
|-------|-------|
| Role | Customer (authenticated, email verified) |
| Permissions | Can read and update own profile, notification, and security settings |
| Test account | portal-test-customer@example.com |
| Environment | Staging (portal.staging.example.com) |
| Prerequisites | Customer must have an active authenticated session |
