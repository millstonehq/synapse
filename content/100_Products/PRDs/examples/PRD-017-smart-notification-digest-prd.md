---
id: PRD-017
type: prd
title: Smart Notification Digest PRD
status: approved
owner: Senior PM
created: '2024-04-15T17:35:08.267Z'
updated: '2025-06-10T06:50:49.217Z'
tags:
  - prd
  - notification-service
summary: Smart Notification Digest PRD
related_tdds:
  - TDD-020
  - TDD-019
example: true
related_standards:
  - STANDARD-024
---

## Summary

Build a smart notification digest feature that intelligently aggregates low-priority notifications into scheduled summary emails and push notifications rather than delivering them individually. Users who receive high notification volumes currently experience fatigue, leading to opt-outs. The digest feature reduces individual notification frequency while maintaining information delivery, improving both user satisfaction and long-term opt-in rates.

## Goals

- Reduce notification fatigue by consolidating low-priority notifications into daily or weekly digests
- Decrease notification-driven push opt-out rates by giving users a lower-volume option
- Maintain notification value and click-through rates by presenting relevant grouped summaries

## In Scope

- Daily and weekly digest schedules, configurable per user
- Digest includes all LOW and NORMAL priority notifications from the window that the user has not yet opened
- Push and email digest delivery channels
- Digest scheduling respects user quiet hours and timezone
- Per-category digest grouping (e.g., "3 order updates", "5 product recommendations")
- Opt-in to digest mode as an alternative to individual notification delivery

## Out of Scope

- Real-time or hourly digest (minimum digest window is 24 hours)
- SMS digest format
- Machine-learning-based digest scheduling (rule-based scheduling only in v1)
- Retroactive digest for notifications already delivered

## Users and Flows

**High-volume notification users** (users who receive > 10 notifications per day) are the primary target. These users are presented with the digest option in notification settings after receiving more than 10 notifications in a week. They can choose "Daily digest" or "Weekly digest" as an alternative to individual delivery for LOW/NORMAL priority notifications.

**All users** can access digest settings in the notification preference center and opt in at any time. Users in digest mode still receive HIGH and CRITICAL priority notifications immediately; only LOW and NORMAL are held for digest.

**The digest scheduler** runs as a background job, querying users whose digest window has elapsed, aggregating their pending notifications, rendering the digest template, and dispatching via the normal notification pipeline.

## Requirements

- Users can select daily (9am local time) or weekly (Monday 9am local time) digest schedules
- HIGH and CRITICAL priority notifications are always delivered immediately regardless of digest settings
- Digest must include a count and summary per notification category
- Each digest entry must link to the full notification detail (deep link or notification center)
- Digest template must be responsive and readable on mobile email clients
- Digest scheduler must complete digest generation for all pending users within 30 minutes of the scheduled send time

## KPIs

- **Digest adoption**: > 15% of users with > 10 daily notifications opt into digest within 3 months of launch
- **Push opt-out reduction**: Users in digest mode should have 20% lower push opt-out rates vs. control group
- **Digest click-through rate**: > 12% of digest emails generate at least one in-app session

## Information Architecture

- PRD in `100_Products/PRDs/`
- TDD for digest scheduler in `90_Architecture/TDDs/`
- Notification Preference API TDD: [[TDD-019|TDD-019]] handles preference storage for digest settings
- SMS Provider Abstraction TDD: [[TDD-020|TDD-020]] is not applicable; digests are email/push only

## Data Model

- **DigestPreference**: `userId`, `digestEnabled`, `schedule` (daily|weekly), `preferredDeliveryTime`, `timezone`, `updatedAt`
- **PendingDigestEntry**: `userId`, `notificationId`, `notificationType`, `category`, `summaryText`, `deepLinkUrl`, `pendingSince`
- **DigestJob**: `jobId`, `userId`, `schedule`, `scheduledAt`, `processedAt`, `notificationCount`, `deliveryStatus`

## Non-Functional

- Digest scheduler must handle 500,000 users enrolled in digest mode without exceeding 30-minute generation window
- Digest email rendering must use the versioned template system (no unversioned template references)
- PendingDigestEntry records older than 7 days are expired and included in the next digest regardless

## Constraints

- Must use existing Notification Preference Store for digest preference storage
- Digest scheduler must not interfere with real-time notification throughput
- Budget: 1 engineer for 6 weeks

## Risks

- **Digest scheduler performance** at 500K enrolled users may exceed the 30-minute window. Mitigation: use parallel digest generation workers scaled by cohort.
- **User confusion** about why HIGH/CRITICAL notifications still arrive immediately while LOW/NORMAL are digested. Mitigation: clear in-app explainer during digest opt-in flow.

## Milestones

### M1: Preference Storage and Scheduler (Weeks 1-3)
#### Deliverables
- Digest preference storage in Notification Preference Store
- PendingDigestEntry accumulation for users in digest mode
- Digest scheduler background job
#### Acceptance Criteria
- Users can enable/disable digest and set schedule in preference center
- LOW/NORMAL notifications for digest users are held in PendingDigestEntry rather than dispatched immediately
- Scheduler generates and dispatches digest for all enrolled users within 30 minutes

### M2: Digest Template and Delivery (Weeks 4-6)
#### Deliverables
- Responsive digest email template (versioned)
- Push digest notification with count summary
- End-to-end testing with real notification types
#### Acceptance Criteria
- Digest email renders correctly on iOS Mail, Gmail, and Outlook
- Push digest shows correct unread count and launches notification center on tap
- High-volume user A/B test shows measurable improvement in opt-out rates
