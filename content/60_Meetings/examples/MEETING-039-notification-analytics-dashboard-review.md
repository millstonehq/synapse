---
id: MEETING-039
type: meeting
title: Notification Analytics Dashboard Review
status: draft
owner: Product Manager
created: '2025-09-08T10:07:31.117Z'
updated: '2025-09-22T09:35:49.760Z'
tags:
  - meeting
  - notification-service
summary: Notification Analytics Dashboard Review
company: NotificationService
topic: Notification Analytics Dashboard Review
meeting_date: '2025-09-24T18:45:28.730Z'
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

- **Project**: Notification Service - Analytics Dashboard Review
- **Topic**: Notification Analytics Dashboard Review
- **Date/Time**: 2025-09-24 18:45 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager
- **Context**: Quarterly review of notification analytics dashboards to assess data completeness, metric accuracy, and identify gaps before the Q4 planning cycle.

## Observations by Domain

- **Email Metrics**: Delivery rate, open rate, and click rate are tracked but all via SendGrid's tracking pixels; no first-party open tracking, creating blind spots if users block pixels
- **Push Metrics**: iOS delivery and open rates tracked; Android open rate not instrumented (missing acknowledgment callback from Android client)
- **SMS Metrics**: Delivery confirmations tracked; no click tracking on URLs in SMS (no link shortener/tracker configured)
- **In-App Metrics**: View and dismiss events tracked; click-through on action links not consistently firing — 30% of click events are missing
- **Cross-Channel Attribution**: No unified user-level view across channels; cannot determine which channel drove a conversion for a multi-channel campaign

## Key Metrics & Data Points

- **Email open rate (pixel-based)**: 22% average — suspect undercounting due to pixel blocking
- **Android push open rate instrumentation**: 0% — not implemented
- **SMS link click tracking**: 0% — no link tracker configured
- **In-app click event loss rate**: ~30% — intermittent client-side event loss
- **Cross-channel attribution**: not available

## Preliminary Scorecard Hooks

- Email Analytics Completeness: 3/5 - Delivery/open/click tracked but pixel-dependent
- Push Analytics Completeness: 2/5 - iOS covered, Android open rate missing
- SMS Analytics Completeness: 2/5 - Delivery confirmed, click tracking absent
- In-App Analytics Completeness: 3/5 - View/dismiss tracked, click loss needs fix
- Cross-Channel Attribution: 1/5 - No unified view, blocks campaign optimization

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Android push open rate gap prevents delivery SLA measurement | High | Certain | Tech Lead | Implement server-side open acknowledgment callback in Android SDK | 2025-10-31 |
| In-app click event loss causes inaccurate CTR data | Medium | High | Principal Engineer | Add retry with local buffer to client-side event sender | 2025-10-15 |

## Decisions & Next Steps

### Decisions

- Android push open rate instrumentation is a P1 fix for Q4
- In-app click event reliability fix is also P1 due to data integrity impact
- Cross-channel attribution will be scoped as a Q1 project — too large for Q4

### Action Items

- Tech Lead to implement Android push open acknowledgment callback (due 2025-10-31)
- Principal Engineer to fix in-app click event loss with client-side buffering (due 2025-10-15)
- Product Manager to scope cross-channel attribution feature for Q1 planning (due 2025-10-07)

### Follow-ups

- Review analytics completeness metrics 30 days after fixes are deployed
- Q1 planning: include cross-channel attribution as a standalone initiative
