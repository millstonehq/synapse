---
id: PRD-020
type: prd
title: Push Notification Segmentation PRD
status: review
owner: Product Manager
created: '2024-12-25T02:26:00.184Z'
updated: '2025-02-27T15:12:20.595Z'
tags:
  - prd
  - notification-service
summary: Push Notification Segmentation PRD
related_tdds:
  - TDD-019
  - TDD-020
example: true
related_standards:
  - STANDARD-022
---

## Summary

Build audience segmentation capabilities for push notification campaigns, enabling marketing and product teams to target push notifications to specific user cohorts based on behavioral, demographic, and preference attributes. Currently all marketing push notifications are broadcast to the entire opted-in user base, leading to poor relevance and declining engagement rates.

## Goals

- Enable precise audience targeting for push notification campaigns to improve relevance and engagement
- Reduce push notification opt-out rates by decreasing the volume of irrelevant messages per user
- Provide self-service segment creation without requiring engineering for each campaign

## In Scope

- Segment builder with attribute-based filtering (user properties, behavioral events, device properties)
- Segment size estimation before campaign send
- Segment membership computed at send time (dynamic segments)
- Campaign scheduling: immediate, scheduled (specific date/time), or triggered (based on a user event)
- Per-campaign analytics: segment reach, delivery rate, CTR by segment
- Segment reuse: save and name segments for future campaigns
- Frequency cap enforcement per segment (limit sends per user per campaign)

## Out of Scope

- In-app message segmentation (separate initiative)
- SMS campaign segmentation (email or push only in v1)
- Predictive segments (ML-based lookalike audiences)
- Multi-variate A/B testing within segments (only 2-variant A/B in v1)

## Users and Flows

**Marketing campaign managers** create segments by building filter rules (e.g., "users who purchased in the last 30 days AND have push enabled AND are on iOS"). They preview the estimated reach, schedule the campaign, and monitor delivery metrics after send.

**Product managers** use triggered campaigns to send push notifications based on in-app behavioral events (e.g., "user opened the app 3 times without completing onboarding"). These use the event trigger delivery mechanism rather than scheduled sends.

The **Notification Routing Engine** receives campaign send jobs with a `segmentId` reference. It resolves the segment members at execution time (for scheduled campaigns) or at trigger time (for event-triggered campaigns) and enqueues individual push jobs for each member.

## Requirements

- Segment attribute filters: user account properties (plan tier, registration date, country), behavioral events (last active, feature usage), device properties (platform, OS version, app version)
- Logical operators: AND, OR, NOT for combining filter conditions
- Estimated reach shown in segment builder (refreshed on filter change, max 30-second staleness)
- Campaign scheduling: immediate send, date/time scheduled, or event-triggered
- Send rate limiting: configurable sends-per-second to avoid stampeding the provider
- Per-campaign frequency cap: each user receives a given campaign at most once (deduplication)
- Campaign results: delivered count, opened count, CTR by segment within 24 hours of send

## KPIs

- **Segmented push CTR improvement**: Segmented campaigns achieve > 30% higher CTR vs. broadcast pushes
- **Opt-out rate**: Push opt-out rate decreases by 15% within 6 months of launch for users receiving only segmented (not broadcast) campaigns
- **Self-service adoption**: > 75% of marketing push campaigns created without engineering assistance within 3 months

## Information Architecture

- This PRD in `100_Products/PRDs/`
- Preference API TDD [[TDD-019|TDD-019]] covers device token and preference data used in segment evaluation
- SMS Abstraction Layer TDD [[TDD-020|TDD-020]] — out of scope; this feature covers push only

## Data Model

- **Segment**: `id`, `name`, `filters[]` (attribute, operator, value), `createdBy`, `lastEstimatedSize`, `lastEstimatedAt`
- **Campaign**: `id`, `name`, `segmentId`, `templateSlug`, `templateVersion`, `schedule` (immediate|scheduled|triggered), `scheduledAt`, `triggerEvent`, `frequencyCap`, `status`
- **CampaignDelivery**: `campaignId`, `userId`, `deviceToken`, `status`, `deliveredAt`, `openedAt`

## Non-Functional

- Segment size estimation must complete within 30 seconds for segments up to 5M users
- Campaign send rate: configurable, default 10,000 messages/second
- Segment evaluation at send time must scale to 10M member segments within 5 minutes

## Constraints

- Must use existing Push Notification Gateway for delivery
- Segment data computed from existing user data warehouse; no new user data collection
- Budget: 2 engineers for 12 weeks

## Risks

- **Segment evaluation latency** for large segments may delay campaign delivery start. Mitigation: pre-compute segment membership for scheduled campaigns in a background job starting 30 minutes before scheduled send.
- **Frequency cap edge cases** for users who belong to multiple segments receiving the same campaign. Mitigation: deduplication at the campaign level using a Redis set of `(campaignId, userId)` pairs.

## Milestones

### M1: Segment Builder and Estimation (Weeks 1-5)
#### Deliverables
- Segment builder UI with attribute filter support
- Segment size estimation API
- Segment storage and management (CRUD)
#### Acceptance Criteria
- Segment with up to 10 filter conditions builds correctly
- Size estimation returns within 30 seconds for segments up to 5M users
- Saved segments can be reused across campaigns

### M2: Campaign Execution and Analytics (Weeks 6-12)
#### Deliverables
- Campaign send pipeline (immediate, scheduled, triggered)
- Send rate limiter and per-campaign frequency cap
- Campaign analytics (delivered, opened, CTR) within 24 hours
- End-to-end A/B test with control group support
#### Acceptance Criteria
- Campaign of 1M users completes delivery within 10 minutes at 10K msg/sec
- No user receives the same campaign more than once
- Campaign CTR data available in dashboard within 24 hours of send
