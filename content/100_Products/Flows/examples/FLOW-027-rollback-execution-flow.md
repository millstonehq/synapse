---
id: FLOW-027
type: flow
title: Rollback Execution Flow
status: proposed
owner: QA Engineer
created: '2025-10-10T10:44:38.579Z'
updated: '2025-06-18T20:50:18.613Z'
tags:
  - flow
  - ci-cd-platform
summary: Rollback Execution Flow
feature_area: CI/CD Platform
related_prds:
  - PRD-034
example: true
---

## Steps

### Step 1: Rollback Decision

A rollback can be initiated in two ways: automatically, by the post-deployment monitoring service when an error rate threshold breach is detected; or manually, by an on-call or deploying engineer clicking "Rollback" in the Release Dashboard or running `plat rollback --service {name}` from the CLI. In the automated path, the monitoring service creates a RollbackTrigger record and sends a Slack notification to the on-call channel with a 60-second veto window. In the manual path, the engineer selects the target version (defaulting to the previous deployment) and confirms the rollback action.

### Step 2: Rollback Submission

If no veto is received within the veto window (automated path) or the engineer confirms (manual path), the Deployment Controller receives a rollback request. The Controller retrieves the previous deployment's image digest from the deployment history and updates the Kubernetes manifest repository's production overlay to point to that image. The update is committed and pushed as a direct commit to the manifest repository; ArgoCD detects the change and begins the sync immediately without requiring a PR review.

### Step 3: Rollout and Health Verification

ArgoCD syncs the production cluster to the previous image version using a rolling update. New pods with the previous image version must pass the readiness probe before the old (failing) pods are terminated. The Controller streams pod status events to the Release Dashboard for real-time monitoring. If the rollback pods also fail readiness probes (indicating the previous version also has a problem), the Controller halts and pages the on-call engineer with an `EMERGENCY: rollback target unhealthy` alert. The Deployment Controller's SLA for rollback completion is 5 minutes from submission.

### Step 4: Confirmation and Incident Handoff

Once the rollback rollout completes, the monitoring service verifies that error rates have returned to baseline. A confirmation is posted to the on-call Slack channel: "Rollback for `{service}` to `{version}` complete. Error rate: 0.04% (baseline: 0.05%)." A post-deployment monitoring window begins for the rolled-back version. The on-call engineer is prompted to create an incident record and link it to the failed deployment for root cause analysis.

## Expected Results

- Rollback to previous version completes within 5 minutes of submission
- Service error rate returns to baseline within 2 minutes of rollback rollout completing
- An immutable RollbackDecision audit record is created with the trigger, decision, and outcome
- On-call engineer receives a Slack confirmation once rollback is complete
- The failed deployment version is flagged in the deployment history to prevent accidental re-promotion

## User Info

| Field | Value |
|-------|-------|
| Role | On-call engineer (manual trigger) or automated monitoring service |
| Permissions | Rollback permissions: service owner group or on-call rotation; no separate approval required for rollback |
| Trigger | Automated (metric threshold breach) or manual (Release Dashboard / CLI) |
| Environment | Production |
| SLA | Rollback complete within 5 minutes of submission |
