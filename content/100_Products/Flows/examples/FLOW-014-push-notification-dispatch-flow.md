---
id: FLOW-014
type: flow
title: Push Notification Dispatch Flow
status: accepted
owner: QA Lead
created: '2025-07-23T02:22:51.947Z'
updated: '2026-10-03T17:34:13.477Z'
tags:
  - flow
  - notification-service
summary: Push Notification Dispatch Flow
feature_area: Notification Service
related_prds:
  - PRD-018
example: true
---

## Steps

### Step 1: Notification Request and Channel Selection

A producer submits a notification request to the Notification Routing Engine. For push notifications, the producer may specify `channel: push` explicitly or use `channel: all` to allow the routing engine to select the best channel. The routing engine checks user opt-in status for push, device token availability in the Push Notification Gateway's token registry, and the user's channel preference ranking. If the user has a valid registered device token and has not opted out of push, the routing engine selects `channel: push` and enqueues the job to the priority-appropriate RabbitMQ push exchange.

### Step 2: Priority Routing and Batching

The Push Notification Gateway's consumer reads the job from the queue. The priority router checks the notification's priority level: CRITICAL and HIGH notifications bypass the batching window and are dispatched immediately. NORMAL and LOW notifications enter the batch accumulator, which groups them by platform (iOS vs. Android) and flushes when the batch reaches 500 entries or the 500ms window expires. Each batch is routed to the appropriate platform submitter.

### Step 3: Platform Dispatch

For Android devices, the FCM batch submitter calls the FCM v1 `batchSend` API with up to 500 device tokens. For iOS devices, the APNs pipeline submitter sends individual HTTP/2 requests over a persistent APNs connection. Both submitters translate the platform-agnostic notification payload into the required platform-specific format: APNs JSON with the correct `apns-push-type` and `apns-priority` headers, or FCM JSON with the correct Android channel ID and priority field.

### Step 4: Delivery Receipt Processing

APNs and FCM return delivery status synchronously (for synchronous errors) or asynchronously (for delivery confirmations). Invalid device token errors (`BadDeviceToken` for APNs, `UNREGISTERED` for FCM) trigger immediate token invalidation in the token registry. The dispatch results are published to Kafka as `push.delivered` or `push.failed` events for analytics consumers.

## Expected Results

- CRITICAL and HIGH priority push notifications are dispatched within 2 seconds of routing decision
- NORMAL and LOW notifications are dispatched within 2 seconds on average (batching window adds up to 500ms)
- Invalid device tokens are marked inactive in the token registry immediately after detection
- Push delivery events appear in the notification analytics dashboard within 15 minutes
- FCM API call volume is reduced by 60% compared to individual sends via batching

## User Info

| Field | Value |
|-------|-------|
| Role | Notification producer (engineering team) |
| Permissions | Can submit push notifications for registered producer ID |
| Test account | testuser-push@example.com with registered test device |
| Test device token | See staging push test guide |
| Environment | Staging |
