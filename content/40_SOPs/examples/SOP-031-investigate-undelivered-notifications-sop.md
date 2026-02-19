---
id: SOP-031
type: sop
title: Investigate Undelivered Notifications SOP
status: approved
owner: SRE Lead
created: '2024-03-11T22:38:55.122Z'
updated: '2025-08-30T07:04:12.873Z'
tags:
  - sop
  - notification-service
summary: Investigate Undelivered Notifications SOP
related_process: PROCESS-021
related_systems:
  - SYSTEM-018
example: true
---

## Preconditions

- You have access to the Notification Service logs in the logging platform (Kibana or equivalent)
- You have access to the provider dashboards for the relevant channel (SendGrid, Twilio, FCM console)
- The notification IDs or user IDs in question have been identified by the reporter
- You have read access to the notification database to query delivery status records
- No active incident is in progress that would explain the undelivered messages systemically

## Materials/Access

- Access to the Notification Service logging dashboard filtered by `service:notification-service`
- Provider dashboard credentials (SendGrid Activity Feed, Twilio Debugger, FCM console)
- Database read access to the `notifications` and `delivery_attempts` tables
- Slack access to `#notifications-incidents` for communication
- The affected notification IDs, user IDs, or time range from the reporter

## Procedure

1. Query the `notifications` table for the affected notification IDs and note the current `status` field values and `last_attempt_at` timestamps.
2. For notifications with status `failed` or `deferred`, query `delivery_attempts` to retrieve all attempt records, error codes, and provider responses.
3. Check the Notification Service error logs in Kibana for the affected time window, filtering by `notification_id` or `recipient_id` to find provider error responses.
4. If error codes indicate a provider-side rejection (e.g., `550 5.1.1` for email invalid address, FCM `InvalidRegistration`), determine if this is a data quality issue (bad address/token) or a provider outage.
5. Check the provider's status page and Activity Feed/Debugger to confirm whether the rejections are isolated or part of a broader provider incident.
6. If the issue is data quality (bad addresses or tokens), identify the source of the bad data and create a ticket for data cleanup.
7. If the issue is a provider-side outage or configuration error, escalate to the on-call engineer and follow the relevant runbook.
8. Document findings in the incident or support ticket, including notification IDs, error codes, root cause assessment, and recommended remediation.

## Validation

- The `delivery_attempts` records for the affected notifications show a clear error code and provider response
- The root cause is identified as one of: data quality issue, provider outage, configuration error, or rate limit breach
- If notifications are deliverable (valid recipient, no suppression), a retry has been queued or triggered
- The reporter has been updated with the investigation findings

## Rollback

1. If an incorrect suppression list entry was identified as the cause, remove the suppression record and trigger a manual retry of the affected notification IDs.
2. If a misconfigured retry policy caused notifications to expire prematurely, update the retry configuration and re-enqueue affected notifications from the dead-letter queue.
3. If a provider credential error caused failures, rotate or correct the credential and verify delivery resumes before closing the investigation.
