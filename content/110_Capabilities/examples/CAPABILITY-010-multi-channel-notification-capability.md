---
id: CAPABILITY-010
type: capability
title: Multi-Channel Notification Capability
status: approved
owner: Head of Engineering
created: '2025-01-15T08:08:47.854Z'
updated: '2026-07-30T13:47:51.486Z'
tags:
  - capability
  - notification-service
summary: Multi-Channel Notification Capability
evidence_links:
  - PROCESS-021
  - PROCESS-023
  - STANDARD-023
example: true
---

## Domain

- Delivery of notifications across email, push, and SMS channels with unified routing logic
- Channel selection, fallback, and opt-out enforcement per user preference
- Producer-facing API abstracting channel-specific delivery details
- Operational monitoring of per-channel delivery rates and failure modes

## Maturity (0-5)

**Current score: 3 / 5 (Defined)**

- **Email delivery**: 3/5 - Dual-provider strategy (SendGrid/Mailgun) with circuit breaker is operational; template versioning and suppression lists are in place but bounce handling automation is incomplete
- **Push dispatch**: 3/5 - FCM and APNs adapters support batching and priority routing; token invalidation is automated; iOS rich-media push is not yet supported
- **SMS dispatch**: 2/5 - Single primary provider (Twilio) with Vonage failover exists but failover is manual; delivery receipts are logged but not surfaced in the analytics dashboard
- **Channel routing engine**: 4/5 - Preference-aware routing with fallback chains is fully automated; quiet hours and frequency caps are enforced; A/B channel experiments are not yet supported

**Gap to Level 4**: Automate SMS failover, add per-channel delivery SLA dashboards, and implement channel-level A/B experimentation.

## Metrics

- Email delivery rate: 98.4% (target > 99%)
- Push delivery rate: 96.1% (target > 97%); invalid token invalidation within 60 seconds
- SMS delivery rate: 94.2% (target > 96%); manual failover adds ~8-minute delay
- Cross-channel fallback activation rate: 3.1% of routed notifications fall back to secondary channel
- Mean time to route a notification from submission to channel enqueue: 120ms P99

## Evidence Links

- [[PROCESS-021|Notification Channel Onboarding Process]] - Governs onboarding new producers to the routing API
- [[PROCESS-023|Channel Opt-Out Compliance Process]] - Defines how opt-out signals are propagated to all channel delivery services
- [[STANDARD-023|Notification Delivery Standards]] - Specifies SLA targets, retry policies, and suppression list requirements per channel

## Notes

- SMS channel maturity lags email and push due to late addition of Vonage as a secondary provider; automated failover is on the Q3 roadmap
- Channel routing logic is the highest-maturity component and can serve as a reference design for future channel additions (e.g., in-app, WhatsApp)
