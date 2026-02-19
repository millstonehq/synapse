---
id: TDD-016
type: tdd
title: Notification Routing Engine TDD
status: approved
owner: Senior Engineer
created: '2024-01-17T11:57:28.567Z'
updated: '2025-11-09T22:13:09.587Z'
tags:
  - tdd
  - notification-service
summary: Notification Routing Engine TDD
related_adrs:
  - ADR-0016
  - ADR-0017
example: true
---

## Summary

Design the Notification Routing Engine — a TypeScript microservice that accepts inbound notification requests and applies a deterministic decision pipeline to select a delivery channel (email, push, or SMS) for each message. The engine must process 500 routing decisions per second at peak, maintain 99.9% availability, and respect user preferences, quiet hours, and per-channel rate limits with sub-100ms decision latency.

This design implements the channel selection logic referenced in [[ADR-0016|ADR-0016: Use Firebase for Push Notifications]] and applies the template resolution strategy defined in [[ADR-0017|ADR-0017: Implement Template Versioning System]].

## Overview

The Notification Routing Engine is a stateless processing service that evaluates routing rules at ingestion time. It does not perform delivery itself — it determines the correct channel and enqueues the prepared notification to the appropriate downstream queue.

Key design principles:
- **Deterministic pipeline**: Routing decisions follow a fixed evaluation order (opt-out → quiet hours → rate limit → channel health → preference rank). No ambiguity in channel selection.
- **Fail-safe behavior**: If any pipeline step encounters an error (e.g., Redis unavailable), the engine uses the most conservative safe default (prefer delivering to a degraded channel over dropping the notification for HIGH/CRITICAL priority).
- **Stateless decisions**: All state required for routing decisions is fetched at request time from the Notification Preference Store and channel health cache. No in-process state between requests.
- **Observability**: Every routing decision is logged with the outcome reason for debugging mis-routed notifications.

## Architecture

- **HTTP Ingestion Layer**: REST endpoint `POST /v1/notifications` accepts notification requests from producers. Validates payload schema, extracts priority and channel preferences, and enqueues the routing job.
- **RabbitMQ Consumer Layer**: Also accepts routing jobs from the internal queue for async processing from other services.
- **Decision Pipeline Service**: Core business logic. Executes the 6-step routing pipeline (opt-out, channel opt-out, quiet hours, frequency cap, channel health, preference rank) and returns a `RoutingDecision`.
- **Channel Dispatcher**: Takes the `RoutingDecision` output and enqueues the notification to the target channel's delivery queue with the correct priority exchange.
- **Preference Cache**: Read-through Redis cache over the Notification Preference Store API. Cache miss latency budget: 80ms.

## Information Model

- **NotificationRequest**: `id`, `producerId`, `userId`, `notificationType`, `priority`, `requestedChannels[]`, `templateSlug`, `templateVersion`, `variableMap`, `deduplicationKey`, `createdAt`
- **RoutingDecision**: `notificationId`, `channel` (email|push|sms|suppressed), `reason`, `deliverAfter` (null unless deferred), `decidedAt`
- **UserPreferenceSnapshot**: `userId`, `globalOptOut`, `channelOptOuts{}`, `quietHours{}`, `frequencyCaps{}`, `channelRanking[]`, `fetchedAt`
- **ChannelHealthStatus**: `channel`, `healthy`, `circuitBreakerState`, `checkedAt`

## Interfaces

- `POST /v1/notifications` — Accept and enqueue a notification routing request; returns `202 Accepted` with `notificationId`
- `GET /v1/notifications/{id}` — Return the routing decision and current delivery status for a notification
- `GET /v1/health` — Liveness and readiness probe; checks Redis and RabbitMQ connectivity
- Internal: `RoutingDecisionService.decide(request, preferences, channelHealth) → RoutingDecision`

## Files and Layout

```
src/
  api/
    routes/notification.routes.ts   - HTTP ingestion endpoint
    middleware/validate.ts           - Request schema validation
  services/
    routing-decision.service.ts      - 6-step routing pipeline
    channel-dispatcher.service.ts    - Queue routing for decisions
    preference-cache.service.ts      - Redis read-through cache
  models/
    notification-request.ts          - Input type definitions
    routing-decision.ts              - Decision output types
    user-preference.ts               - Preference snapshot type
  consumers/
    notification.consumer.ts         - RabbitMQ inbound consumer
  config/
    channel-health.config.ts         - Channel health check config
migrations/
  001_routing_audit_log.sql          - Routing decision audit table
```

## Work Plan

1. **Phase 1 - Foundation (Week 1)**: Database schema for routing audit log, preference cache service, RabbitMQ connection setup
2. **Phase 2 - Decision Pipeline (Week 2)**: Implement all 6 routing pipeline steps with unit tests for each step
3. **Phase 3 - HTTP Ingestion (Week 3)**: REST endpoint, request validation, response format, integration tests
4. **Phase 4 - Channel Dispatching (Week 4)**: Priority queue routing, dead-letter handling, dispatch confirmation
5. **Phase 5 - Observability (Week 5)**: Routing decision logging, metrics (decision latency, suppression rate per step), alerting rules
6. **Phase 6 - Load Testing (Week 6)**: Validate 500 decisions/second target, tune cache hit ratios, finalize HPA configuration

## Risks and Mitigations

- **Risk**: Preference Store API latency causes routing pipeline to exceed 100ms budget. **Mitigation**: Redis read-through cache with 5-minute TTL should keep >95% of requests under 20ms. Cache miss path has 80ms budget; if exceeded, use cached defaults.
- **Risk**: Incorrect quiet hours timezone handling causes notifications to be delivered outside user intent. **Mitigation**: Store and evaluate all quiet hours in UTC. Use a well-tested timezone library (luxon) for all local time calculations.
- **Risk**: Frequency cap race conditions under concurrent requests for the same user. **Mitigation**: Use Redis INCR with atomic expiry to implement sliding window counters. Accept small over-count risk rather than distributed locking overhead.
