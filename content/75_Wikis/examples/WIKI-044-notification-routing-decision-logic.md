---
id: WIKI-044
type: wiki
title: Notification Routing - Decision Logic
status: approved
owner: Notification Team
created: '2024-12-18T16:09:16.106Z'
updated: '2026-05-22T19:10:55.809Z'
tags:
  - wiki
  - notification-service
summary: Notification Routing - Decision Logic
source_repo: https://git.example.com/acme/notification-routing
commit_sha: 24909eebd4ae72c44e05583b78a3be23baa9ec2e
generated_at: '2025-07-20T12:04:51.304Z'
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
importance: high
example: true
---

## Overview

The Notification Routing Engine applies a deterministic decision pipeline to every inbound notification request to select a delivery channel. This page documents the logic in the `RoutingDecisionService` — the core class responsible for evaluating routing rules and returning a channel assignment. Understanding this logic is important for debugging mis-routed notifications and for writing correct routing rule configurations.

## Decision Pipeline

The routing decision is evaluated in the following order. The pipeline short-circuits at the first definitive outcome.

1. **Hard opt-out check**: If the user has a global opt-out set in the Notification Preference Store, all routing decisions return `SUPPRESSED`. No channel is selected.
2. **Channel-specific opt-out**: If the user has opted out of the requested channel (e.g., email), that channel is excluded from consideration. If no remaining channels are available, the result is `SUPPRESSED`.
3. **Quiet hours**: For NORMAL and LOW priority notifications, if the current time in the user's timezone falls within their quiet hours window, channel delivery is deferred. The notification is re-queued with a `deliver_after` timestamp set to the end of the quiet hours window.
4. **Frequency cap**: The rolling-window frequency counter for the user, channel, and priority band is checked. If the cap is exceeded, the notification is dropped (LOW) or deferred to the next window (NORMAL).
5. **Channel availability**: The health status of each downstream delivery service is checked (cached in Redis, refreshed every 15 seconds). Channels whose services are in an open circuit breaker state are excluded.
6. **Preference ranking**: If multiple channels remain eligible, the user's ranked channel preference (stored in the Notification Preference Store) determines the final selection. Default ranking: push > email > SMS.

## Key Data Structures

The `RoutingContext` struct carries all inputs to the decision pipeline:

- `userId`: Target user identifier
- `notificationType`: Category slug (e.g., `order.shipped`, `auth.otp`)
- `priority`: `LOW | NORMAL | HIGH | CRITICAL`
- `requestedChannels`: Optional explicit channel override from the producer
- `userPreferences`: Hydrated from the Notification Preference Store at request time
- `channelHealthMap`: Current health status for each delivery service

The `RoutingDecision` struct returned by the pipeline contains:
- `channel`: Selected channel or `SUPPRESSED`
- `reason`: Human-readable explanation for the decision (for logging and debugging)
- `deliverAfter`: Optional timestamp if deferred due to quiet hours or rate limiting

## Generation Notes

Generated from commit `24909ee` on the `main` branch. The generator analyzed the routing service source files and extracted the decision pipeline logic. Manual review recommended for accuracy.
