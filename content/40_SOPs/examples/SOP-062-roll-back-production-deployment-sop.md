---
id: SOP-062
type: sop
title: Roll Back Production Deployment SOP
status: approved
owner: SRE Lead
created: '2025-10-31T12:34:09.896Z'
updated: '2025-01-19T04:57:27.122Z'
tags:
  - sop
  - ci-cd-platform
summary: Roll Back Production Deployment SOP
related_process: PROCESS-042
related_systems:
  - SYSTEM-032
example: true
---

## Preconditions

- A production deployment has been completed within the last 4 hours and is suspected to be causing degradation
- Monitoring dashboard shows one or more SLO breaches: error rate above 1%, P95 latency above defined threshold, or critical business metric regression
- You have write access to the GitOps manifest repository and access to the deployment approval system
- You have identified the commit SHA of the previous stable deployment from the deployment record

## Materials/Access

- Access to the GitOps manifest repository (write access required to update image tags)
- Access to the GitOps controller UI (ArgoCD or equivalent) to monitor the rollout
- Access to the monitoring dashboard (Grafana) to compare metrics
- The deployment record for the current deployment (contains previous stable SHA)
- Access to #deployments Slack channel for communication

## Procedure

1. Post immediately in #deployments: "ROLLING BACK [service-name] — current version [new-sha] is causing [brief description of issue]. Reverting to [previous-sha]."
2. Open the deployment record to retrieve the previous stable image tag; confirm the previous stable version is present in the container registry before proceeding.
3. In the GitOps manifest repository, update the image tag for the affected service from the current SHA to the previous stable SHA.
4. Commit the change with the message "ROLLBACK: revert [service-name] to [previous-sha] — [reason]. Bypassing review." and push directly to the main branch.
5. Open the GitOps controller UI (ArgoCD), find the application for the affected service, and click "Sync" to ensure the rollback manifest is applied immediately without waiting for automatic reconciliation.
6. Monitor the pod rollout in the GitOps controller until all replicas are running the previous version and show "Healthy" status.
7. Check the monitoring dashboard: confirm error rate, latency, and business metrics are returning toward pre-deployment baseline; allow up to 5 minutes for full recovery.
8. Post in #deployments: "ROLLBACK of [service-name] to [previous-sha] complete. Metrics recovering / recovered." and update the deployment record status to "Rolled Back."
9. Create a follow-up ticket for root cause investigation, link it to the deployment record, and assign it to the Change Owner.

## Validation

- GitOps controller shows the application in "Synced/Healthy" state with the previous stable image tag
- All pod replicas are running the previous version with no restart loops
- Monitoring dashboard shows error rate, latency, and business metrics within normal SLO bounds
- Deployment record is updated to "Rolled Back" with timestamp and reason

## Rollback

1. If the previous stable image tag is no longer present in the registry (expired or deleted), escalate immediately to the Platform Engineer on-call and follow the registry recovery runbook.
2. If the GitOps controller fails to sync the rollback manifest, manually apply it using `kubectl apply -f <manifest-path>` on the production cluster and notify the platform team.
3. If metrics do not recover within 10 minutes of rollback, open a P1 incident and escalate to the Incident Commander.
