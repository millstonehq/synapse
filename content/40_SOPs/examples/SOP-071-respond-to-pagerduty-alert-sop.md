---
id: SOP-071
type: sop
title: Respond to PagerDuty Alert SOP
status: accepted
owner: DevOps Lead
created: '2024-08-28T06:36:01.657Z'
updated: '2026-11-10T23:52:13.973Z'
tags:
  - sop
  - monitoring-stack
summary: Respond to PagerDuty Alert SOP
related_process: PROCESS-047
related_systems:
  - SYSTEM-037
example: true
---

## Preconditions

- You have received a PagerDuty notification and the alert is in a firing state
- You have access to Grafana, the log aggregation system, and Jaeger
- You know the name of the affected service and have access to its primary overview dashboard
- Your PagerDuty mobile app or notification method is confirmed working
- You are the designated primary on-call engineer for the current shift

## Materials/Access

- PagerDuty account with on-call assignment for the current rotation
- Grafana access with read permissions for all production dashboards
- Log aggregation system access (Kibana or Loki/Grafana Logs) for the affected service
- Jaeger access for querying distributed traces
- Incident channel access (#incidents or service-specific channel)
- Runbook for the specific alert (link is in the PagerDuty alert description)

## Procedure

1. Acknowledge the PagerDuty alert immediately. This stops escalation to backup. Do not let it go past 5 minutes without acknowledgement.
2. Open the alert's runbook URL from the PagerDuty alert description. If no runbook URL is present, search the runbook directory by alert name.
3. Post in the incident Slack channel: service name, alert name, time fired, and "investigating." This keeps the team informed even if you resolve quickly.
4. Open the service's primary Grafana overview dashboard and note the current values for: request rate, error rate, P95 latency, and saturation metrics.
5. Check the deployments channel for any changes to the affected service in the last 2 hours. A recent deploy is the most common cause.
6. Follow the diagnosis steps in the runbook for this specific alert, working through them in order.
7. Apply the appropriate remediation steps from the runbook. If no runbook exists for this alert, escalate to the team lead immediately rather than guessing.
8. Once the alert resolves, verify that all four golden signals have returned to baseline on the dashboard, then post resolution in the incident channel with root cause and time-to-resolve.
9. Resolve the PagerDuty incident and close with a brief resolution note describing what was done.

## Validation

- The PagerDuty alert has transitioned to resolved state
- All four golden signals on the service dashboard show values within normal range
- No new related alerts have fired in the 15 minutes following your remediation action
- Resolution message is posted in the incident channel with root cause noted
- If the incident lasted more than 15 minutes, a post-incident ticket has been created

## Rollback

1. If remediation steps made the situation worse, revert any configuration or deployment changes immediately before taking further action.
2. Post in the incident channel that rollback is in progress and the reason.
3. Escalate to team lead if the situation has not stabilized within 5 minutes of the rollback action.
4. If escalation is required, ensure the incident channel has a complete timeline of actions taken so the incoming responder can orient quickly.
5. Do not silence or suppress the alert during active investigation unless authorized by the team lead.
