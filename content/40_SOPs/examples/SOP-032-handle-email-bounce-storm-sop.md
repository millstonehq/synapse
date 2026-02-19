---
id: SOP-032
type: sop
title: Handle Email Bounce Storm SOP
status: review
owner: DevOps Lead
created: '2025-05-30T19:12:46.868Z'
updated: '2025-05-23T19:27:33.214Z'
tags:
  - sop
  - notification-service
summary: Handle Email Bounce Storm SOP
related_process: PROCESS-023
related_systems:
  - SYSTEM-018
example: true
---

## Preconditions

- The bounce rate alert has fired (`email_bounce_rate_high`) or the on-call engineer has been notified of elevated bounces
- You have access to the email provider's Activity Feed and bounce log export
- You have write access to the Notification Service suppression list management API
- The affected sending domain, IP, and campaign/notification type have been identified

## Materials/Access

- SendGrid (or active provider) Activity Feed with bounce event filter
- Notification Service suppression list management API credentials
- Access to the `notifications` and `delivery_attempts` database tables
- Slack access to `#notifications-incidents`
- Email provider support contact details for urgent IP reputation issues

## Procedure

1. Post in `#notifications-incidents`: "Investigating elevated email bounce rate. Provider: [name]. Bounce rate: [current %]. Starting investigation."
2. Access the email provider Activity Feed and export bounce events for the past 60 minutes, filtering by bounce type (hard vs. soft).
3. Determine the bounce composition: if more than 80% are hard bounces, this is a list quality issue; if predominantly soft bounces, this is likely a provider or receiving server issue.
4. For hard bounces: immediately add all hard-bounced addresses to the suppression list using the bulk suppression API to stop retries and protect sender reputation.
5. Identify the notification type or campaign that generated the bounces to understand the data source of bad addresses.
6. If the bounce rate exceeds 5% and continues to climb, pause the sending campaign or notification type via the feature flag to halt further sends while investigating.
7. For soft bounces: check the provider status page for receiving server issues; if the issue is transient, allow normal retry behavior.
8. Once root cause is confirmed, create a ticket for the data source team to clean the address list before resending.
9. Monitor bounce rate on the provider dashboard until it returns below 2% before declaring resolution.

## Validation

- Bounce rate has returned below 2% on the provider dashboard
- All hard-bounced addresses have been added to the suppression list
- The data source producing bad addresses has been identified and a remediation ticket created
- No IP reputation warnings or blacklisting notices have been received from the provider

## Rollback

1. If the bulk suppression update was applied incorrectly (e.g., valid addresses suppressed), export the erroneous suppression records and remove them using the suppression list deletion API.
2. If a campaign was paused as a precaution and the data quality issue was isolated, re-enable the campaign only after the affected address segment has been removed.
3. If sender reputation has been affected (IP warming reset or blacklisting), engage the email provider support team and follow IP warmup procedures before resuming full volume.
