---
id: SOP-024
type: sop
title: Deploy Inventory Service Update SOP
status: accepted
owner: Release Manager
created: '2025-11-30T02:33:47.997Z'
updated: '2026-07-22T07:08:25.942Z'
tags:
  - sop
  - inventory-management
summary: Deploy Inventory Service Update SOP
related_process: PROCESS-014
related_systems:
  - SYSTEM-012
example: true
---

## Preconditions

- CI pipeline is passing on the target branch for the inventory service; no failing tests or linting errors
- Change ticket for this deployment has been approved (low-risk: peer review; high-risk: senior engineer sign-off)
- Docker image is built and tagged with the target commit SHA in the container registry
- If the update includes a database migration, the migration has been dry-run against a production-clone database and validated
- On-call engineer is available and has been notified of the planned deployment
- No other inventory service deployments are in progress (confirm in #inventory-deployments)

## Materials/Access

- ArgoCD access to the `inventory` namespace in the production Kubernetes cluster
- Grafana access to the Inventory Service dashboard
- Access to #inventory-deployments Slack channel
- The target commit SHA and change ticket ID
- `kubectl` configured for the production cluster (for emergency intervention only)

## Procedure

1. Post in #inventory-deployments: "Starting inventory service deploy @ [commit SHA] for [CHANGE-TICKET]. On-call: [name]. ETA: [time]."
2. Open the Inventory Service Grafana dashboard and record baseline metrics: error rate, P95 latency, sync event throughput, and active connection count.
3. If this deployment includes a database migration, run the migration first using the approved migration script. Verify row counts match expectations before proceeding.
4. In ArgoCD, select the inventory service application and update the image tag to the target commit SHA.
5. Click "Sync" to initiate the rolling deployment. Watch the rollout status in ArgoCD until all pods show healthy and the previous pods have terminated.
6. Compare current Grafana metrics to the baseline recorded in step 2: error rate, latency, and sync throughput should be within 10% of baseline.
7. Verify that inventory sync events are flowing correctly by checking that the event consumer lag metric has not increased since the deployment.
8. Monitor for 15 minutes, checking metrics at 5-minute intervals. If error rate exceeds 1% or P95 latency exceeds 1s, proceed immediately to Rollback.
9. Post in #inventory-deployments: "Inventory service deploy @ [commit SHA] complete. Metrics stable."
10. Update the change ticket: mark as deployed, attach commit SHA, timestamp, and a screenshot of stable metrics.

## Validation

- ArgoCD shows the new image tag running on all pods with zero restart events since deployment
- Error rate has not increased by more than 0.1% from pre-deployment baseline
- P95 latency has not increased by more than 100ms from baseline
- Kafka consumer lag for inventory events is stable or decreasing
- Inventory sync reconciliation report for the next scheduled run completes without errors
- Change ticket is updated with deployment evidence

## Rollback

1. Post in #inventory-deployments: "ROLLING BACK inventory service @ [commit SHA]. Reason: [brief description]."
2. In ArgoCD, revert the image tag to the previous stable commit SHA.
3. Click "Sync" and wait for all pods to roll back to the previous version; confirm in ArgoCD that rollout is complete.
4. If the deployment included a database migration, contact the DBA to assess whether a rollback migration is required.
5. Verify in Grafana that metrics return to pre-deployment baseline within 5 minutes of rollback completion.
6. Post rollback confirmation in #inventory-deployments with timestamp and metric screenshot.
7. Update change ticket to "rolled back" status with reason, and open a follow-up investigation ticket.
