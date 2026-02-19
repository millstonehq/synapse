---
id: SOP-066
type: sop
title: Promote Build to Production SOP
status: draft
owner: Release Manager
created: '2025-06-05T23:17:32.256Z'
updated: '2026-06-20T05:31:38.215Z'
tags:
  - sop
  - ci-cd-platform
summary: Promote Build to Production SOP
related_process: PROCESS-041
related_systems:
  - SYSTEM-031
example: true
---

## Preconditions

- The build artifact (container image) has successfully passed all CI stages: lint, test, build, security scan, and publish
- The image is tagged with the correct commit SHA and is present in the staging registry namespace
- The deployment record has been created, the risk tier selected, and approval obtained per the Deployment Approval Policy
- Staging environment has been running this image version for at least 30 minutes without SLO violations
- The on-call engineer is available and has been notified of the pending promotion

## Materials/Access

- Access to the container registry to retag the image for the production namespace
- Write access to the GitOps manifest repository to update the production image tag
- Access to the ArgoCD UI (or equivalent GitOps controller) to trigger and monitor the sync
- Access to the Grafana monitoring dashboard for the target service
- The approved deployment record ID

## Procedure

1. Verify in the registry that the image tag matches the expected commit SHA and that the image signature is valid; if verification fails, stop and contact the Security team.
2. Retag the image in the container registry from the staging namespace to the production namespace: `docker buildx imagetools create --tag <prod-registry>/<service>:<version> <staging-registry>/<service>:<sha>`.
3. Update the image tag in the production GitOps manifest file for the service from the current production SHA to the new version tag.
4. Open a pull request for the manifest change; tag it with the deployment record ID in the title (e.g., "[DEPLOY-042] Promote payments-api to v1.4.2").
5. Obtain peer review approval on the manifest pull request; merge to trigger automatic GitOps reconciliation.
6. Open the ArgoCD UI, locate the application, and confirm "Synced/Healthy" status; watch the pod rollout until all replicas are running the new version.
7. Monitor the Grafana dashboard for the service for 15 minutes, checking error rate, P95 latency, and key business metrics at 5-minute intervals.
8. If metrics are stable, post in #deployments: "Promoted [service] to [version] — all checks passing." and close the deployment record as succeeded.

## Validation

- ArgoCD shows the application as "Synced" with the new image tag and "Healthy" pod status
- All replicas show the new version in `kubectl get pods -o wide`
- Error rate has not increased by more than 0.1% from the pre-promotion baseline
- P95 latency is within 50ms of the pre-promotion baseline
- Deployment record is closed with promotion timestamp and metric evidence

## Rollback

1. If metrics degrade during the 15-minute observation window, revert the GitOps manifest to the previous image tag immediately and follow the Roll Back Production Deployment SOP.
2. If the ArgoCD sync stalls or shows errors, check the ArgoCD logs for resource conflicts and escalate to the platform team if the sync cannot be resolved within 5 minutes.
3. Update the deployment record to "Rolled Back" with the timestamp and reason before opening a post-deploy review ticket.
