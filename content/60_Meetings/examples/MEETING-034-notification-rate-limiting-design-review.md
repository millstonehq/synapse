---
id: MEETING-034
type: meeting
title: Notification Rate Limiting Design Review
status: draft
owner: Product Manager
created: '2025-02-26T23:33:10.890Z'
updated: '2025-10-02T03:39:36.814Z'
tags:
  - meeting
  - notification-service
summary: Notification Rate Limiting Design Review
company: NotificationService
topic: Notification Rate Limiting Design Review
meeting_date: '2024-11-17T00:24:40.005Z'
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

- **Project**: Notification Service - Rate Limiting Architecture
- **Topic**: Notification Rate Limiting Design Review
- **Date/Time**: 2024-11-17 00:24 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager
- **Context**: The current per-user rate limiting is implemented per-service, leading to inconsistent limits and users occasionally receiving 20+ notifications per day from different products. A centralized, enforced rate limiting layer is needed.

## Observations by Domain

- **Current State**: Each producing service implements its own rate limiting (or doesn't), resulting in no global enforcement and users being overwhelmed during high-activity periods
- **Redis Suitability**: Redis sliding window counters are the preferred implementation for low-latency rate limit checks at dispatch time; current Redis cluster has sufficient headroom
- **Exemption Model**: The design needs a clear exemption path for `critical` priority notifications that must bypass per-user limits
- **Backpressure**: When rate limits are hit, the current behavior is to drop the notification; the design review favored deferred queuing over dropping for `normal` priority
- **Configuration Flexibility**: Product teams want per-notification-type limits in addition to the global per-channel limits, requiring a layered configuration model

## Key Metrics & Data Points

- **Max notifications/user/day (observed)**: 47 during a recent campaign overlap
- **Per-user rate limit violations logged**: ~1,200/day (not currently enforced, just logged)
- **Redis P99 latency for rate limit check**: estimated 2ms (acceptable)
- **Notification types with custom limit requirements**: 6 identified by product teams

## Preliminary Scorecard Hooks

- Current Rate Limit Enforcement: 1/5 - Per-service only, no centralized enforcement
- Technical Feasibility of Redis Implementation: 5/5 - Proven pattern, existing cluster ready
- Configuration Model Completeness: 3/5 - Global limits clear, per-type limits need design
- Backpressure Strategy: 3/5 - Defer vs. drop decision needs product input
- Exemption Model: 4/5 - Critical priority exemption well-defined, secondary tiers need review

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Deferred queue grows unbounded during burst events | High | Medium | Tech Lead | Implement deferred queue TTL and size cap | 2024-12-15 |
| Rate limit misconfiguration silently drops critical notifications | High | Low | Principal Engineer | Add exemption validation and alerting for critical bypass | 2024-12-01 |
| Per-type limits increase configuration complexity and ops burden | Medium | Medium | Product Manager | Limit per-type overrides to explicitly approved notification types | 2024-12-20 |

## Decisions & Next Steps

### Decisions

- Centralized Redis sliding window rate limiting will be implemented at the Notification Service dispatch layer
- `critical` priority notifications are unconditionally exempt from per-user rate limits
- `normal` priority notifications are deferred (not dropped) when rate limits are hit, with a 24-hour TTL on deferred messages

### Action Items

- Tech Lead to write TDD for rate limiting implementation (due 2024-12-01)
- Principal Engineer to define configuration schema for per-channel and per-type limits (due 2024-11-24)
- Product Manager to collect per-type limit requirements from all product teams (due 2024-11-30)

### Follow-ups

- Design review of TDD before implementation begins
- Post-launch review of deferred queue behavior at 30 days
