---
id: MEETING-033
type: meeting
title: Push Notification Strategy Session
status: approved
owner: Engineering Manager
created: '2025-09-17T22:32:15.830Z'
updated: '2026-04-02T21:25:19.227Z'
tags:
  - meeting
  - notification-service
summary: Push Notification Strategy Session
company: NotificationService
topic: Push Notification Strategy Session
meeting_date: '2025-09-04T01:51:48.707Z'
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

- **Project**: Notification Service - Push Notification Strategy
- **Topic**: Push Notification Strategy Session
- **Date/Time**: 2025-09-04 01:51 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager
- **Context**: Push notification delivery rate has declined to 71% over the past quarter due to token churn and increased Android fragmentation; strategy needed for improvement.

## Observations by Domain

- **Token Management**: Device tokens are not being refreshed on app launch; stale tokens account for an estimated 18% of dispatch failures with `NotRegistered` errors
- **Payload Design**: Several push payloads exceed the 240-character body limit for Android, causing FCM truncation without error — the message appears sent but is displayed incorrectly
- **Priority Usage**: 60% of pushes are sent as `high` priority even for non-urgent content, causing increased battery complaints from users and potential FCM throttling
- **Opt-In Rate**: Push opt-in rate has dropped to 42% on iOS 17 due to the new permission prompt timing; product wants to evaluate a softer ask flow
- **Analytics Coverage**: Open-rate tracking is implemented for iOS but missing for Android; no click-through tracking on deep links from push

## Key Metrics & Data Points

- **Push delivery rate**: 71% — below 85% SLA target
- **Token invalid rate**: 18% of dispatches return `NotRegistered` or `InvalidRegistration`
- **High-priority push share**: 60% of all push sends (up from 35% six months ago)
- **iOS push opt-in rate**: 42% (down from 58% pre-iOS 17)
- **Android click tracking coverage**: 0% — not implemented

## Preliminary Scorecard Hooks

- Token Management: 2/5 - No refresh on app launch, high stale token rate
- Payload Compliance: 3/5 - iOS compliant, Android truncation issue undetected
- Priority Discipline: 2/5 - Overuse of high priority, no enforcement policy
- User Opt-In Strategy: 3/5 - Default prompt in use, no optimized ask flow
- Analytics Coverage: 2/5 - iOS open rates tracked, Android and click-through missing

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| FCM throttles high-priority sends at scale | High | Medium | Tech Lead | Audit and reclassify push priorities; enforce schema validation | 2025-09-30 |
| Stale token churn degrades delivery rate further | Medium | High | Principal Engineer | Implement token refresh on app launch in mobile client | 2025-10-15 |
| Android truncation creates broken UX invisibly | Medium | High | Tech Lead | Add payload length validation to Notification Service schema check | 2025-09-20 |

## Decisions & Next Steps

### Decisions

- Token refresh on app launch is a P0 fix for Q4 — assigned to mobile team
- Priority reclassification audit to be completed before next sprint ends
- Android click tracking will be added in Q4 alongside the token refresh work

### Action Items

- Tech Lead to implement payload length validation for Android push in Notification Service (due 2025-09-20)
- Principal Engineer to coordinate token refresh implementation with mobile team (due 2025-09-15)
- Product Manager to draft revised iOS opt-in ask flow for design review (due 2025-09-25)

### Follow-ups

- Monthly push delivery rate review until rate recovers above 85%
- Revisit priority usage policy once reclassification audit is complete
