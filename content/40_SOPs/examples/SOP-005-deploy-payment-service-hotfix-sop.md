---
id: SOP-005
type: sop
title: Deploy Payment Service Hotfix SOP
status: approved
owner: Release Manager
created: '2024-06-26T13:44:08.145Z'
updated: '2026-03-28T18:18:21.290Z'
tags:
  - sop
  - payment-processing
summary: Deploy Payment Service Hotfix SOP
related_process: PROCESS-005
related_systems:
  - SYSTEM-005
example: true
---

## Preconditions

- A production incident has been declared and the hotfix has been identified as the resolution path
- The hotfix code has been reviewed by at least one senior engineer (expedited review is acceptable for P1 incidents)
- CI has passed on the hotfix branch (all payment service tests must pass; waivers require Engineering Manager approval)
- The Engineering Manager or Director of Engineering has authorized the hotfix deployment
- The on-call engineer is actively monitoring the payment service during the deployment

## Materials/Access

- Access to the CI/CD pipeline to trigger a hotfix build and deployment
- Access to the payment service deployment dashboard (ArgoCD or equivalent)
- Access to the payment observability dashboard to monitor success rates and latency
- #payment-incidents Slack channel for real-time coordination
- Rollback image tag from the last known good deployment

## Procedure

1. Post in #payment-incidents: "Initiating hotfix deployment for [service] to address [incident description]. Authorized by: [name]."
2. Confirm the hotfix Docker image has been built and pushed to the container registry; note the image tag.
3. Note current baseline metrics on the observability dashboard: payment success rate, P95 authorization latency, error rate by code.
4. In the deployment dashboard, update the payment service image tag to the hotfix image tag.
5. Trigger a rolling deployment and monitor the pod restart progress; do not proceed until all pods are healthy.
6. Verify the hotfix is live by checking the service version endpoint or a log line confirming the new build SHA.
7. Monitor payment success rate and error codes for 10 minutes; confirm the issue is resolved (success rate > 99%, incident errors absent).
8. Post status update in #payment-incidents: "Hotfix deployed successfully. Success rate: X%. Incident resolved."
9. Update the change ticket with hotfix image tag, deployment timestamp, and post-deploy metrics screenshot.
10. Schedule a post-incident review within 48 hours; the hotfix must be followed by a proper fix and standard deployment within 5 business days.

## Validation

- Payment success rate has returned to or above pre-incident baseline
- The specific error causing the incident is no longer appearing in payment logs
- All payment service pods are running the hotfix image version with no crash loops
- Merchant and customer-facing webhooks are delivering successfully
- No new alert conditions have fired since the hotfix deployment

## Rollback

1. If the hotfix causes new issues or does not resolve the incident, post in #payment-incidents: "ROLLING BACK hotfix [image tag]. Reason: [description]."
2. In the deployment dashboard, revert the payment service image tag to the last known good image tag (recorded before deployment).
3. Trigger a rolling deployment to the reverted image; monitor pod health until all pods are running the previous version.
4. Confirm payment success rate returns to baseline within 5 minutes of rollback completion.
5. Re-assess the incident with the original state restored; escalate to Director of Engineering if rollback does not resolve the incident.
