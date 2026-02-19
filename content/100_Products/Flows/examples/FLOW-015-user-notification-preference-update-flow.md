---
id: FLOW-015
type: flow
title: User Notification Preference Update Flow
status: approved
owner: QA Engineer
created: '2024-09-10T13:16:54.244Z'
updated: '2025-08-08T21:36:43.011Z'
tags:
  - flow
  - notification-service
summary: User Notification Preference Update Flow
feature_area: Notification Service
related_prds:
  - PRD-018
example: true
---

## Steps

### Step 1: User Accesses Notification Settings

The user navigates to the notification settings screen in the app (Settings > Notifications). The mobile or web client calls `GET /v1/users/{userId}/preferences` on the Notification Preference API. The API serves the user's current preference document from the Redis cache (cache hit) or from PostgreSQL on a cache miss. The UI renders toggle controls for global opt-out, per-channel opt-outs (email, push, SMS), quiet hours, and digest preferences.

### Step 2: User Makes Preference Changes

The user adjusts their preferences — for example, disabling marketing push notifications or setting quiet hours from 10pm to 8am in their local timezone. The UI updates the preference document in-memory as the user toggles controls, showing a "Save" button when changes are pending.

### Step 3: Preference Write

The client calls `PUT /v1/users/{userId}/preferences` with the complete updated preference document. The Notification Preference API validates the payload (required fields, valid timezone, valid quiet hours window), writes the new preference document to PostgreSQL, appends a `preference_events` audit record, and invalidates the Redis cache entry for the user. The API responds with `200 OK` and the updated preference document.

### Step 4: Cache Propagation and Downstream Notification

After the write completes, the Notification Preference API publishes a `preference.updated` event to the RabbitMQ `notifications.preferences` exchange. The Notification Routing Engine and other delivery services subscribed to this exchange receive the event and invalidate their own preference caches for the affected user. Within 30 seconds of the user saving their preferences, all routing decisions for that user reflect the new preferences.

## Expected Results

- Preference changes are persisted to PostgreSQL within 500ms of the user tapping Save
- The updated preference is reflected in routing decisions within 30 seconds
- The audit log captures the previous and new values for every preference change
- If the user opts out of all push notifications, no further push jobs are enqueued for that user after the 30-second propagation window
- The user sees their saved preferences correctly if they close and reopen the settings screen

## User Info

| Field | Value |
|-------|-------|
| Role | Authenticated app user |
| Permissions | Can read and update own notification preferences |
| Test account | testuser@example.com |
| Test scenario | Disable push, set quiet hours 10pm-8am America/New_York |
| Environment | Staging |
