---
id: SOP-072
type: sop
title: Silence Noisy Alert SOP
status: review
owner: Release Manager
created: '2025-07-09T09:19:45.846Z'
updated: '2025-09-23T07:39:46.925Z'
tags:
  - sop
  - monitoring-stack
summary: Silence Noisy Alert SOP
related_process: PROCESS-068
related_systems:
  - SYSTEM-036
example: true
---

## Preconditions

- The alert has fired multiple times in the last hour without corresponding true incidents
- You have investigated the alert and confirmed it is a false positive or a known transient condition
- You have notified the team lead or engineering manager that you intend to silence the alert
- You have an open ticket tracking the root cause of the alert's noisiness for follow-up

## Materials/Access

- AlertManager web UI or CLI access with write permissions
- The exact alert name and label set (e.g., `{service="api", env="prod"}`) to be silenced
- Incident tracking system to create the follow-up ticket
- Slack access to post in #monitoring-alerts channel

## Procedure

1. Confirm the alert is genuinely noisy and not masking a real problem. Check the service dashboard and error logs before proceeding. Never silence an alert without this check.
2. Open the AlertManager web UI (or use `amtool silence add`) and create a new silence for the specific alert name and label set. Do not use wildcards that would silence other alerts.
3. Set the silence duration to the minimum necessary — maximum 4 hours for unplanned silences. Longer silences require Engineering Manager approval.
4. Add a comment on the silence that includes: your name, the reason for silencing, and the ticket number tracking the root cause fix.
5. Create a follow-up ticket in the incident tracking system titled "Fix noisy alert: [alert name]" and assign it to yourself or the service owner. Set priority based on alert severity.
6. Post in #monitoring-alerts channel: the alert name, silence duration, reason, and the follow-up ticket link.
7. Set a personal reminder for 30 minutes before the silence expires to confirm whether the underlying issue has been resolved.
8. When the silence expires, evaluate whether the alert is still noisy. If yes, either apply the fix or request an extension with Engineering Manager approval.

## Validation

- The alert no longer fires in AlertManager during the silence window
- The silence entry in AlertManager shows your name, comment, and expiry time
- A follow-up ticket is open and assigned for the root cause fix
- The silence event is logged in the #monitoring-alerts channel

## Rollback

1. If the silenced condition turns out to be a real incident, expire the silence immediately in AlertManager.
2. Re-acknowledge the alert in PagerDuty if it re-fires after silence expiry.
3. Post in the incident channel that the silence was premature and the issue is now being treated as an active incident.
4. Escalate to team lead if the situation warrants P1 response.
