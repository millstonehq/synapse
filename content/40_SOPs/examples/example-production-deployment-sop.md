---
id: deploy-with-rollback-sop
type: sop
title: Production Deployment with Rollback
status: draft
owner: Release Manager
created: '2025-10-18T19:48:03.162Z'
updated: '2025-10-18T19:48:03.162Z'
tags:
  - sop
summary: Step-by-step procedure to deploy a service to production with a verified rollback plan.
related_process: change-management-process
example: true
---
## Related Process

Change Management

## Preconditions

- Deployment artifact built and tested
- Approved change ticket
- Maintenance window approved


## Materials/Access

- \_\[TODO: Complete this section]\_

## Procedure

1. Announce start of maintenance window in
1. Validate artifact integrity (checksum/signature)
1. Trigger deployment pipeline to production
1. Monitor health checks and error rates for 15 minutes
1. If SLOs are degraded, execute rollback procedure


## Validation

Verify service health dashboards and error rates are within SLO; run smoke tests.


## Rollback

Trigger automated rollback pipeline; restore previous stable version; verify recovery.
