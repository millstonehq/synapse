---
id: SOP-082
type: sop
title: Handle Customer Data Export Request SOP
status: approved
owner: SRE Lead
created: '2025-02-08T19:14:54.778Z'
updated: '2026-11-18T02:55:04.868Z'
tags:
  - sop
  - customer-portal
summary: Handle Customer Data Export Request SOP
related_process: PROCESS-052
related_systems:
  - SYSTEM-042
example: true
---

## Preconditions

- A verified customer data export request has been received via the portal or customer success team
- The requesting customer's identity has been verified (logged-in session or confirmed via support ticket workflow)
- The request is within the 30-day statutory response window
- No active data retention legal hold affects the account

## Materials/Access

- Access to the portal admin console with data export permissions
- Access to the customer account database (read-only role via bastion)
- Secure file transfer channel for delivering exports (encrypted S3 pre-signed URL)
- Data export request ticket ID

## Procedure

1. Open the customer's account in the portal admin console and confirm account status is active or recently closed (within retention period).
2. Navigate to the Data Management section and initiate a full account data export; select all data categories (profile, activity, tickets, billing history).
3. Note the export job ID and monitor the export job status; typical completion time is 5-10 minutes for standard accounts.
4. Once the export job completes, download the ZIP archive and verify it is non-empty and not corrupted (check file count and spot-check contents).
5. Scan the export archive with the malware scanner before delivery; do not deliver if any files are flagged.
6. Generate an S3 pre-signed URL with 7-day expiry for the export archive; store the URL in the export request ticket.
7. Send the download link to the customer's verified email address using the approved data export notification template.
8. Log the export action in the data subject request audit trail: request ID, account ID, data categories exported, delivery timestamp.
9. Close the export request ticket with a note confirming delivery and the pre-signed URL expiry date.

## Validation

- Export archive is downloadable via the pre-signed URL and the file is not corrupted
- Archive contains data from all requested categories (profile, activity, support, billing)
- Audit trail log entry is present with all required fields
- Customer has received the delivery email (check email delivery logs)
- Request ticket is closed within the 30-day statutory window

## Rollback

1. If the export archive is found to contain incorrect or out-of-scope data after delivery, revoke the pre-signed URL immediately via the S3 console.
2. Notify the customer that the export was recalled and a corrected export will be provided within 5 business days.
3. Investigate the root cause of the incorrect export and open a bug ticket before reprocessing.
4. Reprocess the export following this SOP from step 2; have a second reviewer verify the archive contents before delivery.
