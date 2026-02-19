---
id: SOP-081
type: sop
title: Deploy Customer Portal Release SOP
status: approved
owner: DevOps Lead
created: '2025-09-02T07:55:07.095Z'
updated: '2025-08-23T08:26:10.175Z'
tags:
  - sop
  - customer-portal
summary: Deploy Customer Portal Release SOP
related_process: PROCESS-050
related_systems:
  - SYSTEM-043
example: true
---

## Preconditions

- CI is green on the release candidate branch; no failing tests or linting errors
- QA has signed off on the staging regression suite for this release
- Change ticket is approved with rollback plan documented
- On-call engineer is available and monitoring #customer-portal-deployments
- No active P1 or P2 incidents in the Customer Portal environment
- All database migrations in this release have been tested against a production-clone database

## Materials/Access

- Access to the Customer Portal deployment dashboard (ArgoCD)
- Access to the Grafana portal monitoring dashboard
- Write access to the #customer-portal-deployments Slack channel
- Release ticket ID and release candidate commit SHA
- Feature flag console access (for any flags shipping with this release)

## Procedure

1. Post in #customer-portal-deployments: "Starting portal release [VERSION] @ [COMMIT-SHA] for [RELEASE-TICKET]. On-call: [name]. ETA: 15 min."
2. Open Grafana portal dashboard and record baseline metrics: error rate, P95 API latency, active session count, and CDN hit ratio.
3. If this release includes database migrations, execute migrations first in the ArgoCD jobs panel and wait for completion before proceeding.
4. In ArgoCD, select the `customer-portal` application and update the image tag to the release candidate commit SHA.
5. Click "Sync" and monitor the rollout; wait for all pods to show healthy status before proceeding.
6. Verify the new version is serving traffic: check the version endpoint (`/api/health`) and confirm the deployed SHA matches.
7. Monitor Grafana for 15 minutes, checking at 5-minute intervals. If error rate exceeds 1% or P95 latency exceeds 800ms, proceed immediately to Rollback.
8. Enable any feature flags configured for this release in the feature flag console.
9. Post in #customer-portal-deployments: "Portal release [VERSION] complete. Metrics stable. Feature flags [ENABLED/NONE]."
10. Update the release ticket: mark as deployed, attach commit SHA, timestamp, and a Grafana screenshot showing stable metrics.

## Validation

- ArgoCD shows all portal pods running the new image SHA with no crash restarts
- Error rate has not increased more than 0.1% above pre-deploy baseline
- P95 API latency is within 100ms of pre-deploy baseline
- Active session count is stable (no mass session invalidation)
- No new critical alerts have fired in the monitoring system
- Release notes are published to the status page

## Rollback

1. Post in #customer-portal-deployments: "ROLLING BACK portal release [VERSION]. Reason: [brief description]."
2. In ArgoCD, revert the `customer-portal` image tag to the previously stable commit SHA.
3. Click "Sync" and wait for all pods to roll back to the previous version and show healthy.
4. If migrations were applied, execute the down-migration scripts in the ArgoCD jobs panel.
5. Verify metrics return to pre-deploy baseline within 5 minutes; post confirmation in #customer-portal-deployments.
