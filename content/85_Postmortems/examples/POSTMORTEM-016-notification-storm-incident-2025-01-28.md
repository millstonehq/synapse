---
id: POSTMORTEM-016
type: postmortem
title: Notification Storm Incident 2025-01-28
status: approved
owner: Incident Commander
created: '2025-12-22T13:02:46.272Z'
updated: '2026-04-24T12:13:35.213Z'
tags:
  - postmortem
  - notification-service
summary: Notification Storm Incident 2025-01-28
incident_number: INC-357
severity: SEV-1
incident_date: '2026-12-04'
detection_time: '2026-06-28T20:27:24.004Z'
resolution_time: '2024-03-24T17:15:13.229Z'
total_duration: ~15 minutes
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-040
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On January 28, 2025, the Notification Platform experienced a 47-minute notification storm in which a misconfigured retry policy in the Notification Routing Engine caused approximately 840,000 duplicate notifications to be dispatched to users within a 12-minute window. Users received between 5 and 20 duplicate push notifications and emails for the same underlying event. No notifications were permanently lost, but the storm caused a flood of user complaints and temporarily saturated the email provider rate limits.

The root cause was a code change deployed that morning which set the retry backoff multiplier to 0 instead of 2, causing failed routing decisions to be retried immediately and indefinitely rather than with exponential backoff. The defect was introduced during a refactor of the retry configuration and was not caught in code review or integration tests.

## Timeline

- **09:14** - Routing engine deployment containing the misconfigured retry backoff goes to production via ArgoCD
- **09:15** - First batch of notifications processed normally
- **09:22** - A transient Redis cache miss causes a subset of routing decisions to fail and enter retry
- **09:22** - Failed routing decisions begin retrying at zero-delay intervals, creating a tight retry loop
- **09:25** - Push notification gateway queue depth spikes from 200 to 45,000 messages within 3 minutes
- **09:27** - `notification_queue_depth_critical` alert fires. On-call engineer acknowledges
- **09:28** - SendGrid reports rate limit exceeded. Email delivery begins queuing
- **09:31** - On-call identifies queue storm in progress, posts in #notifications-incidents
- **09:35** - On-call checks recent deploys. Identifies routing engine deploy at 09:14 as likely cause
- **09:38** - Routing engine rolled back via ArgoCD
- **09:40** - Queue depth begins declining. New notifications no longer storm-affected
- **09:52** - Queue depth returns to baseline. Email provider rate limit cleared
- **10:14** - Incident formally closed after 20-minute stable observation window

## Impact

- **Duration**: 47 minutes (09:22 - 10:14 UTC)
- **Notifications affected**: ~840,000 duplicate sends dispatched
- **Users impacted**: ~62,000 users received 5-20 duplicates each
- **Provider cost impact**: ~$1,400 in excess SendGrid and FCM charges for duplicate sends
- **User complaints**: 218 support tickets opened within 2 hours of the incident
- **SLA impact**: Monthly availability unaffected (platform remained up), but user experience severely degraded

## Root Cause Analysis

1. **Misconfigured retry backoff**: The `retryBackoffMultiplier` was set to `0` in the routing engine config during a refactor of the retry policy module. A value of `0` caused the computed backoff delay to always be `0ms`, creating an immediate retry loop. The intended value was `2` (exponential backoff).

2. **Missing configuration validation**: The retry configuration struct had no validation that `retryBackoffMultiplier` must be greater than `0`. A validator would have caught this at startup and prevented the deployment from succeeding.

## Resolution

1. Identified the misconfigured retry backoff value by reviewing the deployment diff
2. Rolled back the routing engine to the previous version via ArgoCD
3. Monitored queue depth recovery for 20 minutes to confirm storm subsided
4. Issued user-facing apology notification to affected users via in-app message
5. Worked with SendGrid to waive the excess charges incurred during the incident

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add validation: `retryBackoffMultiplier` must be > 0 | Notification Engineering | P1 | 2025-02-04 | Completed |
| Add integration test for retry storm prevention | Notification Engineering | P1 | 2025-02-07 | Completed |
| Add `queue_depth_storm_rate` alert (depth increase > 5x in 60s) | SRE | P2 | 2025-02-10 | Completed |
| Add duplicate-send rate alert (sends per user per event > 3 in 10 min) | SRE | P2 | 2025-02-14 | In progress |
| Review all retry configuration defaults across notification services | Notification Engineering | P3 | 2025-02-28 | Pending |

## Lessons Learned

- **What went well**: Queue depth alert fired within 3 minutes of the storm starting. Rollback was completed in under 10 minutes of root cause identification.
- **What went poorly**: No configuration validation prevented the bad value from deploying. The integration test suite had no test case for retry storm behavior.
- **What was lucky**: The storm lasted only 12 minutes before the rollback stopped it. A longer window would have exhausted provider rate limits entirely and delayed all legitimate notifications by hours.
