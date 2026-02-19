---
id: WIKI-015
type: wiki
title: Push Notification - Platform Differences
status: approved
owner: Notification Team
created: '2024-07-06T04:45:16.487Z'
updated: '2025-07-16T15:18:18.856Z'
tags:
  - wiki
  - notification-service
summary: Push Notification - Platform Differences
source_repo: https://git.example.com/acme/push-notification
commit_sha: d18732f580965b10d6c5045fb4250d1d930ece5a
generated_at: '2025-04-02T00:37:43.063Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: claude-3-sonnet
importance: medium
example: true
---

## Overview

iOS (APNs) and Android (FCM) push notification platforms share the same conceptual delivery model but differ significantly in authentication, payload structure, priority semantics, and error handling. This page documents the key differences that affect the Push Notification Gateway implementation and should be read by any engineer working on the gateway's platform adapters.

## APNs (Apple Push Notification service)

APNs uses HTTP/2 with per-connection JWT authentication (ES256 algorithm, 10-minute token expiry). Each notification is sent as a single HTTP/2 request with a JSON body.

Key characteristics:
- **Priority**: `apns-priority: 10` for immediate delivery; `apns-priority: 5` for power-saving delivery (may be batched by iOS). Transactional alerts must use priority 10.
- **Push type**: The `apns-push-type` header is required as of iOS 13. Values: `alert`, `background`, `voip`, `complication`, `fileprovider`, `mdm`.
- **Expiry**: The `apns-expiration` header controls how long APNs stores the notification for delivery if the device is offline. Set to `0` for no storage (OTPs), or a Unix timestamp for retry window.
- **Error handling**: APNs returns a 4xx JSON error body on invalid requests. The `BadDeviceToken` and `Unregistered` error codes indicate tokens that must be removed from the registry immediately.

## FCM (Firebase Cloud Messaging)

FCM uses the HTTP v1 API with OAuth2 service account credentials. Tokens expire after 1 hour and must be refreshed using the Google auth library.

Key characteristics:
- **Android channel**: Since Android 8.0, notifications must be assigned to a channel ID pre-created on the device. Missing or unknown channel IDs result in silent delivery on newer Android versions.
- **Priority**: `HIGH` for immediate delivery (wakes the device); `NORMAL` for battery-efficient delivery (delayed when device is in Doze mode).
- **Collapse key**: FCM supports collapsing multiple notifications with the same `collapse_key` into a single delivery. Useful for "you have N unread messages" patterns.
- **Error handling**: FCM returns HTTP 200 with a success/failure count in the response body for batch sends, and specific error codes (`UNREGISTERED`, `INVALID_ARGUMENT`) that trigger token cleanup.

## Implementation Notes in the Gateway

The Push Notification Gateway abstracts both platforms behind a common `PushProvider` interface. Platform-specific behavior is encapsulated in the `APNsAdapter` and `FCMAdapter` structs. The `BuildPayload()` method on each adapter translates the platform-agnostic `PushRequest` struct into the appropriate wire format.

Token cleanup on `BadDeviceToken` / `UNREGISTERED` errors is handled synchronously within the adapter before returning the error to the caller. This ensures the token registry stays accurate without a separate cleanup job.

## Generation Notes

Generated from commit `d18732f` on the `main` branch. The generator analyzed the adapter source files and documented platform-specific behavior. Manual review recommended for accuracy.
