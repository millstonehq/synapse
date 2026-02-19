---
id: SOP-016
type: sop
title: Deploy Authentication Service Update SOP
status: proposed
owner: DevOps Lead
created: '2024-04-16T11:40:03.274Z'
updated: '2026-12-30T02:20:29.016Z'
tags:
  - sop
  - user-authentication
summary: Deploy Authentication Service Update SOP
related_process: PROCESS-062
related_systems:
  - SYSTEM-007
example: true
---

## Preconditions

- CI is green on the authentication service repository with all tests passing
- Change ticket is approved by Platform Lead with risk classification confirmed
- Deployment artifact exists in the container registry tagged with the target commit SHA
- Security Engineer has reviewed any changes to token format, session logic, or cryptographic operations
- The on-call engineer is available and the deployment window (Tue–Thu, 10am–2pm) is confirmed

## Materials/Access

- Access to the deployment dashboard (ArgoCD or equivalent) with authentication service namespace permissions
- Access to the authentication monitoring dashboard (Grafana)
- `kubectl` configured for the production cluster (for emergency interventions)
- Authentication service smoke test script (`./scripts/auth-smoke-test.sh`)
- The commit SHA being deployed and the change ticket ID

## Procedure

1. Post in #auth-deployments: "Starting auth service deploy @ [commit SHA] for [CHANGE-TICKET]. On-call: [name]. ETA: 15 min."
2. Open the authentication monitoring dashboard and record baseline metrics: login success rate, token issuance rate, P95 authentication latency, and error rate.
3. In the deployment dashboard, select the `auth-service` deployment in the `auth` namespace and set the image tag to the target commit SHA.
4. Click "Sync" to initiate the rolling deployment. Watch rollout status until all new pods pass health checks and old pods are terminated.
5. Immediately run the authentication smoke test suite: `./scripts/auth-smoke-test.sh --env production`. Tests cover: login flow, token issuance, token refresh, logout, and MFA challenge.
6. Verify smoke tests pass (all green). If any test fails, proceed immediately to Rollback.
7. Monitor authentication metrics for 30 minutes post-deploy. If login success rate drops below 99% or P95 latency increases by more than 200ms, initiate Rollback.
8. After 30 minutes with stable metrics and passing smoke tests, post in #auth-deployments: "Auth service deploy @ [commit SHA] complete. Metrics stable."
9. Update the change ticket: mark as deployed, attach commit SHA, smoke test results screenshot, and metrics screenshot.

## Validation

- All authentication smoke tests pass against the production deployment
- Login success rate is >= 99% (baseline or better)
- Token issuance P95 latency has not increased by more than 200ms
- No new alert has fired in the auth service alert group
- Deployment dashboard confirms all pods are running the new image with no restart loops

## Rollback

1. Post in #auth-deployments: "ROLLING BACK auth service @ [commit SHA]. Reason: [description]."
2. In the deployment dashboard, revert the `auth-service` image tag to the previous stable commit SHA and click "Sync".
3. Wait for all pods to roll back; confirm rollout complete in the deployment dashboard.
4. Re-run authentication smoke tests against the rolled-back version to confirm restoration.
5. If smoke tests fail after rollback, escalate immediately to Platform Lead and Security Engineer.
6. Update the change ticket: mark as rolled back with timestamp and reason. Create a post-incident ticket for root cause analysis.
