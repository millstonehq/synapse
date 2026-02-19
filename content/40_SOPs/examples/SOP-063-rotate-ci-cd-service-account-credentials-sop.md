---
id: SOP-063
type: sop
title: Rotate CI/CD Service Account Credentials SOP
status: approved
owner: DevOps Lead
created: '2024-04-08T14:04:35.149Z'
updated: '2026-07-05T08:04:23.270Z'
tags:
  - sop
  - ci-cd-platform
summary: Rotate CI/CD Service Account Credentials SOP
related_process: PROCESS-040
related_systems:
  - SYSTEM-033
example: true
---

## Preconditions

- You have identified the specific service account credential requiring rotation (scheduled rotation, suspected compromise, or credential expiry)
- You have admin access to both the secrets manager and the CI platform's secret configuration
- No active deployments are in progress for services that consume the credential being rotated
- A maintenance window or low-traffic period has been identified for rotation if the credential is critical-path

## Materials/Access

- Admin access to the organization's secrets manager (HashiCorp Vault, AWS Secrets Manager, or equivalent)
- Admin access to the CI platform secret store to update the secret reference
- Access to the service accounts admin console for the target system (container registry, cloud provider, etc.)
- The rotation runbook for the specific credential type if available
- Access to #platform-ops Slack channel for team notification

## Procedure

1. Notify the #platform-ops channel: "Beginning rotation of [credential-name] for [service-account]. Duration: ~[estimated minutes]. This may cause brief pipeline failures."
2. In the target system's admin console, generate a new credential (API key, access token, or certificate) for the service account; do not revoke the old credential yet.
3. In the secrets manager, create a new version of the secret with the new credential value; preserve the old version and record both version identifiers.
4. Update the CI platform's secret reference to point to the new secret version; in pipeline configuration, this may require updating the secret name or version pin.
5. Trigger a test pipeline run on a non-production branch that exercises the rotated credential (e.g., a registry push job); verify the job completes successfully.
6. If the test run succeeds, revoke the old credential in the target system's admin console and delete the old secret version from the secrets manager after a 1-hour retention buffer.
7. Update the secrets inventory record for this credential with the new rotation date, next scheduled rotation date, and your name as the rotating operator.
8. Notify #platform-ops: "Rotation of [credential-name] complete. Old credential revoked. Next rotation due: [date]."

## Validation

- A CI pipeline job that uses the rotated credential runs to completion without authentication errors
- The old credential is confirmed revoked in the target system's admin console
- The secrets inventory shows the updated rotation date and the new secret version ID
- No failed pipeline runs are attributed to the credential rotation after the test run passes

## Rollback

1. If the new credential fails validation, immediately restore the old secret version in the secrets manager and revert the CI platform secret reference to the previous value.
2. Verify pipelines resume normal operation using the restored old credential.
3. Investigate the failure before reattempting rotation; common issues include incorrect permission scopes on the new credential or wrong secret path in the CI configuration.
