---
id: FLOW-016
type: flow
title: Notification Unsubscribe Flow
status: approved
owner: QA Lead
created: '2025-03-02T12:34:16.428Z'
updated: '2025-11-08T11:09:45.765Z'
tags:
  - flow
  - notification-service
summary: Notification Unsubscribe Flow
feature_area: Notification Service
related_prds:
  - PRD-019
example: true
---

## Steps

### Step 1: User Initiates Unsubscribe

The user clicks the "Unsubscribe" link in an email notification. The unsubscribe link is a unique URL containing an encoded `(userId, channel, notificationType)` token. This URL is embedded in every email template and enforced by the email template pre-publish validator. Clicking the link opens the unsubscribe confirmation page hosted by the Notification Platform.

### Step 2: Unsubscribe Confirmation Page

The unsubscribe confirmation page decodes the token and shows the user what they are unsubscribing from (e.g., "You are about to unsubscribe from marketing emails from ExampleCo"). The user can choose to: (a) unsubscribe from only this notification type, (b) unsubscribe from all marketing emails, or (c) unsubscribe from all emails globally. The user clicks "Confirm Unsubscribe" to proceed.

### Step 3: Preference Update

The unsubscribe service calls `PUT /v1/users/{userId}/preferences` on the Notification Preference API with the updated preference document reflecting the user's choice. For a category-level unsubscribe, the specific category is set to `false` in `categorySubscriptions`. For a channel-level unsubscribe, the corresponding `channelOptOuts.email` flag is set to `true`. For a global unsubscribe, `globalOptOut` is set to `true`. The one-click List-Unsubscribe header in every email supports the global unsubscribe path for email clients that support it.

### Step 4: Confirmation and Suppression

The unsubscribe page displays a confirmation message. The Notification Preference API has already propagated the preference change to the routing engine's cache (within 30 seconds). The user's email address is also added to the Email Delivery Service's suppression list for the applicable scope (category, channel, or global). The audit log records the unsubscribe event with a timestamp and the unsubscribe scope for compliance reporting.

## Expected Results

- User preference is updated within 500ms of clicking Confirm Unsubscribe
- No further emails of the unsubscribed type are sent after the 30-second cache propagation window
- The unsubscribe action is logged in the `preference_events` audit table for compliance
- The user can re-subscribe by visiting notification settings and re-enabling the channel or category
- One-click List-Unsubscribe header in all emails allows email clients (Gmail, Outlook) to surface an unsubscribe button natively

## User Info

| Field | Value |
|-------|-------|
| Role | Email recipient (any authenticated or unauthenticated user with a valid unsubscribe token) |
| Permissions | Can unsubscribe from notifications associated with their userId |
| Test account | testuser@example.com |
| Test scenario | Click unsubscribe link in a test order-confirmation email in staging |
| Environment | Staging |
