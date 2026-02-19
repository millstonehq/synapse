---
id: TDD-045
type: tdd
title: Customer Portal Real-Time Updates TDD
status: approved
owner: Principal Engineer
created: '2024-11-08T21:55:28.567Z'
updated: '2025-11-22T13:28:05.942Z'
tags:
  - tdd
  - customer-portal
summary: Customer Portal Real-Time Updates TDD
related_adrs:
  - ADR-0034
  - ADR-0035
example: true
---

## Summary

Design the real-time update infrastructure for the Customer Portal: live ticket status updates, live unread notification counts, and live activity feed entries delivered to the browser without a page refresh. The implementation uses GraphQL subscriptions over WebSocket as specified in [[ADR-0034|ADR-0034]] (Next.js client component model) and [[ADR-0035|ADR-0035]] (GraphQL API), with a dedicated subscription server running on Kubernetes alongside the Customer API Gateway.

## Overview

Real-time updates are a prerequisite for the Notification Center (TDD-042) and improve the perceived responsiveness of the ticket management workflow. The design avoids polling and uses a single persistent WebSocket connection per browser session that multiplexes all subscriptions.

Key design principles:
- **Single connection per session**: All active subscriptions (notifications, ticket status, activity) share one WebSocket connection managed by Apollo Client's `WebSocketLink`
- **Subscription server isolation**: The GraphQL subscription server is a long-lived Node.js process on Kubernetes, separate from the stateless Next.js/Vercel deployment, because Vercel serverless functions do not support persistent connections
- **Graceful reconnect**: The client uses exponential backoff with jitter for reconnection; the UI shows a subtle connectivity indicator when the WebSocket is disconnected
- **Server-side authorization**: The subscription server validates the customer's JWT on connection establishment and scopes all events to that `customer_id`; no subscription data leaks across sessions

## Architecture

- **Subscription Server** (Kubernetes): `graphql-ws` server running alongside the Customer API Gateway; subscribes to Redis Pub/Sub channels keyed by `customer_id`; fans events to connected WebSocket clients
- **Event Publisher** (backend services): Support Widget Service, Preference Service, and Notification Ingestion Service publish events to Redis channels on state changes
- **WebSocketLink** (portal frontend): Apollo Client `WebSocketLink` connects to the subscription server; React hooks (`useSubscription`) bind to specific subscriptions per component
- **Fallback polling**: If the WebSocket connection fails after 3 reconnect attempts, the portal falls back to 30-second polling for the notification feed

## Information Model

- **TicketStatusUpdate**: `{ ticketId: ID, newStatus: TicketStatus, updatedAt: DateTime }`
- **NotificationPush**: `{ notificationId: ID, category: NotificationCategory, title: String, body: String }`
- **ActivityUpdate**: `{ activityId: ID, type: ActivityType, description: String, timestamp: DateTime }`
- **UnreadCountUpdate**: `{ unreadCount: Int }`

## Interfaces

- `subscription OnTicketStatusChange($ticketId: ID!) { ticketStatusChanged(ticketId: $ticketId) { newStatus updatedAt } }` — per-ticket status subscription
- `subscription OnNewNotification { newNotification { notificationId category title body } }` — new notification push
- `subscription OnUnreadCountChange { unreadCountChanged { unreadCount } }` — badge count update
- `subscription OnActivityUpdate { activityUpdated { activityId type description timestamp } }` — live activity feed

## Files and Layout

```
services/
  subscription-server/
    server.ts               - graphql-ws server; JWT auth middleware; Redis subscriber
    resolvers/
      ticketStatus.ts       - ticketStatusChanged resolver
      notifications.ts      - newNotification resolver
      activity.ts           - activityUpdated resolver
    redis/
      subscriber.ts         - Redis Pub/Sub channel management
lib/
  apollo/
    wsLink.ts               - Apollo WebSocketLink configuration with reconnect policy
    fallbackPolling.ts      - Polling fallback if WebSocket unavailable
components/
  realtime/
    RealtimeProvider.tsx    - Context provider; initializes Apollo WebSocketLink on mount
    ConnectionIndicator.tsx - UI indicator for WebSocket connectivity state
```

## Work Plan

1. **Phase 1 - Subscription server scaffold (Week 1)**: Set up `graphql-ws` server on Kubernetes; implement JWT auth on connection; connect to Redis Pub/Sub
2. **Phase 2 - Event publishers (Week 2)**: Add Redis publish calls to Support Widget Service (ticket status changes) and Notification Ingestion Service (new notifications)
3. **Phase 3 - Resolvers and schema (Week 2-3)**: Add subscription types to GraphQL schema; implement resolvers for all four subscription types
4. **Phase 4 - Frontend integration (Week 3-4)**: Configure Apollo `WebSocketLink`; implement `RealtimeProvider`; wire `useSubscription` hooks into `NotificationBell`, `ActivityFeed`, and ticket detail pages
5. **Phase 5 - Fallback and resilience (Week 4)**: Implement polling fallback; implement `ConnectionIndicator`; load test 500 concurrent WebSocket connections

## Risks and Mitigations

- **Risk**: Redis Pub/Sub becomes a bottleneck under high event volume (many simultaneous ticket updates). **Mitigation**: Use separate Redis channels per customer_id rather than a broadcast channel; the subscription server only subscribes to channels for currently connected customers.
- **Risk**: WebSocket connections leak server memory if clients disconnect without a clean close. **Mitigation**: Implement server-side heartbeat (ping/pong every 30 seconds); terminate connections that miss two consecutive heartbeats.
- **Risk**: JWT expiry during a long WebSocket session causes the subscription to silently stop receiving events. **Mitigation**: Client sends a refreshed token to the server before expiry via the `graphql-ws` connection_init message; server re-validates and updates the session.
