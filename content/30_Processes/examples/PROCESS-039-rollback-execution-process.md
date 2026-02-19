---
id: PROCESS-039
type: process
title: Rollback Execution Process
status: approved
owner: Platform Lead
created: '2025-04-08T11:28:41.583Z'
updated: '2025-02-27T15:31:03.601Z'
tags:
  - process
  - ci-cd-platform
summary: Rollback Execution Process
related_standards:
  - STANDARD-037
  - STANDARD-040
related_sops:
  - SOP-066
  - SOP-064
related_systems:
  - SYSTEM-035
example: true
---

## Purpose

This process defines the steps for safely and consistently rolling back a production deployment when post-deployment monitoring reveals SLO degradation, critical errors, or unexpected behavior. Rollback is treated as a first-class operational action — not a failure — and should be executed quickly and without hesitation when health indicators warrant it. The process prioritizes service restoration over root cause investigation, which happens afterward in a separate postmortem workflow.

## Scope

- Rollbacks of application service deployments across all production environments
- Configuration rollbacks applied via the GitOps controller
- Rollbacks of database schema migrations (where reversible; irreversible migrations require manual intervention)
- Does not cover rollbacks of infrastructure-layer changes (Terraform), which follow the infrastructure change management process

## Roles and Responsibilities

- **Change Owner**: Makes the initial rollback decision, executes or delegates rollback steps, and communicates status throughout
- **On-Call Engineer**: Monitors health metrics during and after rollback, escalates if rollback does not resolve the issue
- **Incident Commander**: Takes ownership if the rollback triggers a full incident, coordinates parallel workstreams
- **Platform Engineer**: Available for escalation if the standard rollback mechanism fails or requires manual GitOps intervention

## Triggers

- Post-deployment monitoring shows error rate exceeding 1% or P95 latency exceeding defined SLO threshold for more than 3 consecutive minutes
- On-call engineer or automated alert indicates a regression directly attributable to a recent deployment
- Change Owner or on-call engineer makes a judgment call that the deployment has introduced unacceptable risk

## Inputs

- The commit SHA or image tag of the previous stable deployment (available in the deployment record)
- Access to the GitOps controller to update the target image tag
- Active incident or deployment record to track rollback status

## Outputs

- Service restored to previous stable version with confirmed healthy metrics
- Rollback event recorded in the deployment audit log with timestamp and reason
- Post-deploy review ticket created for root cause investigation within 48 hours
- Updated deployment record marked as rolled back

## Steps

1. Change Owner posts in #deployments: "INITIATING ROLLBACK of [service] from [new-sha] to [previous-sha]. Reason: [brief description]."
2. Change Owner retrieves the previous stable image tag from the deployment record or GitOps repository history
3. Change Owner updates the image tag in the GitOps manifest repository to the previous stable value and merges immediately (bypassing normal review for rollback commits)
4. GitOps controller detects the manifest change and initiates the rollout; Change Owner monitors pod replacement until all replicas are running the previous version
5. On-Call Engineer continuously monitors error rate, latency, and business metrics during the rollback rollout
6. Change Owner verifies metrics return to pre-deployment baseline within 5 minutes of rollback completion
7. Change Owner posts in #deployments: "ROLLBACK of [service] complete. Metrics recovered." and closes the deployment record as rolled back
8. Change Owner creates a post-deployment review ticket and assigns it for investigation within 48 hours

## Controls

- Rollback commits to the GitOps manifest repository must bypass the normal pull request review requirement; a comment in the commit message must indicate "ROLLBACK - skip review"
- Rollback must not be delayed more than 5 minutes after the decision to roll back is made; delays require escalation to the Incident Commander
- All rollback events are recorded with the change owner identity, timestamp, and reason for auditing purposes
