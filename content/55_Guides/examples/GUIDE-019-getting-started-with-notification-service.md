---
id: GUIDE-019
type: guide
title: Getting Started with Notification Service
status: approved
owner: Engineering Team
created: '2025-05-26T04:07:06.396Z'
updated: '2026-11-24T18:16:49.544Z'
tags:
  - guide
  - notification-service
summary: Getting Started with Notification Service
audience: internal
related_systems:
  - SYSTEM-019
  - SYSTEM-016
related_sops:
  - SOP-036
  - SOP-033
example: true
---

## Why This Matters

The Notification Service is the single gateway for all user-facing communications: email, push, SMS, and in-app messages. If you're building a feature that needs to inform users of an event, you'll go through this service. Understanding its architecture and integration model saves hours of debugging and prevents you from accidentally spamming users or violating opt-out preferences.

## How the Service Works

The Notification Service is event-driven. You publish a notification event to an SQS queue; the service consumes it, resolves the recipient's preferences and suppression status, selects the appropriate channel and template, and dispatches to the provider. This means your service does not call email or SMS APIs directly — it only emits events.

The service also enforces rate limits, respects user opt-outs, and handles retries automatically. Your service should not implement its own retry logic for notifications — doing so can cause duplicates.

## Publishing Your First Notification

To send a notification from your service, publish a JSON message to the `notification-events` SQS queue. The message must conform to the payload schema defined in the Notification Payload Format Standard. At minimum you need:

- `notification_id` — a UUID v4 you generate (used for deduplication)
- `recipient_id` — the user_id of the recipient
- `template_id` — the ID of an approved template in the template registry
- `channel` — one of `email`, `push`, `sms`, `in_app`
- `priority` — one of `critical`, `high`, `normal`, `low`
- `idempotency_key` — same as `notification_id` for most use cases

Test your integration in the staging environment first. The staging Notification Service routes sends to sandboxed providers (SendGrid sandbox mode, FCM test project) so no real messages are delivered.

## Requesting a New Template

You cannot use a template that doesn't exist in the registry. If your feature requires a new notification, open a template request via the Notification Template Approval Process. Typical turnaround is 3–5 business days. Include: the notification event trigger, the dynamic variables your service will provide, and a content draft.

## Next Steps

- Review the Notification Payload Format Standard to understand required fields and validation rules
- Consult the Testing Notification Delivery Locally guide (GUIDE-023) to set up your local dev environment
- Join `#notifications-eng` in Slack for questions and announcements from the Notification Service team
