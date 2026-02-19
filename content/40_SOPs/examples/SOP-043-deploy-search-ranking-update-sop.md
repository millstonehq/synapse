---
id: SOP-043
type: sop
title: Deploy Search Ranking Update SOP
status: draft
owner: Release Manager
created: '2025-12-26T12:04:36.358Z'
updated: '2025-02-02T10:41:27.766Z'
tags:
  - sop
  - search-platform
summary: Deploy Search Ranking Update SOP
related_process: PROCESS-028
related_systems:
  - SYSTEM-022
example: true
---

## Preconditions

- The ranking update has completed offline evaluation with NDCG@10 meeting or exceeding the production baseline
- A change ticket is approved and linked to the ranking configuration PR
- A/B test has concluded with statistically significant positive results (if this is a full rollout of a previously tested variant)
- The rollback ranking configuration (current production parameters) is documented in the change ticket
- On-call SRE is available and aware of the deployment window

## Materials/Access

- Access to the ranking configuration repository and deployment pipeline
- Grafana: Search Query Performance dashboard (P50/P95 latency, error rate, CTR trend)
- Feature flag management console (for feature-flag-gated ranking changes)
- The approved ranking configuration file (field weights, function scores, boost definitions)
- Change ticket ID with Platform Lead approval

## Procedure

1. Post in #search-deployments: "Starting ranking update deploy for [CHANGE-TICKET]. On-call: [name]. Rollback config: [commit SHA of current production config]."
2. Review the current ranking configuration in production to confirm it matches the documented rollback baseline. Run a spot check on 5 known test queries to record current result order.
3. Deploy the new ranking configuration via the deployment pipeline. For configuration-only changes this is a hot reload; for changes requiring a new service deployment, follow the standard blue-green deploy process.
4. Wait for the deployment pipeline to confirm the new configuration is active on all query nodes.
5. Run the same 5 test queries from step 2 against production and verify the result order has changed in the expected direction.
6. Open Grafana and monitor the following metrics for 15 minutes: P95 query latency, error rate, and (if available in near-real-time) CTR. Establish the pre-deploy baseline before monitoring.
7. If P95 latency increases by more than 10% or error rate increases by more than 0.1 percentage points, immediately initiate rollback.
8. After 15 minutes with stable metrics, post in #search-deployments: "Ranking update deploy complete. Metrics stable. CTR trend will be assessed in 24 hours."
9. Close the change ticket with deployment evidence: configuration commit SHA, deploy timestamp, and screenshots of stable metrics.

## Validation

- Deployment pipeline confirms new ranking configuration is active on all query nodes
- P95 query latency has not increased by more than 10% from pre-deploy baseline
- Error rate has not increased by more than 0.1 percentage points
- Test query spot check shows result ordering consistent with expected ranking behavior
- No new alerts fired in the 15-minute post-deploy monitoring window

## Rollback

1. Post in #search-deployments: "ROLLING BACK ranking update [CHANGE-TICKET]. Reason: [brief description]."
2. Redeploy the previous ranking configuration using the rollback commit SHA documented in the change ticket.
3. Wait for the rollback configuration to be active on all query nodes; confirm via the deployment pipeline.
4. Run the 5 test queries again and verify result order has returned to the pre-deploy state.
5. Confirm P95 latency and error rate return to pre-deploy baselines within 5 minutes of rollback completion.
