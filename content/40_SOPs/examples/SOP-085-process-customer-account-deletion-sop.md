---
id: SOP-085
type: sop
title: Process Customer Account Deletion SOP
status: draft
owner: SRE Lead
created: '2025-12-07T08:13:23.673Z'
updated: '2025-02-06T01:06:53.788Z'
tags:
  - sop
  - customer-portal
summary: Process Customer Account Deletion SOP
related_process: PROCESS-050
related_systems:
  - SYSTEM-042
example: true
---

## Preconditions

- A verified account deletion request has been received through the portal self-service flow or customer success escalation
- The requesting user's identity and authorization to delete the account has been confirmed
- All outstanding invoices for the account are settled or a write-off has been approved
- Any active data export requests for the account have been fulfilled before deletion proceeds

## Materials/Access

- Access to the portal admin console with account management permissions
- Access to the account database (write access via approved privileged session)
- Deletion workflow script in the portal-admin tooling repository
- Account deletion request ticket ID

## Procedure

1. Open the account deletion request ticket and verify all preconditions are met; confirm the account ID matches the requesting customer.
2. In the portal admin console, navigate to the account and place it in "pending deletion" status to prevent new logins during the deletion process.
3. Run the account deletion preflight script to identify dependent data: active sessions, open support tickets, shared resources, and linked sub-accounts.
4. Manually review the preflight output; if the account has linked sub-accounts, confirm with the requester whether sub-accounts should also be deleted.
5. If all preconditions are clear, execute the account deletion workflow script with the account ID and deletion request ticket ID as parameters.
6. Monitor the script output; the script will anonymize PII, delete session tokens, remove account from SSO provider, and mark the account as deleted in the database.
7. Verify the deletion by attempting to log in with the account credentials; login should be rejected with "account not found."
8. Send the account deletion confirmation email to the customer's last verified email address.
9. Log the deletion action in the data subject request audit trail with account ID (hashed), deletion timestamp, and operator identity.

## Validation

- Login attempt with the deleted account credentials returns "account not found"
- Customer email and PII fields in the database are anonymized (not plaintext)
- SSO provider no longer lists the account in its directory
- Audit trail log entry is present with all required fields
- Deletion confirmation email delivery is confirmed in email logs

## Rollback

1. Account deletion is irreversible once the deletion workflow script completes; there is no automated rollback.
2. If the wrong account was deleted, escalate immediately to the Platform Lead and Privacy Officer.
3. Restore the account from the most recent database backup within the recovery window; document the incident and notify the affected customer.
4. Conduct a root cause review and update this SOP with any additional verification steps to prevent recurrence.
