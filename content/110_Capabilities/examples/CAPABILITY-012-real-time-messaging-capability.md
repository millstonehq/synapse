---
id: CAPABILITY-012
type: capability
title: Real-Time Messaging Capability
status: draft
owner: Head of Engineering
created: '2025-08-30T19:46:24.487Z'
updated: '2025-09-05T19:55:31.903Z'
tags:
  - capability
  - notification-service
summary: Real-Time Messaging Capability
evidence_links:
  - STANDARD-020
  - STANDARD-023
  - PROCESS-064
example: true
---

## Domain

- Sub-second delivery of high-priority and CRITICAL notifications via push and in-app channels
- Server-Sent Events (SSE) for real-time in-app notification badge and inbox updates
- WebSocket and SSE connection lifecycle management at scale
- Priority queue bypass for CRITICAL notifications to guarantee delivery latency
- Real-time delivery acknowledgment and read-receipt tracking

## Maturity (0-5)

**Current score: 2 / 5 (Repeatable)**

- **Push notification latency**: 3/5 - CRITICAL and HIGH priority push notifications bypass the batching window and are dispatched within 2 seconds of routing decision; P99 latency is consistently met in production
- **In-app SSE delivery**: 2/5 - SSE endpoint exists and powers notification badge counts; connection handling under load is not load-tested above 50,000 concurrent connections; reconnect logic on the client has known reliability gaps
- **Real-time acknowledgment**: 2/5 - Push delivery receipts from APNs/FCM are captured asynchronously (latency up to 30 seconds); in-app read receipts are stored but not surfaced to producers in real time
- **WebSocket support**: 1/5 - No WebSocket layer currently exists; SSE covers unidirectional server-to-client use cases only; bidirectional real-time messaging is not supported

**Gap to Level 3**: Load-test SSE at 200,000 concurrent connections, fix client reconnect reliability, and define a formal SLA for in-app real-time delivery latency.

## Metrics

- CRITICAL push dispatch latency: P99 1.8 seconds from routing decision to provider submission (target < 2 seconds)
- HIGH push dispatch latency: P99 1.9 seconds (target < 2 seconds)
- SSE connection stability: 97.2% of connections survive a 1-hour session without client-side reconnect (target > 99%)
- In-app badge update latency: median 800ms from notification event to SSE delivery (target < 500ms)
- Real-time delivery acknowledgment latency: median 22 seconds (target < 5 seconds; gap requires async receipt pipeline redesign)

## Evidence Links

- [[STANDARD-020|Real-Time Delivery Standards]] - Defines latency SLAs and priority tier requirements for real-time notification channels
- [[STANDARD-023|Notification Delivery Standards]] - Broader delivery standards covering all channels including real-time push
- [[PROCESS-064|Notification Content Review Process]] - Governs review of notification content and priority assignments before production use

## Notes

- WebSocket support is listed as out of scope for the current roadmap; the SSE layer covers the majority of in-app real-time use cases
- The in-app badge update latency gap (800ms vs 500ms target) is attributed to an unoptimized SSE fan-out query; a fix is tracked in the backlog
