---
id: POSTMORTEM-032
type: postmortem
title: CI Runner Fleet Outage 2024-12-15
status: approved
owner: Incident Commander
created: '2024-01-16T04:10:52.924Z'
updated: '2026-12-08T22:21:22.265Z'
tags:
  - postmortem
  - ci-cd-platform
summary: CI Runner Fleet Outage 2024-12-15
incident_number: INC-643
severity: SEV-4
incident_date: '2024-04-16'
detection_time: '2025-09-04T23:14:09.175Z'
resolution_time: '2026-08-10T04:54:48.820Z'
total_duration: ~15 minutes
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-070
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On December 15, 2024, all 60 CI runner nodes in the production fleet became unresponsive within a 4-minute window, causing every in-progress build job to fail and blocking new job dispatch. The fleet manager's RabbitMQ connection was severed by a network policy update that was applied without the expected exclusion for the CI namespace. The outage lasted 15 minutes until the network policy was reverted and runners re-registered.

The SEV-4 classification reflects the limited blast radius: no deployments were blocked (the fleet recovered before the deployment queue grew) and no end-user services were affected.

## Timeline

- **09:41** - Network team applies a network policy update to restrict egress in the `default` namespace
- **09:42** - CI runner pods in the `ci-runners` namespace begin losing RabbitMQ connectivity; jobs start timing out
- **09:43** - Build Orchestration Service reports 60 jobs as stale (heartbeat timeout)
- **09:45** - `ci_runner_fleet_all_down` alert fires. On-call engineer acknowledges.
- **09:47** - On-call identifies no recent CI/CD deploys. Checks runner pod logs; sees `AMQP connection refused` errors.
- **09:50** - Network policy change identified as root cause via Kubernetes audit log.
- **09:51** - Network policy reverted by network team.
- **09:54** - Runners begin re-registering with the fleet manager. Queue backlog starts clearing.
- **09:56** - All 60 runners back online. Build job success rate returns to normal.

## Impact

- **Duration**: 15 minutes (09:41 - 09:56 UTC)
- **Builds affected**: 60 in-flight builds aborted; all were re-queued automatically and completed within 25 minutes of recovery
- **Deployments blocked**: Zero (deployment queue was empty at time of outage)
- **Developer impact**: ~40 developers experienced build failures; all resolved on automatic retry
- **SLA impact**: Runner fleet availability dropped to 99.97% for December

## Root Cause Analysis

1. **Network policy namespace mismatch**: The network policy update was intended to restrict egress in `default` namespace only. However, the policy was applied as a cluster-wide NetworkPolicy with no namespace selector, affecting all namespaces including `ci-runners` where runner pods need egress to the RabbitMQ broker in `platform` namespace.

2. **No CI/CD exclusion in network policy review process**: The network policy review checklist did not include a step to verify CI/CD namespace connectivity. The change was reviewed and approved by two engineers without either catching the scope issue.

## Resolution

1. On-call engineer identified the RabbitMQ connection error in runner logs
2. Correlated with recent Kubernetes audit log showing network policy change
3. Network team reverted the network policy to the previous version
4. Verified runner re-registration and job queue clearing

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add CI/CD namespace connectivity test to network policy review checklist | Network team | P1 | 2024-12-20 | Completed |
| Add automated network policy validation CI job for platform namespace changes | Platform team | P1 | 2025-01-10 | Completed |
| Configure RabbitMQ connection retry with exponential backoff in runner agent | CI/CD team | P2 | 2025-01-15 | Completed |
| Add `ci_runner_fleet_all_down` runbook with network connectivity diagnosis steps | CI/CD team | P2 | 2025-01-15 | Completed |

## Lessons Learned

- **What went well**: Alert fired within 2 minutes. Root cause identified quickly via audit log. Recovery was fast after the revert.
- **What went poorly**: The network policy review process had a gap: no check for CI/CD namespace impact. A standard checklist item would have caught this.
- **What was lucky**: No deployments were in-flight during the outage. Had any critical deploys been queued, this would have been a SEV-2.
- **Process improvement**: All network policy changes must now pass an automated connectivity test before merging.
