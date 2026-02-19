---
id: REPORT-030
type: report
title: Push Notification Engagement Report
status: review
owner: Notification Tech Lead
created: '2024-08-20T03:56:31.125Z'
updated: '2026-12-13T02:36:18.038Z'
tags:
  - report
  - notification-service
summary: Push Notification Engagement Report
company: NotificationService
report_month: 2026-11
report_type: analytics
overall_health: poor
confidence: low
active_initiatives_count: 4
critical_risks_count: 2
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Push opt-in rate (new users) | > 60% | 54% | Below target |
| Push click-through rate (CTR) | > 8% | 5.2% | Below target |
| Token validity rate | > 95% | 91.3% | Below target |
| Delivery acceptance (APNs/FCM) | > 99% | 98.7% | On target |
| Push-triggered app opens | - | 142K/month | Measured |

Push notification engagement is underperforming against targets. Click-through rate has declined 2.1 points quarter-over-quarter, and opt-in rates for new users have not recovered since iOS 14's opt-in prompt changes. Token validity is also lower than expected, indicating stale device tokens are not being pruned promptly.

## Key Highlights

- **Token cleanup job deployed**: A nightly job now scans for tokens with no successful delivery in 90 days and marks them inactive. Expected to improve token validity rate to > 95% within 30 days.
- **Notification copy A/B test results**: Personalized push notifications (including the user's name and action-specific copy) outperformed generic copy by 3.4 points in CTR across a 2-week A/B test.
- **iOS opt-in prompt placement tested**: Moved the notification permission prompt to occur after a user completes their first meaningful action (onboarding step 3) rather than at app launch. Opt-in rate improved from 52% to 58% in the test cohort.

## Active Initiatives

1. **Push notification segmentation PRD**: Approved. Engineering scoping in progress. Will enable audience targeting to reduce irrelevant sends.
2. **Rich push notifications**: Adding image and action button support for iOS and Android to improve CTR.
3. **Personalization engine integration**: Connecting notification copy generation to the user personalization service.
4. **Opt-in prompt optimization**: Expanding the improved opt-in prompt placement to all new user registrations.

## Incidents

No push delivery incidents this period.

## Risks

- **High**: CTR decline may indicate notification fatigue. Without segmentation, continued volume increases will further depress engagement.
- **High**: iOS token validity degradation may reflect a bug in the APNs feedback processing. Investigation underway.

## Next Month Focus

- Begin push notification segmentation engineering
- Deploy rich push notification support (iOS first)
- Roll out improved opt-in prompt placement to 100% of new users
- Complete APNs feedback processing investigation
