---
id: FLOW-026
type: flow
title: Production Deployment Flow
status: approved
owner: QA Engineer
created: '2024-09-30T17:28:21.958Z'
updated: '2025-05-19T03:49:44.133Z'
tags:
  - flow
  - ci-cd-platform
summary: Production Deployment Flow
feature_area: CI/CD Platform
related_prds:
  - PRD-035
example: true
---

## Steps

### Step 1: Artifact Promotion Gate

Before a production deployment can begin, the target image must have passed the staging promotion gate. The artifact promotion pipeline verifies that the container image digest has a clean Trivy vulnerability scan (no critical CVEs), a valid Cosign signature, and a passing canary analysis run in staging. If any gate fails, the promotion is blocked and the deploying engineer receives a Slack notification identifying the failing gate. No production deployment can begin until these checks pass.

### Step 2: Approval Request

The Deployment Controller creates an ApprovalRequest for the production deployment and sends a Slack notification to the service owner's designated approver group. The notification includes the image tag, commit SHA, GitHub commit message, and a link to the diff. Approvers have a configurable window (default: 4 hours) to approve or reject. If no action is taken within the window, the request expires and the engineer must re-initiate. For services configured with `auto` gate mode, this step is skipped and the deployment proceeds immediately after the promotion gate.

### Step 3: Deployment Execution

Upon approval, the Deployment Controller updates the Kubernetes manifest repository (via a merged PR to the production overlay) and ArgoCD detects the change and begins syncing the new image to the production Kubernetes cluster. ArgoCD performs a rolling update, deploying the new pods alongside the existing ones. New pods must pass the readiness probe (typically a `/healthz` check verifying database and dependency connectivity) before traffic is shifted. If the readiness probe fails for any new pod within the configured timeout, ArgoCD halts the rollout and the Deployment Controller triggers an automatic rollback.

### Step 4: Post-Deployment Monitoring

Once the rollout completes, the automated post-deployment monitoring window begins (default: 10 minutes for standard services, 30 minutes for high-risk changes). The monitoring service watches error rate and P95 latency against the service's configured thresholds. If a threshold is breached for 2 consecutive minutes, the automated rollback system posts a Slack notification with a 60-second veto window before initiating rollback. The deployment is considered successful after the monitoring window completes without a threshold breach.

## Expected Results

- Production deployments complete within 10 minutes of approval for standard-sized services
- All production deployments have an audit record including approver identity, image digest, and deployment timestamp
- Services with failing readiness probes are never exposed to live traffic; the old version remains live until the new version is healthy
- Post-deployment error rate and latency are continuously monitored for 10–30 minutes after each deployment
- Any deploy-caused regression triggers an automated rollback without requiring manual on-call intervention for clear-cut error rate spikes

## User Info

| Field | Value |
|-------|-------|
| Role | CI service account (Deployment Controller) and approver engineer |
| Permissions | Approver: approve/reject deployments for their service group; Controller: ArgoCD sync, Harbor image pull |
| Trigger | Successful staging promotion gate + approval grant |
| Environment | Production Kubernetes cluster |
| Rollback | One-click via Release Dashboard or automated via monitoring service |
