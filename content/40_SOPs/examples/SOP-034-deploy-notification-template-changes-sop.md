---
id: SOP-034
type: sop
title: Deploy Notification Template Changes SOP
status: approved
owner: SRE Lead
created: '2025-06-09T23:53:28.729Z'
updated: '2026-05-14T21:07:25.212Z'
tags:
  - sop
  - notification-service
summary: Deploy Notification Template Changes SOP
related_process: PROCESS-019
related_systems:
  - SYSTEM-018
example: true
---

## Preconditions

- The template change has been approved through the Notification Template Approval Process (PROCESS-019)
- The approved template version is tagged and available in the template registry
- A deployment ticket has been created and linked to the approved template version
- No other template deployments are currently in progress for the same notification event

## Materials/Access

- Access to the template registry with write permissions to update production template bindings
- Access to the Notification Service admin API to verify active template versions
- Access to the monitoring dashboard to confirm delivery metrics post-deploy
- Slack access to `#notifications-releases`

## Procedure

1. Post in `#notifications-releases`: "Deploying template change for [notification event]. Template version: [version]. Ticket: [ID]."
2. In the template registry, verify the approved version is present and its checksum matches the approved artifact.
3. Update the notification event binding to reference the new template version (do not delete the previous version).
4. Trigger a test notification send using the internal test harness to confirm the new template renders correctly and all dynamic variables resolve.
5. Review the rendered test output for layout accuracy, variable substitution, and presence of required elements (unsubscribe link, correct branding).
6. If the template is for a high-volume event, verify the change in a canary send to 1% of recipients and monitor delivery and engagement metrics for 10 minutes.
7. Promote the template binding to 100% of recipients if canary validation passes.
8. Monitor delivery rate, bounce rate, and unsubscribe rate on the dashboard for 15 minutes post-deploy.
9. Update the deployment ticket with the deployment timestamp, test results, and post-deploy metrics screenshot.

## Validation

- Test notification renders correctly with all dynamic variables populated
- Delivery rate for the affected notification event is stable post-deploy
- No increase in unsubscribe or complaint rate following the template change
- The deployment ticket is closed with evidence

## Rollback

1. If the new template causes rendering issues or elevated opt-outs, revert the notification event binding to the previous template version in the template registry.
2. Trigger a test send with the reverted template to confirm correct rendering.
3. Post in `#notifications-releases`: "Template change rolled back for [notification event]. Reason: [brief description]."
4. Update the deployment ticket with rollback details and create a review ticket for the template issue.
