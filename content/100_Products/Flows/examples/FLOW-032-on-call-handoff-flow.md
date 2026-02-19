---
id: FLOW-032
type: flow
title: On-Call Handoff Flow
status: approved
owner: QA Engineer
created: '2024-12-30T07:02:14.288Z'
updated: '2026-12-21T11:45:46.295Z'
tags:
  - flow
  - monitoring-stack
summary: On-Call Handoff Flow
feature_area: Monitoring Stack
related_prds:
  - PRD-038
example: true
---

## Steps

### Step 1: Pre-Handoff Preparation (Outgoing Engineer)

The outgoing on-call engineer prepares a handoff document 1 hour before the end of their shift. The document captures: any active or recently resolved incidents (with postmortem links if applicable), any open follow-up items from the shift (pending action items, monitoring issues not yet resolved), the current state of all monitoring-stack services (any degraded components, elevated error rates, or unusual patterns worth watching), and any scheduled deployments or maintenance windows in the next 24 hours.

The document is posted to the team's on-call Slack channel as a pinned message. For shifts where incidents were active, the outgoing engineer schedules a synchronous 15-minute handoff call with the incoming engineer rather than relying on the written handoff alone.

### Step 2: Handoff Communication and Knowledge Transfer

The outgoing engineer sends a Slack message to the incoming engineer in the on-call channel: tagging them, linking the handoff document, and summarizing the top 2-3 things to watch. For complex ongoing situations, a 15-minute video call is conducted to walk through the active state together.

During the handoff call (if held), the outgoing engineer shares their screen and walks through: the current Grafana monitoring overview dashboard, any active AlertManager silences and when they expire, any anomaly detection advisory alerts from the [[PRD-038|Automated Anomaly Detection]] system that have been firing, and any services that behaved unusually during the shift even if no formal alert fired.

### Step 3: PagerDuty Schedule Transition

The on-call management platform (PRD-039) automatically transitions the PagerDuty on-call schedule to the incoming engineer at the scheduled handoff time. No manual action is required for this step — PagerDuty will route all new pages to the incoming engineer from the handoff time forward.

The incoming engineer confirms they are receiving PagerDuty notifications by checking the PagerDuty mobile app and verifying their contact methods are active. If the scheduled handoff is a shift swap (override), the incoming engineer confirms the override is correctly reflected in PagerDuty before the outgoing engineer goes off-call.

### Step 4: Incoming Engineer Orientation

The incoming engineer reviews the handoff document and verifies the current state against the described situation. They open the monitoring overview dashboard and confirm their understanding of any elevated or unusual states. If anything in the handoff document is unclear, they ask the outgoing engineer for clarification immediately while they are still available.

The incoming engineer posts a brief acknowledgement to the on-call Slack channel confirming they have reviewed the handoff and are ready. This acknowledgement is recorded by the on-call management platform to confirm successful handoff. The outgoing engineer is then fully off-call and can stop monitoring alerts.

## Expected Results

- Handoff document completed and posted 1 hour before shift end
- Incoming engineer confirms handoff receipt and readiness before outgoing engineer goes off-call
- Zero alert gaps between shifts (PagerDuty transition is automatic)
- Active incidents have explicit continuity — incoming engineer knows current status and next steps
- Handoff acknowledged and recorded in on-call management platform

## User Info

| Field | Value |
|-------|-------|
| Role | Outgoing on-call engineer (primary), incoming on-call engineer |
| Permissions | Grafana (read), AlertManager API (read silences), PagerDuty (verify schedule) |
| Handoff channel | Slack `#on-call-monitoring` |
| Environment | Production |
| Async escalation | If incoming engineer doesn't confirm within 30 minutes, tech lead is automatically notified |
