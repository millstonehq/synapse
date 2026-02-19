---
id: RUNBOOK-044
type: runbook
title: Build Runner Out of Disk Runbook
status: approved
owner: On-Call Engineer
created: '2025-08-17T13:07:46.381Z'
updated: '2025-02-28T13:53:05.766Z'
tags:
  - runbook
  - ci-cd-platform
summary: Build Runner Out of Disk Runbook
example: true
---

## Service

- **System**: [[SYSTEM-034|Build Runner Fleet]]
- **Owner team**: Platform Engineering
- **On-call rotation**: PagerDuty schedule "platform-oncall"
- **Slack channel**: #platform-incidents
- **Runtime**: Self-hosted runners / EC2 / Docker

## Alerts

- `BuildRunnerDiskUsageAbove90Pct` — Runner host disk utilization has exceeded 90% on the root or Docker volume; typically caused by accumulated image layers, build cache, or leftover artifacts
- `BuildRunnerDiskFull` — Runner host has reached 100% disk utilization; all new jobs on this runner will fail immediately with "no space left on device"
- `DockerLayerCacheEvictionFailed` — Docker daemon failed to evict old image layers due to disk pressure, causing build failures

## Diagnosis Steps

1. **Identify the affected runner** - From the alert, note the runner host ID or hostname; confirm it is the same runner producing "no space left on device" errors in recent job logs.
2. **Check overall disk usage** - SSH to the runner host and run `df -h` to identify which filesystem is full (root, `/var`, or a dedicated `/data` volume).
3. **Identify the top disk consumers** - Run `du -sh /var/lib/docker/* | sort -rh | head -20` to identify the largest Docker directories (images, containers, volumes, build cache).
4. **Check for leftover artifact files** - Check `/tmp` and the workspace directory (`/home/runner/work` or equivalent) for large files left by failed jobs that did not clean up.
5. **Check Docker system usage** - Run `docker system df` to get a summary of images, containers, volumes, and build cache size.

## Remediation Steps

1. **If Docker build cache is the primary consumer**: Run `docker builder prune --all --force` to clear all build cache; this is safe and will not remove images or containers.
2. **If dangling images are consuming space**: Run `docker image prune -f` to remove all untagged (dangling) images; this recovers space without affecting tagged production images.
3. **If stopped containers are accumulating**: Run `docker container prune -f` to remove all stopped containers; confirm no containers in "exited" state are needed for debugging.
4. **If workspace files remain from failed jobs**: Delete the workspace directory content manually (`rm -rf /home/runner/work/*`) after confirming no active jobs are running on this runner.
5. **If the disk is fully exhausted and cleanup is insufficient**: Take the runner offline in the CI admin, terminate the instance, and launch a replacement from the standard runner AMI; the autoscaler should provision a fresh instance automatically.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer begins disk cleanup steps |
| 10 min | If multiple runners are affected simultaneously, escalate to Platform Engineer |
| 20 min | If pipeline throughput drops below 50% due to runner degradation, declare platform incident |
| 45 min | If runner replacement is needed and autoscaler is not provisioning, escalate to Platform Lead |

## Dashboards

- [Runner Disk Usage](https://grafana.internal/d/runner-disk) - Per-runner disk utilization over time with alert thresholds
- [Docker System Metrics](https://grafana.internal/d/docker-metrics) - Image, container, volume, and cache size trends
- [CI Throughput](https://grafana.internal/d/ci-throughput) - Jobs per minute and queue depth to quantify impact
