---
id: RUNBOOK-043
type: runbook
title: CI Pipeline Stuck Job Runbook
status: approved
owner: On-Call Engineer
created: '2024-01-20T09:13:33.598Z'
updated: '2026-07-15T15:50:37.464Z'
tags:
  - runbook
  - ci-cd-platform
summary: CI Pipeline Stuck Job Runbook
example: true
---

## Service

- **System**: [[SYSTEM-031|CI Platform]]
- **Owner team**: Platform Engineering
- **On-call rotation**: PagerDuty schedule "platform-oncall"
- **Slack channel**: #platform-incidents
- **Runtime**: GitHub Actions / Self-hosted runners / Kubernetes

## Alerts

- `CIPipelineJobStuckFor30min` — A CI job has been in "in_progress" state for more than 30 minutes without producing log output; fires when no heartbeat is received for 30+ minutes
- `CIRunnerHeartbeatMissing` — A runner agent has stopped sending heartbeats to the CI server, indicating a crashed or hung runner process
- `CIPipelineQueueDepthHigh` — Job queue depth exceeds 50 pending jobs, suggesting runner pool exhaustion or job processing is blocked

## Diagnosis Steps

1. **Check the stuck job details** - Navigate to the failing pipeline in the CI UI; note the job name, runner ID, and the last log line produced before output stopped.
2. **Check runner agent health** - In the runner admin console, find the runner processing the stuck job; check whether it shows "online," "offline," or "stale" status and when the last heartbeat was received.
3. **Inspect runner host resources** - SSH to the runner host (or view cloud console metrics) and check CPU, memory, and disk usage; a stuck job is often caused by OOM or full disk, causing the process to hang.
4. **Check for network partition** - Verify the runner can reach the CI server and the container registry; run `curl -I https://registry.internal` from the runner host to confirm network connectivity.
5. **Review recent runner logs** - On the runner host, inspect the runner agent logs (`journalctl -u gitlab-runner -n 200` or equivalent) for error messages indicating why the job hung.
6. **Check for hung child processes** - On the runner host, run `ps aux | grep <job-id>` to identify any orphaned build processes that may be blocking the job from completing.

## Remediation Steps

1. **If the runner is out of disk**: Follow the Build Runner Out of Disk Runbook to free space, then cancel and re-trigger the stuck job.
2. **If the runner process is hung**: Force-kill the runner agent process on the host (`sudo kill -9 <pid>`), verify the runner agent restarts automatically, and re-trigger the stuck job.
3. **If the runner shows offline/stale**: Remove the stale runner registration from the CI admin console, terminate and replace the runner instance via the autoscaler, and re-trigger the job.
4. **If the job is stuck waiting for a locked resource** (e.g., concurrent job mutex, file lock): identify the locking job, determine if it is also stuck or running legitimately, and cancel the stuck job to release the lock.
5. **If no runner-side cause is found**: Cancel the stuck job from the CI UI and re-trigger it; document the occurrence in the flaky job tracker and monitor for recurrence.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer receives alert; begins diagnosis steps |
| 15 min | If root cause not identified, escalate to Platform Engineer on-call via PagerDuty |
| 30 min | If runner pool is degraded impacting multiple teams, declare a platform incident and notify #platform-incidents |
| 60 min | If platform is still degraded, escalate to Platform Lead for vendor support engagement |

## Dashboards

- [CI Platform Health](https://grafana.internal/d/ci-platform-health) - Runner pool utilization, job queue depth, and job success rates
- [Runner Metrics](https://grafana.internal/d/runner-metrics) - Per-runner CPU, memory, disk, and job throughput
- [CI Job Duration P95](https://grafana.internal/d/ci-job-duration) - Job duration trends by stage and repository
