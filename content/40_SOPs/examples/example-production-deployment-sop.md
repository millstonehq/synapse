---
id: deploy-with-rollback-sop
type: sop
title: Production Deployment with Rollback
status: approved
owner: Release Manager
created: '2025-10-18T00:00:00.000Z'
updated: '2025-10-18T00:00:00.000Z'
tags:
  - sop
  - deployments
  - production
summary: >-
  Step-by-step procedure to deploy a service to production and roll back
  if needed. USE AN SOP when someone needs to EXECUTE a specific
  operational task with exact steps, validation checks, and a rollback
  plan. SOPs answer "what are the exact steps to do X?" They assume the
  reader already understands the concepts (from a Guide) and has
  authorization (from a Process). SOPs are prescriptive and verifiable -
  every step has a clear done/not-done state. Compare: a Process defines
  who approves the deployment and when; a Guide explains how deployments
  work conceptually; a Runbook handles when the deployment causes an
  incident.
related_process: change-management-process
related_systems:
  - payments-api-system
example: true
---

## Preconditions

- CI is green on `main` branch - no failing tests or broken builds
- Change ticket is approved (low-risk: peer review, high-risk: senior sign-off)
- Deployment artifact (Docker image) exists in the container registry tagged with the target commit SHA
- On-call engineer is available and aware of the deployment
- No other deployments are currently in progress (check #deployments channel)
- For database migrations: migration has been tested against a production-clone database

## Materials/Access

- Access to the deployment dashboard (ArgoCD or equivalent)
- Access to the monitoring dashboard (Grafana)
- Access to the #deployments Slack channel
- `kubectl` configured for the production cluster (for emergency interventions only)
- The commit SHA being deployed
- The change ticket ID

## Procedure

1. Post in #deployments: "Starting deploy of [service] @ [commit SHA] for [CHANGE-TICKET]. On-call: [name]."
2. Open the monitoring dashboard and note current baseline metrics: error rate, P95 latency, request throughput
3. In the deployment dashboard, select the target service and set the image tag to the target commit SHA
4. Click "Sync" to initiate the blue-green deployment. Watch the rollout status until all new pods are healthy
5. Verify the new pods are serving traffic by checking the deployment dashboard shows 100% shifted
6. Check the monitoring dashboard: compare error rate, latency, and throughput against the baseline noted in step 2
7. Wait 15 minutes while monitoring. Check metrics at 5-minute intervals. If any SLO is breached (error rate > 1%, P95 > 1s), proceed immediately to Rollback
8. After 15 minutes with stable metrics, post in #deployments: "Deploy of [service] @ [commit SHA] complete. Metrics stable."
9. Update the change ticket: mark as deployed, attach the commit SHA, timestamp, and a screenshot of stable metrics

## Validation

After completing the procedure, verify all of the following:

- The deployment dashboard shows the new version running on all pods with no restarts
- Error rate has not increased by more than 0.1% from baseline
- P95 latency has not increased by more than 100ms from baseline
- Business metrics (order completion, payment success) are within normal range
- No new alerts have fired in the alerting system
- The change ticket is updated with deployment evidence

If any validation check fails, execute the Rollback procedure below.

## Rollback

If at any point during or after deployment metrics degrade:

1. Post in #deployments: "ROLLING BACK [service] @ [commit SHA]. Reason: [brief description]."
2. In the deployment dashboard, revert the image tag to the previous stable commit SHA
3. Click "Sync" and wait for all pods to roll back to the previous version
4. Verify metrics return to baseline within 5 minutes
5. If metrics do not recover after rollback, escalate to the on-call engineer and follow the [[example-service-outage-runbook|Service Outage Runbook]]
6. Post in #deployments: "Rollback of [service] complete. Metrics recovered."
7. Update the change ticket: mark as rolled back with timestamp and reason
8. Create a post-incident ticket to investigate the failure within 48 hours
