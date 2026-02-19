---
id: GUIDE-024
type: guide
title: Understanding Notification Routing Rules
status: approved
owner: Engineering Team
created: '2025-10-17T06:46:47.919Z'
updated: '2025-07-18T01:51:08.840Z'
tags:
  - guide
  - notification-service
summary: Understanding Notification Routing Rules
audience: partner
related_systems:
  - SYSTEM-018
  - SYSTEM-020
related_sops:
  - SOP-038
  - SOP-040
example: true
---

## Why This Matters

When you publish a notification event, you specify a channel — but the Notification Service doesn't simply send blindly. It evaluates a set of routing rules before dispatching: user preferences, opt-out status, priority level, and channel availability. Understanding this logic helps you predict when a notification will and won't be delivered, and debug unexpected failures.

## The Routing Decision Pipeline

Every notification event goes through the following checks in order:

1. **Suppression list check**: Is the recipient's email/phone/device token on the global suppression list? If yes, delivery is skipped and the notification is marked `suppressed`.
2. **Opt-out check**: Has the user opted out of the notification's category or channel? If yes, delivery is skipped (unless the notification is marked `critical` or is classified as transactional).
3. **Priority override**: `critical` priority notifications bypass opt-out checks for channel-level preferences but still respect global opt-outs.
4. **Channel availability**: Is the requested channel currently active (not disabled via feature flag)? If the channel is disabled, the Notification Service checks if a fallback channel is configured.
5. **Rate limit check**: Does dispatching this notification exceed the user's per-channel rate limit? If yes, the notification is deferred to the next available send slot.
6. **Provider routing**: The notification is routed to the active provider for the channel (primary or failover provider).

## Fallback Channel Configuration

You can configure a fallback channel for a notification type. For example, if a push notification fails because the user has no registered device tokens, the Notification Service can automatically fall back to email. Fallback chains are defined in the notification type registry and must be approved before they are active.

Fallback only triggers on specific conditions: no valid tokens, channel disabled, or a permanent provider error. Transient errors (timeouts, soft failures) trigger retry, not fallback.

## Debugging a Routing Decision

If a notification was not delivered and you need to understand why, query the `notifications` table for the `notification_id` and check the `status` and `routing_outcome` fields. The `routing_outcome` field stores the step at which the routing pipeline stopped and the reason code (e.g., `suppressed`, `opt_out`, `rate_limited`, `no_valid_token`).

## Next Steps

Review the Notification Priority Level Standard to understand how priority affects routing. If you need a custom fallback configuration for your notification type, submit a request to the Notification Service team via the `#notifications-eng` channel.
