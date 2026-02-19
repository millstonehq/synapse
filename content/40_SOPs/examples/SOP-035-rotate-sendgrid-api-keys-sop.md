---
id: SOP-035
type: sop
title: Rotate SendGrid API Keys SOP
status: approved
owner: DevOps Lead
created: '2024-02-05T03:13:04.130Z'
updated: '2025-05-26T16:23:57.490Z'
tags:
  - sop
  - notification-service
summary: Rotate SendGrid API Keys SOP
related_process: PROCESS-064
related_systems:
  - SYSTEM-020
example: true
---

## Preconditions

- You have admin access to the SendGrid account to create and revoke API keys
- You have write access to the secrets manager where the current API key is stored
- A change ticket has been created for the key rotation (routine rotation or incident-driven)
- The on-call engineer is aware of the rotation, as it involves a brief configuration update to the Notification Service

## Materials/Access

- SendGrid admin console with API Key management access
- Secrets manager (AWS Secrets Manager or HashiCorp Vault) with write access to the `notification-service/sendgrid-api-key` path
- Notification Service deployment access to trigger a config reload or rolling restart
- Slack access to `#notifications-ops`

## Procedure

1. Log in to the SendGrid admin console and navigate to Settings > API Keys.
2. Create a new API key with the same permission scopes as the existing key (Mail Send, Suppressions Read/Write, Bounces Read/Write). Name it with the rotation date, e.g., `notification-service-2026-02`.
3. Copy the new API key value immediately; it will not be displayed again after this step.
4. Store the new API key in the secrets manager at the path `notification-service/sendgrid-api-key`, replacing the existing value.
5. Trigger a rolling restart of the Notification Service pods to pick up the new secret value: `kubectl rollout restart deployment/notification-service -n notifications`.
6. Verify the Notification Service starts successfully and is sending email by checking the monitoring dashboard for a successful send within 5 minutes (or trigger a test notification).
7. Confirm in the SendGrid Activity Feed that emails are being accepted with the new key (no `401 Unauthorized` errors).
8. Revoke the old API key in the SendGrid admin console once the new key is confirmed working.
9. Update the change ticket with rotation timestamp and confirmation of old key revocation.

## Validation

- No `401 Unauthorized` errors appear in Notification Service logs after the restart
- Email delivery rate remains stable post-rotation
- The old API key has been revoked in the SendGrid admin console
- The change ticket is updated with evidence of successful rotation

## Rollback

1. If the Notification Service fails to authenticate after the restart, the old key may have been revoked prematurely — immediately create a new API key in SendGrid.
2. Update the secrets manager with the new key value and trigger another rolling restart.
3. If the SendGrid account shows authentication issues not related to the key, contact SendGrid support with the account credentials and incident details.
