---
id: FLOW-030
type: flow
title: Incident Response Flow
status: approved
owner: QA Lead
created: '2025-05-24T04:56:19.241Z'
updated: '2026-03-22T01:26:26.734Z'
tags:
  - flow
  - monitoring-stack
summary: Incident Response Flow
feature_area: Monitoring Stack
related_prds:
  - PRD-038
example: true
---

## Steps

### Step 1: Incident Detection

An incident is detected via one of three paths: (a) automated alert from AlertManager reaching the on-call engineer via PagerDuty, (b) anomaly detection advisory alert from the [[PRD-038|Automated Anomaly Detection]] system surfaced in Slack, or (c) manual report from an engineer or customer. All three paths converge at incident declaration.

The on-call engineer declares an incident by creating an incident record in the monitoring platform. The incident record captures: severity (SEV-1 through SEV-3), affected services, initial symptom description, and time of detection. A dedicated Slack channel is created automatically (`#incident-{date}-{short-description}`) and all subsequent coordination happens there.

### Step 2: Severity Assessment and Mobilization

The on-call engineer assesses severity within 5 minutes of detection using the defined severity criteria: SEV-1 = production impact affecting customers or SLO breach in progress; SEV-2 = significant degradation but no customer impact yet; SEV-3 = minor degradation or impending issue.

For SEV-1: Incident commander role is assigned (default: on-call engineer until tech lead joins). Engineering manager is notified. Status page is updated immediately. For SEV-2: Tech lead is looped in but not paged until 15 minutes without resolution. For SEV-3: On-call engineer handles autonomously; escalates if no resolution in 30 minutes.

### Step 3: Investigation and Mitigation

The incident commander coordinates investigation using the affected service's Grafana dashboard and runbook. Investigation is timeboxed: at 15 minutes, if root cause is unknown, the incident commander calls for help rather than continuing to diagnose alone. The goal at this phase is mitigation (restore service) before root cause (understand why).

Common mitigations: rollback a recent deployment, scale up replicas, kill a long-running database query, activate a circuit breaker, or enable a maintenance page. Once a mitigation is identified, it is executed immediately. Recovery is confirmed when metrics return to baseline and alerts resolve in AlertManager.

### Step 4: Communication and Closure

For SEV-1 and SEV-2, the status page is updated at 15-minute intervals during the incident. A final update is posted when the incident is resolved, including a brief description of what happened and what was done.

The incident is closed in the monitoring platform when all of: (a) root cause is identified, (b) mitigation is in place and stable for 15 minutes, and (c) status page shows operational for all affected services. A postmortem is required for SEV-1 and SEV-2. The postmortem must be published within 5 business days.

## Expected Results

- Incident declared within 5 minutes of detection for automated alerts
- Customer-facing status page updated within 10 minutes of SEV-1 declaration
- Severity correctly classified and appropriate stakeholders mobilized
- Mitigation applied within MTTR targets (SEV-1: < 30 minutes, SEV-2: < 1 hour)
- Postmortem published for SEV-1 and SEV-2 within 5 business days

## User Info

| Field | Value |
|-------|-------|
| Role | On-call engineer, incident commander, tech lead |
| Permissions | Monitoring platform (create/update incidents), AlertManager (silence), Status Page (update) |
| Test account | incident-drill@example.com |
| Environment | Production |
| Coordination channel | Slack `#incident-{date}-{description}` (auto-created) |
