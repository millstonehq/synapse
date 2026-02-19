---
id: PROCESS-023
type: process
title: Unsubscribe Request Handling Process
status: deprecated
owner: Director of Engineering
created: '2025-07-25T03:01:25.849Z'
updated: '2026-02-08T04:14:01.337Z'
tags:
  - process
  - notification-service
summary: Unsubscribe Request Handling Process
related_standards:
  - STANDARD-023
  - STANDARD-019
related_sops:
  - SOP-034
  - SOP-033
related_systems:
  - SYSTEM-018
example: true
---

## Purpose

This process ensures that user unsubscribe requests are captured, validated, and propagated to the suppression list within the timeframes required by CAN-SPAM and GDPR. Failure to honor opt-out requests in a timely manner creates regulatory exposure and damages user trust.

## Scope

- Unsubscribe requests received via email list-unsubscribe headers (RFC 8058)
- Unsubscribe link clicks embedded in email, SMS, and in-app messages
- Direct API calls to the preference management endpoint
- Suppression list updates triggered by provider bounce and complaint webhooks

## Roles and Responsibilities

- **Notification Service**: Automatically processes machine-readable unsubscribe events and updates the suppression list
- **Customer Support Engineer**: Handles manual unsubscribe requests received through support tickets
- **Compliance Officer**: Reviews suppression list audit logs quarterly and validates that opt-outs are being honored
- **Platform Lead**: Escalates failures in opt-out processing to engineering and compliance

## Triggers

- User clicks an unsubscribe link in any notification channel
- A List-Unsubscribe POST request is received from a mailbox provider
- A hard bounce or spam complaint webhook is received from the email provider
- A user submits a data deletion request under GDPR

## Inputs

- Unsubscribe event from channel (link click, List-Unsubscribe POST, provider webhook)
- User identifier (email address, phone number, device token, or user_id)
- Channel scope of the unsubscribe (all channels or specific channel)

## Outputs

- Updated suppression list record with channel scope and timestamp
- Suppression confirmation sent to user (for email unsubscribes)
- Audit log entry for compliance review

## Steps

1. Unsubscribe event is received by the Notification Service preference endpoint
2. Service validates the event signature (for provider webhooks) or token (for link clicks)
3. User identifier is resolved to a canonical user_id or, if unavailable, stored as a raw address in the suppression list
4. Suppression record is written with the channel scope, request source, and timestamp
5. For email unsubscribes, a confirmation message is sent to the user within 24 hours
6. Suppression record is replicated to all channel dispatchers within 5 minutes
7. Audit log entry is written and retained for 3 years per compliance requirement

## Controls

- Suppression records must propagate to all channel dispatchers within 10 minutes
- No test or re-engagement send may target a suppressed address without explicit re-consent
- Quarterly audit must verify that the suppression list is being checked before every send
- GDPR deletion requests must remove both the suppression record and all notification history for the user
