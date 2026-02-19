---
id: SOP-096
type: sop
title: Deploy Billing Service Update SOP
status: review
owner: SRE Lead
created: '2025-05-28T21:32:11.590Z'
updated: '2026-06-19T09:44:52.304Z'
tags:
  - sop
  - billing-engine
summary: Deploy Billing Service Update SOP
related_process: PROCESS-058
related_systems:
  - SYSTEM-046
example: true
---

## Preconditions

- CI is green on the `main` branch for the billing service — all tests pass including billing calculation unit tests and integration tests
- The change ticket is approved; for changes touching invoice generation, tax logic, or payment processing it requires senior engineer sign-off
- The billing service Docker image is built and tagged with the target commit SHA in the container registry
- No monthly billing cycle run is in progress (check the billing run dashboard status)
- The on-call engineer is available and aware of the deployment
- If the update includes a database schema migration, the migration has been validated against a production-data clone

## Materials/Access

- Access to the deployment dashboard (ArgoCD)
- Access to the billing run dashboard in Grafana
- Access to the billing service error log in the log aggregation system
- `kubectl` configured for the production cluster (for emergency rollback only)
- The approved change ticket ID and the target commit SHA

## Procedure

1. Post in #billing-deployments: "Starting billing service deploy @ [commit SHA]. Change ticket: [ID]. On-call: [name]."
2. Open the billing run dashboard and confirm no billing cycle run is `IN_PROGRESS`. If a run is active, wait for it to complete before proceeding.
3. Note current baseline metrics from Grafana: invoice generation success rate, payment gateway call latency, and billing API error rate.
4. In ArgoCD, select the `billing-service` application and update the image tag to the target commit SHA. Click **Sync**.
5. Watch the rollout in ArgoCD until all billing service pods are healthy and the old pods are terminated.
6. Verify the new version is serving traffic by checking the billing API health endpoint returns the expected version tag.
7. Monitor the billing run dashboard and error logs for 15 minutes. Compare invoice generation rate, error rate, and latency against the baseline noted in step 3.
8. If metrics are stable, post in #billing-deployments: "Billing service deploy complete @ [commit SHA]. Metrics stable."
9. Update the change ticket: mark as deployed with commit SHA, deployment timestamp, and a screenshot of stable billing metrics.

## Validation

- All billing service pods are running the new version with no restarts
- Invoice generation success rate has not decreased from pre-deploy baseline
- Billing API error rate is below 0.5%
- Payment gateway integration health check passes
- No new alerts in #billing-incidents during the monitoring window

## Rollback

1. Post in #billing-deployments: "ROLLING BACK billing service @ [commit SHA]. Reason: [description]."
2. In ArgoCD, revert the `billing-service` image tag to the previous stable commit SHA and click **Sync**.
3. Wait for all pods to return to the previous version and confirm they are healthy.
4. Verify billing metrics return to the pre-deploy baseline within 5 minutes.
5. Post in #billing-deployments: "Billing service rollback complete. Metrics stable."
6. Update the change ticket with rollback timestamp and reason. Create a follow-up investigation ticket.
