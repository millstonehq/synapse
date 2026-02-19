---
id: MEETING-038
type: meeting
title: Real-Time Notification Design Session
status: accepted
owner: Engineering Manager
created: '2024-01-12T12:30:01.840Z'
updated: '2025-06-23T11:31:54.013Z'
tags:
  - meeting
  - notification-service
summary: Real-Time Notification Design Session
company: NotificationService
topic: Real-Time Notification Design Session
meeting_date: '2025-01-14T06:00:18.873Z'
example: true
our_attendees:
  - Principal Engineer
  - Tech Lead
  - Product Manager
their_attendees:
  - Engineering Manager
  - QA Lead
---

## Meeting Details

- **Project**: Notification Service - Real-Time In-App Notifications
- **Topic**: Real-Time Notification Design Session
- **Date/Time**: 2025-01-14 06:00 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager
- **Context**: Product wants real-time in-app notifications (no page refresh required). Current in-app notifications are fetched on page load. Design session to evaluate WebSocket vs. SSE for the delivery mechanism.

## Observations by Domain

- **Current In-App Delivery**: Polling every 60 seconds creates notification delays of up to 1 minute; unacceptable for real-time use cases like chat messages and order status updates
- **WebSocket Evaluation**: WebSockets provide full-duplex communication; overkill for server-push-only use case, and add complexity to load balancing (sticky sessions or Redis pub/sub required)
- **SSE Evaluation**: Server-Sent Events (SSE) are simpler for server-push-only, HTTP/2 compatible, and automatically handled by browsers with EventSource API; preferred by engineering
- **Connection Scaling**: At peak, ~15,000 concurrent users; 15,000 persistent SSE connections on 3 notification worker pods is feasible with Node.js event loop architecture
- **Notification Fan-out**: Multi-tab users need to receive notifications on all open tabs; the SSE connection must support tab-level multiplexing

## Key Metrics & Data Points

- **Current in-app notification latency**: 0–60 seconds (polling-based)
- **Target latency**: < 2 seconds for real-time events
- **Peak concurrent users**: ~15,000
- **Estimated SSE connections at peak**: 15,000 × 1.3 (multi-tab factor) = ~19,500
- **Redis pub/sub for fan-out**: estimated < 1ms additional latency per event

## Preliminary Scorecard Hooks

- Current Polling Architecture: 1/5 - 60s latency unacceptable for real-time requirements
- SSE Technical Fit: 5/5 - Correct tool for server-push, low complexity, well-supported
- WebSocket Fit: 3/5 - Overpowered for use case, adds load balancing complexity
- Scaling Confidence at 15k Connections: 4/5 - Node.js SSE well-proven at this scale
- Fan-out Architecture: 4/5 - Redis pub/sub approach is clean, latency acceptable

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| SSE connection storms on reconnect after pod restart | Medium | Medium | Tech Lead | Implement jittered reconnect backoff on client EventSource wrapper | 2025-02-01 |
| Redis pub/sub becomes bottleneck at high fan-out volume | Medium | Low | Principal Engineer | Benchmark with 20k simulated connections before production release | 2025-02-15 |

## Decisions & Next Steps

### Decisions

- SSE (Server-Sent Events) selected over WebSockets for real-time notification delivery
- Redis pub/sub will be used for cross-pod notification fan-out
- Client will implement jittered exponential backoff for reconnection

### Action Items

- Tech Lead to write TDD for SSE notification delivery system (due 2025-01-28)
- Principal Engineer to prototype Redis pub/sub fan-out and run load test (due 2025-02-15)
- Product Manager to define the notification types that require real-time delivery (due 2025-01-21)

### Follow-ups

- TDD review before engineering kickoff
- Load test results review before production release decision
