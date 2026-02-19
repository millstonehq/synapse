---
id: TDD-019
type: tdd
title: Notification Preference API TDD
status: accepted
owner: Senior Engineer
created: '2025-10-31T10:58:06.809Z'
updated: '2025-11-15T13:48:11.334Z'
tags:
  - tdd
  - notification-service
summary: Notification Preference API TDD
related_adrs:
  - ADR-0017
  - ADR-0015
example: true
---

## Summary

Design the Notification Preference API — the RESTful service that stores, retrieves, and enforces per-user notification preferences for the Notification Platform. The API must support global opt-out, per-channel opt-out, per-category subscriptions, quiet hours, and daily/weekly frequency caps. It must serve read requests at P95 < 20ms (cache hit) and propagate preference changes to the cache within 30 seconds.

The preference data model is designed to support the per-category unsubscribe groups needed for compliance with email regulations referenced in [[ADR-0015|ADR-0015: Adopt Multi-Provider Email Strategy]] and the channel-level controls required by the template versioning system in [[ADR-0017|ADR-0017: Implement Template Versioning System]].

## Overview

The Notification Preference API is a TypeScript microservice with a PostgreSQL persistence layer and a Redis read-through cache. It is the authoritative source of preference data for all delivery services. Delivery services call the preference API (or its cache) on every routing decision.

Key design principles:
- **Read-optimized**: The overwhelming majority of traffic is reads (routing decisions); writes (user preference updates) are infrequent. The cache is sized and tuned for read performance.
- **Audit trail**: Every preference change is appended to an immutable `preference_events` table. This supports compliance auditing and debugging of unexpected suppression.
- **Atomic updates**: Preference updates are applied as a complete document replacement (not partial patches) to avoid partial-update race conditions.
- **Event-driven cache invalidation**: Preference changes publish events to RabbitMQ. Downstream services with their own preference caches can invalidate proactively.

## Architecture

- **REST API Layer**: CRUD endpoints for user preferences. JWT authentication for user-facing paths; service token authentication for internal service reads.
- **Preference Service**: Business logic for preference validation, merge rules (global opt-out overrides channel opt-out), and quiet hours normalization (stored as UTC offsets).
- **Cache Layer**: Redis stores serialized `UserPreference` documents keyed by `user:{userId}:preferences`. TTL: 5 minutes. Explicit invalidation on write via Redis DEL command.
- **Repository Layer**: PostgreSQL stores the canonical preference document per user and the immutable `preference_events` audit log.
- **Event Publisher**: After each preference write, publishes a `preference.updated` event to the RabbitMQ `notifications.preferences` exchange.

## Information Model

- **UserPreference**: `userId`, `globalOptOut`, `channelOptOuts{email, push, sms}`, `categorySubscriptions{[category]: boolean}`, `quietHours{enabled, startUtcOffset, endUtcOffset, timezone}`, `frequencyCaps{daily, weekly}`, `channelRanking[]`, `updatedAt`
- **PreferenceEvent**: `eventId`, `userId`, `changeType` (opt-out|opt-in|quiet-hours|frequency-cap|ranking), `previousValue`, `newValue`, `changedBy`, `createdAt`

## Interfaces

- `GET /v1/users/{userId}/preferences` — Return full preference document for a user
- `PUT /v1/users/{userId}/preferences` — Replace full preference document (atomic)
- `PATCH /v1/users/{userId}/preferences/channels/{channel}/opt-out` — Convenience endpoint for channel opt-out
- `GET /v1/users/{userId}/preferences/events` — Return audit log of preference changes
- `DELETE /v1/users/{userId}/preferences` — Reset preferences to platform defaults (for GDPR erasure workflows)

## Files and Layout

```
src/
  api/
    routes/preferences.routes.ts        - Preference CRUD endpoints
    routes/preference-events.routes.ts  - Audit log endpoint
    middleware/auth.middleware.ts        - JWT and service token auth
  services/
    preference.service.ts               - Business logic, validation, merge rules
    cache.service.ts                    - Redis read-through cache
    event-publisher.service.ts          - RabbitMQ event publishing
  repositories/
    preference.repository.ts            - PostgreSQL preference CRUD
    preference-event.repository.ts      - Audit log append
  types/
    user-preference.ts
    preference-event.ts
migrations/
  001_preferences.sql
  002_preference_events.sql
```

## Work Plan

1. **Phase 1 - Schema and Repository (Week 1)**: Database schema, PostgreSQL repositories for preferences and events
2. **Phase 2 - Business Logic (Week 2)**: Preference validation rules, merge logic, quiet hours normalization
3. **Phase 3 - REST API (Week 3)**: All endpoints with authentication middleware, request validation
4. **Phase 4 - Cache Layer (Week 4)**: Redis read-through cache, explicit invalidation on write, cache hit rate monitoring
5. **Phase 5 - Event Publishing (Week 5)**: RabbitMQ event publishing, integration tests for end-to-end cache propagation

## Risks and Mitigations

- **Risk**: Cache invalidation race condition causes stale preferences to be used for a routing decision immediately after a user opts out. **Mitigation**: Accept a maximum 30-second window of stale data; document this in the SLA. For GDPR erasure, use synchronous cache invalidation rather than TTL expiry.
- **Risk**: Preference document grows too large as category subscriptions scale. **Mitigation**: Limit the `categorySubscriptions` map to 100 entries per user; prune inactive categories quarterly.
