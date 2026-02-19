---
id: SOP-070
type: sop
title: CI Runner Maintenance SOP
status: accepted
owner: SRE Lead
created: '2025-11-03T23:19:22.663Z'
updated: '2026-11-12T14:26:15.562Z'
tags:
  - sop
  - ci-cd-platform
summary: CI Runner Maintenance SOP
related_process: PROCESS-038
related_systems:
  - SYSTEM-031
example: true
---

## Preconditions

- Maintenance is either scheduled (weekly runner image refresh, OS patching) or required urgently (runner disk exhaustion, CVE patch, runner agent crash)
- You have identified which runners require maintenance (all runners in a pool, or specific runner IDs)
- The platform team has a quorum available to monitor pipeline throughput during the maintenance window
- No P1 or P2 incidents are currently in progress that depend on the runners being taken offline

## Materials/Access

- Admin access to the CI platform's runner management console (GitHub Actions runner groups, GitLab CI runner admin, or self-hosted runner orchestration)
- SSH or console access to the runner host instances if direct OS-level maintenance is required
- Access to the runner autoscaling configuration to temporarily increase pool size if reducing capacity
- Access to #platform-ops Slack channel for communication

## Procedure

1. Notify #platform-ops and #deployments: "CI runner maintenance starting. Reducing [pool-name] runner capacity by [N] runners for approximately [duration]. Expect increased queue wait times."
2. In the CI platform runner admin, mark the target runners as "offline" or "paused" to stop them accepting new jobs; existing in-progress jobs will continue to completion.
3. Wait for all in-progress jobs on the target runners to complete (monitor via the runner admin dashboard); do not forcibly terminate running jobs.
4. If performing an OS or runner agent update: connect to the runner host, apply the update package (`apt-get upgrade gitlab-runner` or equivalent), and verify the runner agent restarts successfully.
5. If performing a runner image refresh: update the runner AMI or container image reference in the autoscaling group or runner pool configuration, terminate the old instances, and allow autoscaling to launch new instances with the updated image.
6. Verify new runner instances register with the CI platform and appear in the runner admin as "online" and "idle."
7. Trigger a test pipeline run on a representative repository to confirm the refreshed runners execute jobs successfully from end to end.
8. Re-enable the maintained runners and notify #platform-ops: "CI runner maintenance complete. [Pool-name] runners back online. [N] runners healthy."

## Validation

- All maintained runners show "online" and "idle" status in the CI platform runner admin
- The test pipeline run completes successfully on the refreshed runners
- Pipeline queue wait times return to normal levels within 5 minutes of maintenance completion
- Runner agent version is confirmed updated (visible in runner admin metadata)

## Rollback

1. If refreshed runner instances fail to register with the CI platform, terminate the new instances and restore the previous AMI or container image in the autoscaling group configuration.
2. If the runner agent update causes job failures, downgrade the runner agent to the previous version and open a support ticket with the CI platform vendor.
3. If maintenance cannot be completed within the planned window, bring original runners back online and reschedule the maintenance.
