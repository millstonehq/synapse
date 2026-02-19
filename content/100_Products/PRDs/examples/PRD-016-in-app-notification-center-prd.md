---
id: PRD-016
type: prd
title: In-App Notification Center PRD
status: approved
owner: Head of Product
created: '2025-05-03T08:55:43.599Z'
updated: '2025-05-04T18:21:33.040Z'
tags:
  - prd
  - notification-service
summary: In-App Notification Center PRD
related_tdds:
  - TDD-018
  - TDD-016
example: true
related_standards:
  - STANDARD-021
---

## Summary

Build an in-app notification center that allows users to view, manage, and act on their notifications without leaving the application. This replaces the current model where all notification content is delivered exclusively via push, email, or SMS — channels the user may have opted out of or may not check promptly. The notification center provides a persistent, browsable inbox within the app.

## Goals

- Provide a persistent notification inbox so users who have disabled push/email can still receive important alerts in-app
- Reduce notification-driven support contacts by giving users visibility into the full notification history
- Increase engagement with time-sensitive notifications by surfacing them at the point of user interaction

## In Scope

- In-app notification inbox with read/unread state and badge count
- Notification categories (transactional, promotional, system) with per-category filtering
- Mark as read, mark all as read, and delete individual notifications
- Deep link support — tapping a notification navigates to the relevant in-app screen
- Retention: notifications stored for 90 days, then archived
- REST API for mobile and web clients
- Server-sent events (SSE) for real-time badge count updates

## Out of Scope

- Rich media notifications (image attachments, video) — deferred to v2
- Notification reactions or replies
- Cross-device sync of read state (each device sees its own read state in v1)
- Admin interface for manually sending in-app notifications (separate initiative)

## Users and Flows

**End users** access the notification center from a bell icon in the app navigation bar. They see a list of notifications in reverse chronological order, with unread items visually distinguished. Tapping a notification marks it as read and navigates to the relevant content via deep link. Users can filter by category and manage read/delete state.

**Mobile clients** receive real-time badge count updates via SSE. When the user opens the notification center, the client fetches the notification list via REST API. Badge count drops to zero when the user opens the center.

**Notification producers** (order service, auth service, marketing platform) submit in-app notifications via the existing notification dispatch API with `channel: in-app` or `channel: all`. The routing engine enqueues the notification to the new in-app storage service.

## Requirements

- Display the 50 most recent notifications on initial load; support pagination for older entries
- Badge count reflects the number of unread notifications; updates in real time via SSE
- Notifications must be stored durably — not lost on device restart or app reinstall
- Each notification must include: title, body, category, deep link URL, sent timestamp, read status
- Mark-as-read must be propagated to the server immediately (optimistic UI with server confirmation)
- Notification list API must respond within 200ms at P95

## KPIs

- **In-app center adoption**: > 40% of active users view the notification center within 30 days of launch
- **Read rate**: > 60% of in-app notifications read within 24 hours
- **Push opt-out retention**: Users who disable push but enable in-app notifications retained at same rate as full-push users

## Information Architecture

- System doc for in-app notification storage service in `70_Systems/`
- This PRD in `100_Products/PRDs/`
- TDD for storage service in `90_Architecture/TDDs/`
- API reference in `200_References/`

## Data Model

- **InAppNotification**: `id`, `userId`, `title`, `body`, `category`, `deepLinkUrl`, `readAt` (null if unread), `sentAt`, `expiresAt`
- **UserNotificationState**: `userId`, `unreadCount`, `lastFetchedAt`
- Notifications are immutable after creation; only `readAt` is mutable

## Non-Functional

- Notification storage must survive service restarts and pod rescheduling (durable PostgreSQL-backed)
- Badge count SSE connections: up to 50,000 concurrent connections per pod, horizontally scalable
- Notification list API: P95 < 200ms, P99 < 500ms
- Data retention: 90 days active, archived to cold storage for 1 year

## Constraints

- Must use existing Kubernetes infrastructure
- SSE connections must be managed without stateful session affinity (use Redis pub/sub for cross-pod broadcast)
- Budget: 2 engineers for 8 weeks

## Risks

- **Badge count SSE scalability** at peak concurrent users may require dedicated SSE pods. Mitigation: implement Redis pub/sub fan-out so any pod can serve any user's SSE stream.
- **Deep link coverage** requires coordination with mobile teams for all existing notification types. Mitigation: use a fallback "open app home screen" link for notifications without a specific deep link.
- **90-day retention storage cost** may grow at high notification volume. Mitigation: enforce per-user notification count cap of 500 active entries.

## Milestones

### M1: Storage API and Basic Inbox (Weeks 1-4)
#### Deliverables
- Notification storage service with PostgreSQL backend
- REST API for list, read, delete operations
- Routing engine integration for `channel: in-app` dispatch
- Mobile client integration (iOS and Android)
#### Acceptance Criteria
- In-app notifications appear in the inbox within 5 seconds of dispatch
- Mark-as-read persists across app restarts
- Notification list loads within 200ms at P95

### M2: Real-Time Badge Count and SSE (Weeks 5-8)
#### Deliverables
- SSE endpoint for real-time badge count updates
- Redis pub/sub fan-out for cross-pod delivery
- Badge count display in app navigation bar
- Load test validating 50,000 concurrent SSE connections
#### Acceptance Criteria
- Badge count updates within 2 seconds of a new notification being stored
- Badge count drops to 0 immediately when user opens the notification center
- System sustains 50,000 concurrent SSE connections with P95 < 100ms update latency
