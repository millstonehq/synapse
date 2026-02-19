---
id: MEETING-028
type: meeting
title: Real-Time Inventory Tracking Discussion
status: accepted
owner: Principal Engineer
created: '2025-02-02T04:35:46.622Z'
updated: '2026-05-04T07:31:29.336Z'
tags:
  - meeting
  - inventory-management
summary: Real-Time Inventory Tracking Discussion
company: InventoryManagement
topic: Real-Time Inventory Tracking Discussion
meeting_date: '2025-03-28T06:40:40.791Z'
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

- **Project**: Real-Time Inventory Capabilities
- **Topic**: Real-Time Inventory Tracking Discussion
- **Date/Time**: 2025-03-28 6:40 AM CT
- **Attendees (engineering)**: Principal Engineer, Tech Lead, Platform Engineer
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Discovery session to evaluate the feasibility and architecture options for providing sub-second inventory visibility to the order management system. Current data freshness is 5 minutes via ClickHouse; order management team is requesting <5 second freshness for high-demand SKUs.

## Observations by Domain

- **Current State**: Inventory data is published to ClickHouse every 5 minutes via a batch sync job; this is acceptable for analytics but too stale for real-time order decisions on high-demand SKUs
- **Event Stream Option**: The Kafka stock-movements topic already provides real-time events; order management could subscribe directly, but maintaining accurate state in order management from events is complex and error-prone
- **Read-Through Cache Option**: A Redis-backed read-through cache updated on every inventory write would provide <100ms freshness but adds complexity to the write path and introduces a new cache invalidation problem
- **WebSocket/Server-Sent Events**: Product team explored a push-based model where the inventory service pushes updates to subscribers; engineering flagged that this requires significant infrastructure work and a new subscription management layer
- **Scope**: Real-time freshness is needed for only ~5% of SKUs (high-demand items); applying real-time tracking to all 2.1M SKUs is unnecessary and would be expensive

## Key Metrics & Data Points

- **Current data freshness**: 5 minutes (ClickHouse batch)
- **Requested freshness by order management**: <5 seconds for high-demand SKUs
- **High-demand SKUs (>100 reservations/day)**: ~105,000 (5% of catalog)
- **Estimated Redis memory for high-demand SKU cache**: ~2GB (feasible with current cluster)
- **Kafka stock-movements event latency (p50)**: 200ms end-to-end

## Preliminary Scorecard Hooks

- Current Freshness: 2/5 - 5-minute lag is not acceptable for high-demand SKU order decisions
- Event Stream Approach: 3/5 - Technically sound but adds consumer state management complexity
- Read-Through Cache Approach: 4/5 - Low latency, feasible scope, manageable complexity
- Push Model Approach: 2/5 - High infrastructure effort for the expected benefit
- Scope Management: 4/5 - Limiting to high-demand SKUs keeps the problem tractable

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Cache invalidation complexity creates new inconsistency window | Medium | Medium | Tech Lead | Use write-through cache pattern with TTL fallback; document invalidation guarantees explicitly | 2025-05-01 |
| High-demand SKU classification changes frequently; cache set needs dynamic management | Medium | High | Platform Engineer | Use a configurable demand threshold query to dynamically determine cache members; recompute daily | 2025-05-15 |
| Redis cache adds latency to the inventory write path | Low | Low | Principal Engineer | Profile write path impact in staging; accept up to 10ms additional write latency | 2025-04-15 |

## Decisions & Next Steps

### Decisions

- Read-through Redis cache approach is selected as the implementation strategy for real-time inventory
- Scope is limited to SKUs with >100 reservations/day (approximately 105,000 SKUs)
- Push model (WebSocket/SSE) is rejected for this iteration due to infrastructure cost vs. benefit

### Action Items

- Write TDD for read-through Redis cache implementation (Tech Lead - 2025-04-11)
- Define high-demand SKU classification query and refresh schedule (Platform Engineer - 2025-04-11)
- Profile write path latency impact in staging (Principal Engineer - 2025-04-18)
- Share TDD with order management team for feedback (Product Manager - 2025-04-15)

### Follow-ups

- TDD review meeting: 2025-04-14
- Order management team briefing on expected data freshness guarantees
- Pilot with 1,000 high-demand SKUs before full rollout
