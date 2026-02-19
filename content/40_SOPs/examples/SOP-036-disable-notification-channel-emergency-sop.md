---
id: SOP-036
type: sop
title: Disable Notification Channel Emergency SOP
status: approved
owner: SRE Lead
created: '2024-10-01T10:15:57.497Z'
updated: '2025-06-29T02:05:57.072Z'
tags:
  - sop
  - notification-service
summary: Disable Notification Channel Emergency SOP
related_process: PROCESS-022
related_systems:
  - SYSTEM-018
example: true
---

## Preconditions

- An active incident or emergency condition requires immediate cessation of sends on a specific notification channel (e.g., runaway loop sending thousands of emails, SMS being sent to wrong recipients)
- You have access to the Notification Service feature flag system or admin API to disable channels
- The on-call engineer and Platform Lead have been notified of the situation
- The scope of the emergency is understood (which channel, which notification types, estimated impact)

## Materials/Access

- Notification Service feature flag console or admin API with channel disable permissions
- Monitoring dashboard to confirm send volume drops to zero after disabling
- Slack access to `#notifications-incidents` for real-time communication
- Access to the queue management console to inspect and pause the notification queue if needed

## Procedure

1. Post in `#notifications-incidents`: "EMERGENCY: Disabling [channel] notifications. Reason: [brief description]. ETA: immediate."
2. In the Notification Service feature flag console, set the feature flag for the affected channel to `disabled`. This prevents new notifications from being dispatched.
3. If the notification queue has already accumulated a large backlog of items that must not be delivered, pause the consumer for the affected channel queue.
4. Verify on the monitoring dashboard that the send volume for the affected channel drops to zero within 2 minutes of the disable action.
5. Check the provider dashboard (SendGrid, Twilio) to confirm no further sends are being accepted from the Notification Service.
6. Notify stakeholders (product, customer support) of the channel disable and expected impact to user-facing functionality.
7. Begin root cause investigation while the channel remains disabled.
8. When the root cause is resolved and the fix is deployed, re-enable the channel under careful monitoring and process any backlog with human review if messages could have been duplicated.

## Validation

- Send volume for the disabled channel shows zero on the monitoring dashboard
- Provider dashboard confirms no new sends have been accepted for 5 minutes
- Queue consumer is confirmed paused (if applicable)
- Stakeholders have been notified of the impact

## Rollback

1. Before re-enabling the channel, confirm the root cause has been fixed and any affected queue messages have been reviewed and either discarded or approved for delivery.
2. Re-enable the channel feature flag and resume the queue consumer.
3. Monitor send rate closely for 15 minutes to confirm volume returns to normal without recurrence of the original issue.
4. Post in `#notifications-incidents`: "[Channel] notifications re-enabled. Monitoring for recurrence."
