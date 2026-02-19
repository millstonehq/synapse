---
id: FLOW-029
type: flow
title: Alert Escalation Flow
status: review
owner: QA Lead
created: '2024-04-17T10:11:33.689Z'
updated: '2026-06-30T03:10:11.787Z'
tags:
  - flow
  - monitoring-stack
summary: Alert Escalation Flow
feature_area: Monitoring Stack
related_prds:
  - PRD-039
example: true
---

## Steps

### Step 1: Alert Fires and Initial Acknowledgement

AlertManager evaluates a firing alert rule and determines it exceeds the configured threshold for its evaluation window. The alert is routed through the routing tree based on `severity` and `team` labels. For critical severity, an immediate PagerDuty high-urgency page is sent to the on-call engineer on the team's rotation (as managed by the [[PRD-039|On-Call Management Platform]]). For warning severity, a Slack message is posted to the team's alert channel.

The on-call engineer acknowledges the alert within the target MTTA window (5 minutes for critical). Acknowledging in PagerDuty marks the alert as in-progress and stops escalation timers. The engineer posts an initial assessment to the team's incident Slack channel within 5 minutes of acknowledging.

### Step 2: Initial Diagnosis

The engineer uses the service's Grafana dashboard (linked from the alert) to assess the scope of the issue. They check the error rate, latency percentiles, and recent deployment activity. If a deployment in the last 30 minutes correlates with the alert, rollback is the first action regardless of the diagnostic findings.

If no recent deployment, the engineer follows the service-specific runbook diagnosis steps. Diagnosis should take no more than 15 minutes. If the root cause is not identified within 15 minutes, the engineer proceeds directly to escalation rather than continuing to investigate alone.

### Step 3: Escalation Decision

At 15 minutes post-acknowledgement, the engineer evaluates: is the issue resolved or is a clear resolution path identified? If yes, continue to resolution. If no, escalate immediately.

Escalation means paging the service tech lead via the secondary on-call PagerDuty schedule. The tech lead joins the incident Slack channel and takes over coordination. The original on-call engineer remains engaged for diagnostic support. The engineer posts an escalation note explaining what has been diagnosed so far and what was tried.

### Step 4: Resolution and Closure

Once the issue is resolved (error rate back to baseline, alerts resolved in AlertManager), the on-call engineer verifies stability for 15 minutes before closing the incident. A brief incident summary is posted to the team Slack channel: what happened, what was done, and whether a postmortem is required (postmortem required for any SEV-1 or SEV-2, and for any SEV-3 lasting more than 30 minutes).

If a postmortem is required, a postmortem document is created from the template and assigned to the incident commander before the incident is closed.

## Expected Results

- All critical alerts acknowledged within 5 minutes of firing
- Root cause identified or escalation triggered within 15 minutes of acknowledgement
- Resolution time tracked from first alert fire to issue resolved in AlertManager
- Postmortem created for qualifying incidents within 24 hours of resolution
- Alert closed in PagerDuty with resolution notes populated

## User Info

| Field | Value |
|-------|-------|
| Role | On-call engineer (primary), tech lead (escalation) |
| Permissions | AlertManager API (silence, resolve), PagerDuty (acknowledge, escalate), Grafana (read) |
| Test account | oncall-test@example.com (staging only) |
| Environment | Production |
| On-call tool | PagerDuty (primary notification), Slack (coordination) |
