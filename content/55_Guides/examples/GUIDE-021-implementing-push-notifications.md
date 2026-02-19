---
id: GUIDE-021
type: guide
title: Implementing Push Notifications
status: draft
owner: Engineering Team
created: '2024-08-03T11:11:12.091Z'
updated: '2026-04-25T00:16:13.625Z'
tags:
  - guide
  - notification-service
summary: Implementing Push Notifications
audience: internal
related_systems:
  - SYSTEM-016
  - SYSTEM-017
related_sops:
  - SOP-031
  - SOP-040
example: true
---

## Why This Matters

Push notifications drive time-sensitive engagement — transaction confirmations, security alerts, order updates. But they're also the easiest channel to abuse. Users have no tolerance for irrelevant push notifications and will revoke permissions immediately. This guide explains how to implement push correctly through the Notification Service so you don't burn the channel.

## Device Token Registration

Push notifications require a device token — a unique address issued by APNs (iOS) or FCM (Android). Your mobile client is responsible for requesting this token from the OS and registering it with the platform. To register a token, call the Notification Service device registration endpoint:

```
POST /api/v1/device-tokens
{
  "user_id": "usr_abc123",
  "platform": "ios",
  "token": "<apns_token>",
  "app_version": "3.2.1"
}
```

Tokens should be re-registered on every app launch, as they can be refreshed by the OS. The Notification Service deduplicates tokens by `(user_id, platform, token)` and does not create duplicate records.

## Sending a Push Notification

After registering tokens, send push notifications through the standard notification event queue — the same as email and SMS. Set `channel: push` in your event payload. The Notification Service resolves all registered tokens for the user and dispatches to all active devices.

Push payloads must conform to the Push Notification Schema Standard. Key constraints:
- `title`: max 65 characters
- `body`: max 240 characters
- No raw PII in the payload — resolve all personalization server-side
- `deep_link`: use app-registered URI schemes only (e.g., `myapp://orders/123`)

## Handling Token Invalidation

When APNs or FCM returns `NotRegistered` or `InvalidRegistration`, the user has uninstalled the app or revoked push permission. The Notification Service automatically marks these tokens as invalid and stops dispatching to them. Your service does not need to handle this case.

## Next Steps

Test your integration using the Debug Push Notification Delivery SOP (SOP-038) procedure for local validation. Review the Push Notification Data Privacy Policy before adding any new data fields to push payloads.
