---
id: POSTMORTEM-031
type: postmortem
title: Production Deployment Rollback 2025-01-25
status: deprecated
owner: Incident Commander
created: '2025-09-22T01:19:48.037Z'
updated: '2025-08-02T16:28:07.425Z'
tags:
  - postmortem
  - ci-cd-platform
summary: Production Deployment Rollback 2025-01-25
incident_number: INC-642
severity: SEV-2
incident_date: '2026-08-12'
detection_time: '2025-01-23T18:09:59.513Z'
resolution_time: '2024-07-10T13:00:13.927Z'
total_duration: ~2 hours
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-068
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On January 25, 2025, a production deployment of the `order-processing` service introduced a database migration that altered a column type used by a live query. The deployment passed all CI checks but caused a type mismatch at runtime, resulting in 5xx errors for all order creation requests within 8 minutes of the deploy. The on-call engineer initiated a rollback via ArgoCD, which completed in 4 minutes and restored service. Total outage duration was 22 minutes.

The post-deploy monitoring window of 15 minutes was insufficient to catch the failure pattern, which only manifested above a certain traffic volume threshold reached 8 minutes after deployment.

## Timeline

- **11:02** - Deployment of `order-processing` v2.4.1 initiated via Deployment Controller
- **11:04** - ArgoCD sync completes; health checks pass; deployment marked successful
- **11:10** - First errors appear in logs: `ERROR: operator does not exist: integer = text`
- **11:12** - `order_processing_5xx_rate_high` alert fires. On-call engineer acknowledges.
- **11:14** - On-call identifies recent deploy as likely cause. Initiates rollback via ArgoCD UI.
- **11:18** - Rollback sync completes. Error rate drops immediately to zero.
- **11:24** - Metrics stable. On-call posts all-clear in #deployments.

## Impact

- **Duration**: 22 minutes (11:02 - 11:24 UTC)
- **Services affected**: `order-processing` (all order creation endpoints)
- **Users affected**: All users attempting to create orders during the window
- **Requests failed**: ~1,200 order creation requests returned 500 errors
- **Revenue impact**: Estimated $4,800 in lost or delayed orders
- **SLA impact**: `order-processing` monthly uptime dropped to 99.95%

## Root Cause Analysis

1. **Schema migration not backward-compatible**: The migration changed the `product_id` column from `integer` to `text` to support alphanumeric product IDs. The query in the new application code used `= text`, but the migration ran before the new code was deployed, leaving a window where the old code ran against the new schema. The reverse order should have been enforced.

2. **Health check did not exercise the failing code path**: The readiness probe checked `/healthz`, which does not call the database. A more comprehensive smoke test exercising a real order creation call would have caught the error before traffic shifted.

## Resolution

1. On-call engineer identified the deploy as the root cause via log analysis
2. Initiated ArgoCD rollback to the previous image tag (v2.4.0)
3. Monitored error rate for 15 minutes to confirm full recovery
4. Coordinated with service team to develop a safe re-deploy strategy using expand/contract migration pattern

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add post-deploy smoke test to order creation endpoint | Service team | P1 | 2025-02-01 | Completed |
| Document expand/contract migration pattern in deployment guide | Platform team | P1 | 2025-02-05 | Completed |
| Extend post-deploy monitoring window from 15 min to 30 min | Platform team | P2 | 2025-02-10 | Completed |
| Add migration compatibility check to CI pipeline | Platform team | P2 | 2025-02-28 | In progress |

## Lessons Learned

- **What went well**: Alerting fired within 2 minutes of errors starting. Rollback was initiated quickly and completed in 4 minutes, well within the 5-minute target.
- **What went poorly**: The CI pipeline did not catch the schema/code version incompatibility. Health checks were too shallow to detect the failure before traffic was shifted.
- **What was lucky**: The rollback path was clean — no irreversible schema changes had been made, so reverting the image was sufficient.
- **Process gap**: The team was not aware of the expand/contract migration pattern. This is now documented in the deployment guide.
