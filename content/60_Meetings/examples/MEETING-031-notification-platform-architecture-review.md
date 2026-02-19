---
id: MEETING-031
type: meeting
title: Notification Platform Architecture Review
status: accepted
owner: Engineering Manager
created: '2024-06-15T16:18:40.025Z'
updated: '2025-04-01T22:04:15.158Z'
tags:
  - meeting
  - notification-service
summary: Notification Platform Architecture Review
company: NotificationService
topic: Notification Platform Architecture Review
meeting_date: '2026-07-26T12:07:56.314Z'
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

- **Project**: Notification Service Platform
- **Topic**: Notification Platform Architecture Review
- **Date/Time**: 2026-07-26 12:00 PM UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Mid-year architecture review following rapid growth in notification volume (email, push, SMS). Team is evaluating scalability of the current fanout model and reliability of delivery guarantees ahead of a planned enterprise tier launch.

## Observations by Domain

- **Delivery Pipeline**: Current synchronous fanout architecture processes notifications inline with request handling, creating latency spikes during traffic bursts. The pipeline lacks per-channel circuit breakers, causing SMS provider failures to block email delivery.
- **Channel Abstraction**: Email (SendGrid), push (FCM/APNs), and SMS (Twilio) are wired directly to business logic rather than behind a unified channel interface. Adding a new provider requires changes in multiple service layers.
- **Template Engine**: Handlebars-based template rendering is embedded in the API service rather than isolated as a discrete step. No caching of compiled templates, which causes redundant compilation on every notification send.
- **Preference Management**: User notification preferences are stored in a single JSONB column with no schema enforcement. Reads require deserializing the full preference object even for single-channel lookups.
- **Observability**: Per-channel delivery success rates are tracked only at the batch level. Individual notification outcomes are not persisted beyond a 7-day log retention window, preventing long-term deliverability analysis.
- **Retry and Dead-Letter**: Retry logic is implemented independently per channel with inconsistent backoff strategies. There is no centralized dead-letter queue, making it difficult to audit or reprocess failed notifications.

## Key Metrics & Data Points

- **Daily notification volume**: ~4.2 million across all channels (email 62%, push 31%, SMS 7%)
- **P99 delivery latency (email)**: 1,840 ms, target is under 500 ms
- **SMS provider failure blast radius**: last outage caused 18% drop in email throughput due to shared thread pool
- **Template compilation cache hit rate**: 0% (no caching implemented)
- **Preference lookup query time (P95)**: 220 ms due to full JSONB deserialization
- **Unrecoverable failed notifications (30-day)**: 14,300 with no reprocessing path

## Preliminary Scorecard Hooks

- Delivery Pipeline: 2/5 - Synchronous fanout without channel isolation creates systemic blast-radius risk at scale
- Channel Abstraction: 2/5 - Provider coupling throughout the codebase makes extensibility costly and error-prone
- Template Engine: 3/5 - Functional but missing compilation caching and lifecycle separation from the API layer
- Preference Management: 3/5 - Works at current scale but JSONB schema drift and read cost will become critical issues
- Observability: 2/5 - Batch-level metrics insufficient for SLA commitments; short log retention limits incident analysis
- Retry and Dead-Letter: 2/5 - Per-channel inconsistency and no centralized dead-letter queue are operational liabilities

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| SMS provider outage continues to degrade email delivery due to shared thread pool | High | High | Principal Engineer | Introduce per-channel isolated worker pools with independent circuit breakers | 2026-08-31 |
| JSONB preference schema drift causes silent read errors as feature set expands | High | Medium | Tech Lead | Migrate preference model to normalized rows with versioned schema; add validation layer | 2026-09-15 |
| No dead-letter queue means failed notifications are permanently unrecoverable | Medium | High | Tech Lead | Implement centralized dead-letter queue (SQS or equivalent) with replay tooling | 2026-08-22 |
| Template compilation overhead will worsen as notification volume grows | Medium | Medium | Principal Engineer | Add compiled-template cache with TTL and invalidation on template publish events | 2026-09-01 |

## Decisions & Next Steps

### Decisions

- Async fanout via a queue-backed worker model is the target architecture; synchronous inline processing will be deprecated after worker infrastructure is validated in staging.
- Channel abstraction layer will be introduced as an interface with adapter implementations per provider, decoupling business logic from SDK specifics.
- Dead-letter queue is a prerequisite for the enterprise tier launch and will be scoped as a blocking dependency.

### Action Items

- Draft TDD for async fanout architecture with per-channel worker pools (Principal Engineer - 2026-08-05)
- Prototype channel abstraction interface and SendGrid adapter as proof of concept (Tech Lead - 2026-08-12)
- Stand up SQS dead-letter queue in staging and instrument replay tooling (Tech Lead - 2026-08-22)
- Implement compiled-template cache with Redis backing in the API service (Principal Engineer - 2026-09-01)
- Create schema migration plan for notification preferences table normalization (Engineering Manager - 2026-08-15)

### Follow-ups

- Reconvene in 4 weeks to review async fanout TDD and channel abstraction prototype
- QA Lead to define acceptance criteria for delivery SLA validation before enterprise tier launch
- Product Manager to confirm notification volume projections for Q4 to inform worker pool sizing
