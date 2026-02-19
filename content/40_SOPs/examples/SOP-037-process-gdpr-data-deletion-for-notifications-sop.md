---
id: SOP-037
type: sop
title: Process GDPR Data Deletion for Notifications SOP
status: review
owner: Release Manager
created: '2025-01-07T00:24:34.698Z'
updated: '2026-02-08T00:30:24.556Z'
tags:
  - sop
  - notification-service
summary: Process GDPR Data Deletion for Notifications SOP
related_process: PROCESS-022
related_systems:
  - SYSTEM-020
example: true
---

## Preconditions

- A verified GDPR Right to Erasure request has been received and validated by the privacy/legal team
- The user identifier (user_id, email address, phone number) has been confirmed and documented in the deletion request ticket
- You have write access to the Notification Service database with the ability to execute data deletion scripts
- A backup of the affected records has been taken before deletion (per legal hold requirements)

## Materials/Access

- Database write access to the Notification Service `notifications`, `delivery_attempts`, `device_tokens`, and `suppression_list` tables
- Secrets manager access to retrieve database credentials for the deletion script
- The verified deletion request ticket with user identifier and scope
- Slack access to `#privacy-ops` for communication with the privacy team

## Procedure

1. Confirm the deletion request ticket has been verified and approved by the legal/privacy team before proceeding.
2. Record the user identifiers in scope (user_id, email addresses, phone numbers, device tokens) from the deletion request ticket.
3. Take a point-in-time export of all notification records for the user and store them in the legal hold archive bucket (required for audit purposes).
4. Execute the deletion script for the `notifications` table: delete all records where `recipient_id` matches the user_id.
5. Execute the deletion script for the `delivery_attempts` table: delete all attempts linked to the deleted notification IDs.
6. Delete all device tokens associated with the user from the `device_tokens` table.
7. Remove the user's email address and phone number from the `suppression_list` table (the user's right to erasure overrides suppression retention unless a legal basis exists to retain it).
8. Notify the email provider (SendGrid) to remove the user's address from their global suppression and bounce lists via the provider API.
9. Document the deletion completion in the privacy request ticket with a timestamp and confirmation that all identified records were deleted.

## Validation

- A query against all affected tables using the user identifier returns zero records
- The email provider API confirms the address has been removed from the provider's suppression and bounce lists
- The legal hold archive contains the pre-deletion export
- The privacy request ticket is updated with deletion confirmation

## Rollback

1. GDPR deletions are irreversible by design; no rollback of deleted records is permitted.
2. If a deletion was executed on the wrong user ID, immediately escalate to the Privacy Officer and legal team.
3. Restore only if an erroneous deletion can be shown not to involve the requesting user's data, using the legal hold archive as the source.
