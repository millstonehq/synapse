---
id: SOP-069
type: sop
title: Emergency Hotfix Deployment SOP
status: approved
owner: DevOps Lead
created: '2024-02-26T03:31:59.369Z'
updated: '2025-02-25T00:40:51.833Z'
tags:
  - sop
  - ci-cd-platform
summary: Emergency Hotfix Deployment SOP
related_process: PROCESS-042
related_systems:
  - SYSTEM-031
example: true
---

## Preconditions

- An active production incident requires an immediate code fix that cannot wait for the normal deployment review cycle
- An engineering manager or on-call lead has verbally authorized the emergency deployment
- The hotfix code change has been written, reviewed by at least one other engineer (synchronous review is acceptable), and CI has passed

## Materials/Access

- Write access to the hotfix branch and the production GitOps manifest repository
- Access to the CI platform to monitor the expedited pipeline run
- Access to the ArgoCD UI (or equivalent) to trigger and monitor the production deployment
- Access to the Grafana dashboard for the affected service
- The active incident channel and the #deployments Slack channel

## Procedure

1. Create a hotfix branch from the latest production commit (not from the main branch if main contains unreleased features): `git checkout -b hotfix/<incident-id> v<last-production-tag>`.
2. Apply the minimal code fix required to resolve the incident; do not bundle unrelated changes into the hotfix.
3. Open an emergency pull request with the incident ID in the title; obtain synchronous review approval from one other engineer (video call or direct message confirmation is acceptable).
4. Merge the pull request; the CI pipeline must run all stages including security scan — no pipeline stages may be bypassed even for emergency hotfixes.
5. Once CI passes, tag the hotfix commit with a patch version tag (e.g., `v1.4.3`) and push the tag to trigger the release pipeline.
6. In the GitOps manifest repository, update the production image tag to the hotfix version and merge directly to main with the incident ID in the commit message.
7. Confirm ArgoCD syncs the hotfix to production and all pods are running the new version; monitor the Grafana dashboard for 10 minutes.
8. Post in the incident channel and #deployments: "Hotfix [version] deployed. Monitoring. Incident ID: [ID]."
9. Retroactively create the deployment record within 4 hours of deployment, documenting the authorization, reviewer, and incident reference.

## Validation

- All pods are running the hotfix version in ArgoCD with "Healthy" status
- The incident condition that triggered the hotfix has been resolved (confirmed by incident commander)
- Error rate and latency are returning to pre-incident baseline
- The deployment record is created and linked to the incident within 4 hours

## Rollback

1. If the hotfix does not resolve the incident or introduces new failures, roll back to the previous production version immediately using the Roll Back Production Deployment SOP.
2. Document the failed hotfix attempt in the incident timeline before attempting a second hotfix.
3. If two consecutive hotfix attempts fail, escalate to a war room with the engineering manager and a principal engineer.
