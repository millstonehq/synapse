---
id: SOP-033
type: sop
title: Update Email DNS Records SOP
status: approved
owner: DevOps Lead
created: '2025-06-12T16:28:19.186Z'
updated: '2026-08-20T03:27:37.277Z'
tags:
  - sop
  - notification-service
summary: Update Email DNS Records SOP
related_process: PROCESS-024
related_systems:
  - SYSTEM-018
example: true
---

## Preconditions

- A DNS record change has been approved via the change management process (DKIM key rotation, SPF update, DMARC policy change, or MX record update)
- You have write access to the DNS management console for the sending domain
- You have access to an MX toolbox or equivalent DNS verification tool
- The on-call engineer has been notified of the planned change
- A rollback plan (restoring previous DNS values) is documented

## Materials/Access

- DNS management console (Route 53 or equivalent) with write access to the sending domain zone
- Current DNS record values (exported before making changes)
- MXToolbox or Google Admin Toolbox for post-change validation
- Email provider DNS verification tool (SendGrid's Domain Authentication checker)
- Slack access to `#notifications-ops` for change communication

## Procedure

1. Export current DNS record values for the target record types (SPF TXT, DKIM TXT, DMARC TXT) and store them in the change ticket as the rollback baseline.
2. Post in `#notifications-ops`: "Starting DNS update for [domain]. Change: [brief description]. Change ticket: [ID]."
3. Apply the DNS record change in the DNS management console, double-checking the record type, name, value, and TTL against the approved change ticket.
4. Wait for DNS propagation based on the record's TTL (minimum 5 minutes for short-TTL records, up to 48 hours for propagation globally).
5. Validate the updated record using MXToolbox: confirm the new value is resolving from at least 3 geographically distributed DNS resolvers.
6. Validate email authentication using the email provider's domain verification tool to confirm DKIM signing and SPF alignment are passing.
7. Send a test email from the configured sending domain and verify the email headers show `dkim=pass`, `spf=pass`, and `dmarc=pass`.
8. Post in `#notifications-ops`: "DNS update for [domain] complete. Verification: DKIM pass, SPF pass, DMARC pass."
9. Update the change ticket with verification evidence (screenshot of authentication results) and mark as complete.

## Validation

- MXToolbox confirms the new record value is resolving consistently
- Email authentication headers on a test send show `dkim=pass`, `spf=pass`, `dmarc=pass`
- Email provider domain authentication dashboard shows the domain as verified
- No increase in bounce rate or delivery failures is detected in the 30 minutes following the change

## Rollback

1. If email authentication failures are detected after the DNS change, immediately restore the previous record values from the backup recorded in step 1.
2. Verify the rollback has propagated and authentication headers return to passing on a test send.
3. Post in `#notifications-ops`: "DNS change rolled back for [domain]. Reason: [brief description]."
4. Update the change ticket with rollback details and create a post-change review ticket to investigate the cause of the failure.
