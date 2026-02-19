---
id: RUNBOOK-047
type: runbook
title: CI Runner Pool Exhausted Runbook
status: approved
owner: On-Call Engineer
created: '2025-07-05T11:28:41.619Z'
updated: '2026-12-29T15:17:56.968Z'
tags:
  - runbook
  - ci-cd-platform
summary: CI Runner Pool Exhausted Runbook
example: true
---

## Service

- **System**: [[SYSTEM-031|CI Platform]]
- **Owner team**: Platform Engineering
- **On-call rotation**: PagerDuty schedule "platform-oncall"
- **Slack channel**: #platform-incidents
- **Runtime**: GitHub Actions / Self-hosted runner autoscaler

## Alerts

- `CIRunnerPoolUtilizationAbove95Pct` — Active runners as a percentage of total pool capacity exceeds 95%; new jobs are queuing with no available runners
- `CIJobQueueWaitTimeP95Above10min` — The 95th percentile wait time for a queued CI job to start running exceeds 10 minutes
- `CIRunnerAutoscalerFailedToProvision` — The runner autoscaler has attempted to launch new runner instances but failed; pool is not growing to meet demand

## Diagnosis Steps

1. **Check current pool utilization** - In the CI runner admin console, view the total number of registered runners versus the number currently executing jobs; confirm whether all runners are busy or some are offline/unhealthy.
2. **Check autoscaler status** - If using an autoscaler (e.g., GitLab Runner on Kubernetes, GitHub Actions autoscaler), check its logs for provisioning errors; common causes include cloud provider quota limits and instance type unavailability.
3. **Identify the source of increased demand** - Check the job queue to identify which repositories or teams are submitting unusually high volumes of jobs; a runaway CI configuration or merge queue flush can exhaust the pool.
4. **Check for stuck jobs consuming runners** - Identify jobs that have been running longer than expected (>60 minutes) — these may be hung jobs holding runner capacity; check using `argocd app list` or the CI platform's running jobs view.
5. **Check cloud provider capacity** - If using EC2, GCE, or Azure VMs as runners, check the cloud console for service disruptions or quota limits that may be preventing autoscaler from launching new instances.

## Remediation Steps

1. **If autoscaler cannot provision due to cloud quota**: Request an emergency quota increase via the cloud provider console and notify the engineering manager; consider temporarily increasing the runner instance size to handle more concurrent jobs per instance.
2. **If hung jobs are consuming capacity**: Cancel all jobs that have been running more than 90 minutes without producing log output; investigate the job configuration for missing timeouts.
3. **If a specific repository is flooding the queue**: Temporarily limit the concurrency for that repository's pipelines in the CI platform configuration; notify the owning team.
4. **If autoscaler configuration is broken**: Manually launch runner instances from the approved runner AMI and register them with the CI platform; document the instances for later deregistration.
5. **If demand is legitimately high (release day, merge queue)**: Temporarily increase the autoscaler maximum pool size and communicate expected queue wait times to engineering teams in #deployments.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer assesses pool utilization and demand source |
| 10 min | If autoscaler is broken, escalate to Platform Engineer |
| 20 min | Notify #platform-incidents and all engineering teams of extended CI queue times |
| 45 min | If pool exhaustion persists, escalate to Platform Lead for capacity planning decision |

## Dashboards

- [Runner Pool Utilization](https://grafana.internal/d/runner-pool) - Active/idle/offline runner counts and capacity trends
- [CI Queue Depth](https://grafana.internal/d/ci-queue) - Pending job queue depth and wait time P95
- [Autoscaler Events](https://grafana.internal/d/autoscaler) - Provisioning attempts, success rate, and failure reasons
