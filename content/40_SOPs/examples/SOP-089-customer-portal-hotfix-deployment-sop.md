---
id: SOP-089
type: sop
title: Customer Portal Hotfix Deployment SOP
status: approved
owner: SRE Lead
created: '2024-12-09T02:56:02.190Z'
updated: '2025-10-27T03:36:05.672Z'
tags:
  - sop
  - customer-portal
summary: Customer Portal Hotfix Deployment SOP
related_process: PROCESS-049
related_systems:
  - SYSTEM-043
example: true
---

## Preconditions

- A P1 or P2 incident is active and the hotfix is the approved remediation path
- The hotfix fix has been committed, reviewed by at least one engineer, and CI is passing
- Engineering Manager or on-call lead has approved the hotfix deployment out-of-band
- Rollback plan is identified (previous stable SHA is known)

## Materials/Access

- Access to the Customer Portal deployment dashboard (ArgoCD)
- Access to Grafana portal monitoring dashboard
- Write access to #customer-portal-incidents and #customer-portal-deployments Slack channels
- Hotfix commit SHA and hotfix ticket ID
- Engineering Manager contact for approval sign-off

## Procedure

1. Post in #customer-portal-incidents: "Hotfix ready for deployment. Commit: [SHA]. Fixes: [brief description]. Ticket: [HOTFIX-TICKET]. Awaiting EM approval."
2. Obtain Engineering Manager explicit approval in the Slack thread or via the incident management system before proceeding.
3. Post in #customer-portal-deployments: "HOTFIX deployment starting. Commit: [SHA]. Ticket: [HOTFIX-TICKET]. On-call: [name]."
4. Open Grafana and note current incident-state metrics as a baseline for post-hotfix comparison.
5. In ArgoCD, update the `customer-portal` image tag to the hotfix commit SHA and click "Sync."
6. Monitor the rollout; wait for all pods to reach healthy status before declaring the deployment complete.
7. Verify the hotfix is live by checking the version endpoint and confirming the SHA matches the hotfix commit.
8. Monitor Grafana for 10 minutes; confirm the incident metrics (error rate, latency) are recovering toward normal baseline.
9. Post in #customer-portal-incidents: "Hotfix deployed. Monitoring recovery. Metrics: [current error rate / latency]."
10. After 10 minutes of stable metrics, update the incident ticket and the hotfix ticket with deployment evidence.

## Validation

- ArgoCD shows all portal pods running the hotfix SHA with no restarts
- The specific error or behavior that triggered the incident is no longer occurring
- Error rate is recovering toward pre-incident baseline
- No new alerts have fired in the 10 minutes since hotfix deployment

## Rollback

1. Post in #customer-portal-incidents: "Hotfix not effective / making incident worse. ROLLING BACK to [PREVIOUS-SHA]."
2. In ArgoCD, revert the image tag to the previous stable SHA and sync.
3. Wait for all pods to return to healthy status on the previous version.
4. Confirm incident metrics are no longer worsening and post status in #customer-portal-incidents.
5. Escalate to Engineering Manager and reconvene the incident bridge to identify an alternative remediation path.
