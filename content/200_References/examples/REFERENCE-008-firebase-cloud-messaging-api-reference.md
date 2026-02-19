---
id: REFERENCE-008
type: reference
title: Firebase Cloud Messaging API Reference
status: published
owner: Platform Team
created: '2025-02-09T17:55:19.422Z'
updated: '2025-04-02T05:48:37.132Z'
tags:
  - reference
  - notification-service
summary: Firebase Cloud Messaging API Reference
upstream_url: https://docs.example.com/firebase-cloud-messaging-api-reference
last_synced: '2026-08-19T04:18:38.960Z'
attribution: IEEE
license: CC BY-SA 4.0
category: tutorial
example: true
---

## Overview

Firebase Cloud Messaging (FCM) is Google's cross-platform messaging solution for Android, iOS, and the web. The Push Notification Gateway uses the FCM HTTP v1 API to deliver push notifications to Android devices and to Android apps on ChromeOS. FCM v1 replaced the legacy FCM HTTP API and XMPP protocol; the legacy endpoints were shut down in June 2024.

The FCM v1 API uses OAuth 2.0 service account credentials (rather than a server key) for authentication, which provides per-project token scoping and eliminates the security risk of a long-lived shared secret.

## Authentication

FCM v1 requires a short-lived OAuth 2.0 bearer token scoped to `https://www.googleapis.com/auth/firebase.messaging`. The Push Notification Gateway obtains this token using a service account key file via the Google Auth Library:

- Tokens expire after 1 hour; the gateway refreshes them proactively (5 minutes before expiry) using a background job
- The service account key is stored in Kubernetes Secrets and injected as an environment variable at runtime
- Each Firebase project requires its own service account; the gateway supports multiple project credentials for multi-app deployments

## Key Endpoints

**Send a message** (single device):
`POST https://fcm.googleapis.com/v1/projects/{project_id}/messages:send`

**Send to multiple devices** (batch):
`POST https://fcm.googleapis.com/batch`

The batch endpoint accepts up to 500 individual message requests in a single HTTP multipart request. The Push Notification Gateway uses the batch endpoint for NORMAL and LOW priority notifications to reduce FCM API call volume by up to 60% compared to individual sends. CRITICAL and HIGH priority notifications are sent individually to avoid batch accumulation delay.

## Message Structure

The FCM v1 message payload uses a platform-agnostic `message` wrapper with an optional `android` override block:

```json
{
  "message": {
    "token": "<device_registration_token>",
    "notification": {
      "title": "Your order has shipped",
      "body": "Order #12345 is on its way"
    },
    "android": {
      "priority": "high",
      "notification": {
        "channel_id": "order_updates",
        "click_action": "OPEN_ORDER_DETAIL"
      }
    }
  }
}
```

Key fields:
- `token`: The device registration token obtained at app install and stored in the Push Notification Gateway's token registry
- `android.priority`: `"normal"` (delivered when the device is active) or `"high"` (wakes the device; use for time-sensitive notifications)
- `android.notification.channel_id`: Maps to an Android notification channel defined in the app; required for Android 8.0 and above

## Error Handling

FCM v1 returns structured error responses that the Push Notification Gateway handles as follows:

- `UNREGISTERED` (404): The device token is no longer valid (app uninstalled or token rotated). The gateway marks the token as inactive in the token registry immediately. This is the most common error.
- `INVALID_ARGUMENT` (400): The message payload is malformed. The job is sent to the dead-letter queue for investigation; this is typically caused by an unsupported `channel_id` value.
- `QUOTA_EXCEEDED` (429): The per-project send quota has been exceeded. The gateway backs off exponentially (starting at 1 second) and retries up to 5 times before moving the job to the dead-letter queue.
- `UNAVAILABLE` (503): FCM is temporarily unavailable. The gateway retries with exponential backoff; if FCM remains unavailable after 90 seconds, the circuit breaker trips and notifications are queued for deferred delivery.
- `INTERNAL` (500): Unexpected FCM error. Treated the same as `UNAVAILABLE`.

## Token Management

Device registration tokens change when: the user installs the app on a new device, the user clears app data, or FCM rotates the token automatically. The Push Notification Gateway maintains a token registry (PostgreSQL + Redis cache) and handles token lifecycle:

- New tokens are registered via `POST /v1/devices` on the Push Notification Gateway's internal API, called by the mobile client on first launch and after FCM token rotation
- Stale tokens (no successful delivery in 60 days) are flagged for cleanup
- `UNREGISTERED` errors immediately invalidate the token and suppress further sends to that token

## Sync Notes

This reference documents FCM HTTP v1 API behavior as used by the Push Notification Gateway. For APNs-specific behavior, see the internal Push Platform Differences wiki. Re-sync when Google publishes breaking changes to the FCM v1 API or deprecates message fields used in the gateway's payload mapper.
