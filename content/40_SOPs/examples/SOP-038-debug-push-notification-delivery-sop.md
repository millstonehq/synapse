---
id: SOP-038
type: sop
title: Debug Push Notification Delivery SOP
status: proposed
owner: DevOps Lead
created: '2025-09-22T07:08:04.684Z'
updated: '2026-12-13T20:16:41.378Z'
tags:
  - sop
  - notification-service
summary: Debug Push Notification Delivery SOP
related_process: PROCESS-022
related_systems:
  - SYSTEM-016
example: true
---

## Preconditions

- A user or internal report indicates push notifications are not being received on a specific device or for a specific notification type
- The affected user_id, device platform (iOS/Android), and notification type have been identified
- You have access to the Notification Service logs and the FCM/APNs response logs
- The Notification Service is otherwise healthy (no active delivery-wide incident)

## Materials/Access

- Notification Service logging platform (Kibana) with `service:notification-service` and `channel:push` filters
- FCM console (Firebase Console > Cloud Messaging) for Android delivery status
- APNs response logs or APNs Push Notifications console for iOS
- Database read access to the `device_tokens` and `notifications` tables
- The affected user_id and device token (if known) from the report

## Procedure

1. Query the `notifications` table for the user_id and notification type to confirm the notification was created and dispatched. Check the `status` and `last_attempt_at` fields.
2. If status is `dispatched`, query the `delivery_attempts` table for the notification ID and retrieve the provider response code for the push attempt.
3. Look up the FCM or APNs error code in the Notification Service logs. Common errors: `InvalidRegistration` (stale token), `NotRegistered` (user uninstalled app), `DeviceTokenNotForTopic` (wrong APNs topic).
4. Check the `device_tokens` table for the user_id and verify the stored token is current. If the token matches the error (stale or unregistered), mark it for cleanup.
5. If the token appears valid, check whether the user has push notification permissions enabled at the OS level (this cannot be verified server-side; confirm with the user).
6. Test delivery using the FCM or APNs console by sending a direct test push to the device token to confirm the token is valid and the device is reachable.
7. If the test push succeeds from the console but Notification Service sends fail, compare the payload format to the schema standard to identify any malformed fields.
8. Document findings and, if the issue is a stale token, queue a token refresh request to the mobile client.

## Validation

- The root cause is identified: stale token, OS permission revoked, payload format error, or provider routing issue
- A test push to the device token succeeds from the provider console
- If a valid token was found, a test notification dispatched by the Notification Service is received on the device

## Rollback

1. If a token cleanup was performed on a valid token, restore the original token value in the `device_tokens` table from the audit log and trigger a re-dispatch.
2. If a payload schema fix was applied that caused regression in other notification types, revert the schema change and re-evaluate.
3. Document all corrective actions in the investigation ticket.
