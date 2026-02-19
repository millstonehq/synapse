---
id: GUIDE-022
type: guide
title: Notification Preference Management Guide
status: review
owner: Engineering Team
created: '2024-04-18T00:34:32.165Z'
updated: '2025-01-16T23:56:25.289Z'
tags:
  - guide
  - notification-service
summary: Notification Preference Management Guide
audience: customer
related_systems:
  - SYSTEM-019
  - SYSTEM-016
related_sops:
  - SOP-036
  - SOP-031
example: true
---

## Why This Matters

User notification preferences control what users receive and how. Respecting these preferences is both a legal requirement (CAN-SPAM, GDPR) and a product quality concern. This guide explains the preference model, how preferences are enforced at dispatch time, and how to build preference UI that integrates correctly with the Notification Service.

## The Preference Model

Each user has a preference record in the Notification Service with three layers of control:

1. **Global opt-out**: User has unsubscribed from all non-transactional notifications. The Notification Service will never send marketing or informational messages regardless of channel or notification type.
2. **Channel-level preferences**: User has disabled a specific channel (e.g., "no SMS"). Transactional messages on that channel are also blocked.
3. **Notification-type preferences**: User has enabled or disabled specific notification categories (e.g., "weekly digest emails", "payment reminders").

Transactional notifications (account security, payment receipts) bypass type-level preferences but are still subject to global opt-out and channel-level preferences.

## Reading and Writing Preferences

Preference reads and writes go through the preference management API:

```
GET  /api/v1/users/{user_id}/preferences
PATCH /api/v1/users/{user_id}/preferences
```

When building a preference center UI, fetch the current preference state on page load and display it. On save, send a PATCH with only the fields that changed. The Notification Service applies changes immediately — preferences take effect on the next dispatch cycle.

## Handling Unsubscribe Links

All non-transactional email templates include a `{{unsubscribe_url}}` variable. This URL is a signed, one-click unsubscribe link managed by the Notification Service. Clicking it records the opt-out via the preferences API and sends a confirmation email within 24 hours. Do not implement custom unsubscribe flows that bypass this mechanism.

## Next Steps

Review the Notification Opt-Out Compliance Policy for the legal requirements around opt-out processing timelines. Use the Unsubscribe Request Handling Process reference for understanding how opt-outs flow through the system.
