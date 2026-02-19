---
id: TDD-042
type: tdd
title: Customer Notification Center TDD
status: approved
owner: Principal Engineer
created: '2024-05-25T07:44:58.205Z'
updated: '2026-06-21T04:23:14.239Z'
tags:
  - tdd
  - customer-portal
summary: Customer Notification Center TDD
related_adrs:
  - ADR-0035
  - ADR-0034
example: true
---

## Summary

Design the Notification Center for the Customer Portal: a unified inbox for system alerts, ticket updates, and promotional messages. The center supports real-time delivery via WebSocket push, in-app persistence, and email digest fallback. This TDD implements the notification data layer and delivery pipeline as defined in [[ADR-0035|ADR-0035]] (GraphQL API) and the frontend integration approach from [[ADR-0034|ADR-0034]] (Next.js server components).

## Overview

The Notification Center replaces the legacy email-only notification system. Notifications are authored by backend services (Support Widget Service, Preference Service, Analytics Service) and delivered to the portal via a dedicated notifications feed exposed through the Customer API Gateway GraphQL schema.

Key design principles:
- **Push-first delivery**: Active portal sessions receive notifications via GraphQL subscriptions (WebSocket); fallback to email digest for inactive users
- **Read state ownership**: Read/unread state is stored server-side and synchronized across sessions; clearing a notification on mobile reflects on desktop
- **Category filtering**: Notifications carry a category (ticket_update, system_alert, promotion) that the UI uses for filtering and the user can mute per-category
- **Idempotent delivery**: Each notification has a stable `source_event_id` to prevent duplicates if the upstream service retries publishing

## Architecture

The Notification Center spans three layers:

- **Notification Ingestion Service**: A lightweight consumer subscribed to the internal RabbitMQ `portal.notifications` exchange; normalizes payloads from Support Widget, Preference Service, and Analytics Service into the canonical `Notification` schema and writes to PostgreSQL
- **Notification Feed API** (Customer API Gateway): GraphQL queries and subscriptions exposing the feed to the portal frontend; backed by DataLoader for efficient batch reads
- **NotificationBell Component** (portal frontend): Client component that subscribes to the GraphQL subscription and renders the unread count badge; clicking opens the full `NotificationCenter` panel (server-rendered list with client-side mark-as-read)

## Information Model

- **Notification**: `{ id: ID, customerId: ID, category: NotificationCategory, title: String, body: String, actionUrl: String, isRead: Boolean, createdAt: DateTime, sourceEventId: String }`
- **NotificationCategory**: enum `ticket_update | system_alert | promotion`
- **NotificationFeed**: `{ items: [Notification], unreadCount: Int, pageInfo: PageInfo }`

## Interfaces

- `query NotificationFeed($first: Int, $after: String, $category: NotificationCategory) { notificationFeed { unreadCount items { id title body isRead createdAt } pageInfo { endCursor hasNextPage } } }` — paginated feed query
- `subscription OnNewNotification { newNotification { id title body category } }` — real-time push subscription
- `mutation MarkNotificationRead(id: ID!)` — mark a single notification read
- `mutation MarkAllNotificationsRead` — bulk mark all read

## Files and Layout

```
app/
  notifications/
    page.tsx              - Server component: full notifications page (SSR initial list)
components/
  notifications/
    NotificationBell.tsx  - Client component: badge + subscription hook
    NotificationCenter.tsx- Client component: panel with paginated list
    NotificationItem.tsx  - Presentational: single notification row
lib/
  graphql/
    notifications.graphql - Query and subscription definitions
    generated/            - Generated TypeScript types
services/
  notification-ingestion/ - RabbitMQ consumer, normalization, PostgreSQL writes
```

## Work Plan

1. **Phase 1 - Data model and ingestion (Week 1)**: Define `notifications` PostgreSQL table; implement RabbitMQ consumer for Support Widget and Preference Service events; write normalization logic
2. **Phase 2 - GraphQL schema (Week 2)**: Add `notificationFeed`, `newNotification` subscription, and mutations to Customer API Gateway schema; implement resolvers with DataLoader
3. **Phase 3 - Frontend components (Week 3)**: Implement `NotificationBell` with subscription hook; `NotificationCenter` panel with paginated list and mark-as-read
4. **Phase 4 - Email digest fallback (Week 4)**: Implement nightly digest job that emails unread notifications to users who have not visited the portal in 24 hours
5. **Phase 5 - Testing and polish (Week 5)**: E2E tests for real-time delivery; load test subscription fanout at 500 concurrent sessions; accessibility review

## Risks and Mitigations

- **Risk**: WebSocket subscriptions do not scale horizontally on Vercel serverless. **Mitigation**: Run the subscription server as a separate long-lived service on Kubernetes; portal frontend connects directly to that endpoint rather than via Vercel edge.
- **Risk**: High notification volume causes unread counts to become stale. **Mitigation**: Unread count is computed server-side on each query; client does not cache the count independently.
- **Risk**: Notification ingestion consumer falls behind during traffic spikes. **Mitigation**: Consumer uses a durable queue with dead-letter channel; monitoring alert if consumer lag exceeds 500 messages.
