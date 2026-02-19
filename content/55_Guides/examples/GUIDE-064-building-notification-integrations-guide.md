---
id: GUIDE-064
type: guide
title: Building Notification Integrations Guide
status: approved
owner: Engineering Team
created: '2024-07-11T22:42:35.999Z'
updated: '2026-03-15T22:04:43.653Z'
tags:
  - guide
  - notification-service
summary: Building Notification Integrations Guide
audience: customer
related_systems:
  - SYSTEM-019
  - SYSTEM-017
related_sops:
  - SOP-034
  - SOP-035
example: true
---

## Why This Matters

The Notification Platform handles delivery of emails, push notifications, and SMS messages to users across the product. If you are building a feature that needs to notify users — an order confirmation, a security alert, a digest of weekly activity — you are integrating with the Notification Platform. Understanding how integrations work prevents the most common mistakes: sending to opted-out users, bypassing preference checks, or writing notification logic directly into a product service instead of using the shared infrastructure.

This guide covers the concepts and patterns you need to build a correct integration. For the exact API calls and credential setup steps, see [[SOP-034|Notification Producer Onboarding SOP]]. For managing the email templates your integration will use, see [[SOP-035|Email Template Publishing SOP]].

## Prerequisites

Before starting, confirm you have the following:

- A registered producer ID and API key from the Notification Platform team (request via the #notifications-platform Slack channel)
- A notification type defined in the notification type registry (e.g., `order.shipped`, `account.security_alert`) — this is required before you can submit jobs
- For email notifications: a published email template in the template registry, or agreement with the Notification Platform team on which existing template to use
- An understanding of which user preference fields your notification type is subject to (marketing notifications must respect category opt-outs; transactional notifications respect only global opt-out and channel opt-out)

## Core Concepts

### Producers and Notification Types

Your service is a **producer**. Producers submit notification requests to the Notification Routing Engine via `POST /v1/notifications`. The routing engine owns all channel selection, preference checking, quiet hours enforcement, and delivery. You do not call SendGrid, FCM, or Twilio directly — doing so bypasses preference checks and the suppression list, which is a compliance violation.

A **notification type** (e.g., `order.shipped`) defines the semantic category of a notification. It is configured in the notification type registry with a default channel, fallback channels, and the preference categories it belongs to. Once your notification type is registered, you can submit jobs without specifying routing details — the routing engine resolves them.

### The Notification Preference Store

The [[SYSTEM-019|Notification Preference Store]] holds each user's opt-in and opt-out state for every channel and notification category. When you submit a notification, the routing engine queries the preference store to determine whether the user should receive it and on which channel. You do not need to check preferences yourself — the routing engine does this for you.

However, you should understand what happens when a user has opted out: the notification is either suppressed (no delivery, no record) or rerouted to a fallback channel, depending on your notification type's configuration. If your feature depends on guaranteed delivery (e.g., a critical security alert), configure your notification type as `transactional: true` so it bypasses marketing opt-outs.

### The Email Delivery Service

The [[SYSTEM-017|Email Delivery Service]] renders and delivers email notifications. It uses the template slug and version you specify in your notification request. Template variables you pass in the `variableMap` field are injected into the template at render time. If a required variable is missing, the job is sent to the dead-letter queue and the user does not receive the email.

## Step-by-Step Integration

1. **Register your notification type** - Submit a notification type registration form (link in #notifications-platform). Specify the type name, default channel, whether it is transactional or marketing, and the variable schema for any templates it will use.
2. **Publish your email template** - If your notification requires a custom email template, follow [[SOP-035|Email Template Publishing SOP]] to author, validate, and publish it to the template registry. The pre-publish validator checks for unsubscribe link presence, required variables, and rendering correctness.
3. **Obtain producer credentials** - Follow [[SOP-034|Notification Producer Onboarding SOP]] to register your service as a producer and receive an API key scoped to your notification types.
4. **Submit a test notification in staging** - Call `POST /v1/notifications` with your test user's `userId`, your notification type, the template slug and version, and a complete `variableMap`. Check the Notification Platform staging dashboard to confirm the job was routed and delivered.
5. **Handle the `202 Accepted` response** - The routing engine returns a `notificationId` immediately; delivery is asynchronous. If you need delivery confirmation, subscribe to the `notification.delivered` and `notification.failed` events on the RabbitMQ `notifications.events` exchange.
6. **Deploy and monitor** - After deploying to production, monitor the notification analytics dashboard for your notification type. Watch for elevated dead-letter queue depth (missing variables) or suppression rate (unexpectedly high opt-out for your category).

## Common Questions

**Can I send to a user who has opted out for testing?**
In staging, you can override preference checks by adding `"debugOverridePreferences": true` to your request body. This flag is disabled in production.

**What happens if I send a notification to a userId that does not exist?**
The routing engine returns `404 Not Found` synchronously. Your service should handle this gracefully and not retry.

**How do I send to multiple users at once (bulk send)?**
Submit individual `POST /v1/notifications` requests per user. There is no batch submission endpoint. For large campaign sends (>10,000 users), use the campaign segmentation feature — contact the Notification Platform team.

**What should I put in the `priority` field?**
Use `NORMAL` for most notifications. Use `HIGH` only for time-sensitive operational alerts (e.g., a payment failure that requires immediate action). Use `CRITICAL` only for security alerts (e.g., a new device login). `CRITICAL` bypasses quiet hours and batching windows.

## Next Steps

- Complete producer registration: [[SOP-034|Notification Producer Onboarding SOP]]
- Publish your email template: [[SOP-035|Email Template Publishing SOP]]
- Review the preference model: [[SYSTEM-019|Notification Preference Store]]
- Monitor your integration after launch via the Notification Analytics Dashboard (link in #notifications-platform)
