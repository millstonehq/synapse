---
id: WIKI-016
type: wiki
title: Notification Priority System - Deep Dive
status: approved
owner: Notification Team
created: '2024-10-14T13:28:34.528Z'
updated: '2025-01-25T02:00:00.798Z'
tags:
  - wiki
  - notification-service
summary: Notification Priority System - Deep Dive
source_repo: https://git.example.com/acme/notification-priority-system
commit_sha: 21153f2542e6ef7134ecf032fecae3332db8d785
generated_at: '2025-03-23T08:08:29.551Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: gpt-4
importance: high
example: true
---

## Overview

The Notification Platform uses a four-level priority system to control delivery speed, queuing behavior, and resource allocation across all notification types. Priority is assigned by the notification producer at enqueue time and flows through the entire delivery pipeline, influencing queue selection, rate limiting, and provider-level delivery settings.

This deep dive documents how priority levels are defined, how they map to internal queue infrastructure, and the tradeoffs involved in choosing a priority for a given notification type.

## Priority Levels

The platform defines four priority levels in ascending urgency order:

- **LOW**: Digest summaries, weekly reports, and promotional messages. Eligible for batching. Subject to daily frequency caps and quiet hours enforcement. Delivered via lower-priority RabbitMQ queues with a 24-hour TTL.
- **NORMAL**: Standard transactional alerts, account activity notifications, and non-urgent product updates. Delivered within 60 seconds under normal load. Subject to per-hour frequency caps; quiet hours are respected unless the user has opted out of quiet hours.
- **HIGH**: Time-sensitive alerts such as order status changes, shipping updates, and security notifications. Bypasses quiet hours. Delivered within 10 seconds under normal load. Not eligible for batching.
- **CRITICAL**: Authentication OTPs, fraud alerts, and security incident notifications. No frequency caps. No batching. Delivered immediately via the highest-priority consumer group. APNs priority 10 / FCM HIGH mandatory.

## Queue Architecture

Each priority level maps to a dedicated RabbitMQ exchange and queue set:

| Priority | Exchange | Consumer Group | Max Queue Depth | TTL |
|----------|----------|----------------|-----------------|-----|
| LOW | `notifications.low` | `low-priority-workers` (2 pods) | 500,000 | 24h |
| NORMAL | `notifications.normal` | `normal-priority-workers` (4 pods) | 200,000 | 4h |
| HIGH | `notifications.high` | `high-priority-workers` (6 pods) | 50,000 | 1h |
| CRITICAL | `notifications.critical` | `critical-priority-workers` (8 pods) | 10,000 | 15m |

Messages exceeding TTL without delivery are dead-lettered for analysis. CRITICAL dead-letter depth triggers a PagerDuty alert.

## Rate Limiting Behavior

Rate limiting is applied per-user, per-channel, per-priority-band:

- LOW and NORMAL notifications share a combined daily cap (configurable per user, default 20/day across both channels).
- HIGH notifications have a separate hourly cap (default 10/hour per channel).
- CRITICAL notifications are exempt from all rate limits.

Rate limit decisions are made in the Notification Routing Engine using Redis counters with sliding window semantics.

## Generation Notes

Generated from commit `21153f2` on the `main` branch. The generator analyzed the routing engine source and the queue configuration to document the priority system. Manual review recommended for accuracy.
