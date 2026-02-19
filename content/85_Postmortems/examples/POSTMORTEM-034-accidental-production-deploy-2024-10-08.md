---
id: POSTMORTEM-034
type: postmortem
title: Accidental Production Deploy 2024-10-08
status: draft
owner: Incident Commander
created: '2024-12-10T08:45:31.223Z'
updated: '2026-12-28T09:13:53.252Z'
tags:
  - postmortem
  - ci-cd-platform
summary: Accidental Production Deploy 2024-10-08
incident_number: INC-645
severity: SEV-3
incident_date: '2025-08-05'
detection_time: '2024-07-13T14:35:34.493Z'
resolution_time: '2025-04-25T11:16:22.887Z'
total_duration: ~15 minutes
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-061
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On October 8, 2024, a developer accidentally triggered a production deployment of a staging-only feature branch for the `user-profile` service. The developer ran an ArgoCD CLI command intending to target the staging Application but omitted the `--app` flag correctly, causing ArgoCD to match the production Application instead. The deployment went live for approximately 15 minutes before detection and rollback. The feature branch was not production-ready and contained unfinished API changes that broke the user profile update flow for affected users.

## Timeline

- **14:22** - Developer runs `argocd app sync user-profile --revision feature/new-profile-api` in a terminal intended for staging
- **14:22** - ArgoCD syncs the production `user-profile` Application with the feature branch revision
- **14:24** - `user_profile_update_5xx_rate_high` alert fires. On-call engineer acknowledges.
- **14:26** - On-call identifies the ArgoCD sync in the deployment history — production was synced to an unexpected revision
- **14:28** - On-call initiates rollback to the previous production revision
- **14:30** - Rollback sync completes. Error rate drops to zero.
- **14:37** - Metrics stable. All-clear posted in #deployments.

## Impact

- **Duration**: ~15 minutes (14:22 - 14:37 UTC)
- **Users affected**: All users attempting to update their profile during the window; ~380 failed requests
- **Revenue impact**: None directly; no financial transactions involved
- **SLA impact**: `user-profile` service availability for October: 99.96%
- **Data impact**: None — no writes succeeded due to the API contract mismatch returning errors

## Root Cause Analysis

1. **No environment confirmation step in ArgoCD CLI**: The ArgoCD CLI `app sync` command targets whichever Application matches the name in the current kubeconfig context. There was no prompt or confirmation showing which environment was being targeted before the sync was initiated.

2. **Production ArgoCD Applications accessible from shared developer terminals**: Developers had RBAC access to trigger syncs on production Applications from their local machines. This made accidental production operations possible without any confirmation layer.

## Resolution

1. On-call identified the unexpected revision in ArgoCD deployment history
2. Initiated ArgoCD rollback to the last production-promoted revision (v1.8.3)
3. Confirmed user-profile API returned to normal error rates
4. Developer notified; no disciplinary action — process gap, not human error

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Restrict production ArgoCD sync RBAC to CI service accounts and Deployment Controller only | Platform team | P1 | 2024-10-15 | Completed |
| Add environment label to ArgoCD Application names (`user-profile-prod` vs `user-profile-staging`) | Platform team | P1 | 2024-10-15 | Completed |
| Add ArgoCD sync confirmation prompt for production Applications via UI/policy | Platform team | P2 | 2024-10-25 | Completed |
| Update onboarding docs to clarify ArgoCD production access model | Platform team | P3 | 2024-11-01 | Completed |

## Lessons Learned

- **What went well**: Alert fired within 2 minutes. Rollback was fast and clean. No data was lost.
- **What went poorly**: Developers had RBAC access to trigger production syncs directly. This was unnecessary and created risk.
- **What was lucky**: The feature branch changes were API-breaking but not data-corrupting. All user requests failed safely with errors rather than writing bad data.
- **Architecture improvement**: Production deployments should only be initiated by the Deployment Controller, not directly by engineers via CLI. RBAC is now enforced accordingly.
