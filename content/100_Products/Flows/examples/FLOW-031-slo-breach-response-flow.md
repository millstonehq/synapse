---
id: FLOW-031
type: flow
title: SLO Breach Response Flow
status: draft
owner: QA Lead
created: '2025-08-11T06:50:53.637Z'
updated: '2025-08-08T22:59:01.572Z'
tags:
  - flow
  - monitoring-stack
summary: SLO Breach Response Flow
feature_area: Monitoring Stack
related_prds:
  - PRD-040
example: true
---

## Steps

### Step 1: SLO Burn Rate Alert Triggers

The SLO Tracking Service computes a fast-burn rate (1-hour window consuming > 2% of monthly error budget) and fires a burn rate alert via the Alert Management Service. The alert is routed to the team's Slack channel as a high-priority message (not PagerDuty, unless this is a fast burn during business hours for a customer-facing service).

The on-call engineer acknowledges the burn rate alert and opens the SLO Management Console to view the current error budget state. Key data points: remaining budget percentage, burn rate trend (accelerating/steady/decelerating), and the metric driving the error rate. The engineer also checks whether an incident is already declared for the affected service — if so, the SLO context is added to the active incident record.

### Step 2: Budget Triage and Response Decision

The engineer triages the budget situation using the three-tier framework from the [[PRD-040|Cost-Aware Monitoring Configuration]] context: budget > 50% remaining and burn rate decelerating → monitor (no immediate action); budget 20-50% remaining or burn rate steady at > 1x → investigate and prepare mitigation; budget < 20% remaining or burn rate > 5x → treat as active incident, escalate immediately.

For budget < 20%, the engineer declares a SEV-2 incident immediately and follows the Incident Response Flow. For budget 20-50%, the engineer opens an investigation to identify the error source without declaring a formal incident unless the situation worsens. The investigation uses the service's Grafana SLO dashboard showing error rate breakdown by endpoint, status code, and time.

### Step 3: Root Cause Identification and Mitigation

The engineer identifies the specific error source driving the SLO burn: which endpoint(s) are failing, what error codes are returned, and whether the errors correlate with a recent deployment, dependency degradation, or traffic spike. The SLO dashboard error budget breakdown panel shows the contribution by endpoint.

Once the error source is identified, the engineer applies the appropriate mitigation: rollback if deployment-related, circuit breaker if dependency-related, or rate limiting if traffic-related. If the error source cannot be identified within 20 minutes, the engineer escalates to the tech lead. After mitigation, the engineer monitors burn rate for 30 minutes to confirm it has returned to a sustainable rate (< 1x the monthly allocation pace).

### Step 4: Budget Recovery and Documentation

After the immediate error rate is resolved, the engineer documents the burn event in the SLO Management Console: what caused the burn, how much budget was consumed, and what mitigation was applied. If the breach consumed > 20% of the monthly error budget, a mini-postmortem (abbreviated postmortem with root cause and action items) is required even if no formal incident was declared.

The team reviews their remaining monthly error budget and adjusts planned maintenance windows or risky deployments for the remainder of the month accordingly. If the monthly SLO was breached (budget fully consumed), a full postmortem is required.

## Expected Results

- Burn rate alert acknowledged within 5 minutes of firing
- Budget triage completed and response decision made within 10 minutes
- Error source identified within 20 minutes or escalation triggered
- Mitigation applied and burn rate stabilized within MTTR targets
- Budget consumption documented in SLO Management Console

## User Info

| Field | Value |
|-------|-------|
| Role | On-call engineer, service team lead |
| Permissions | SLO Management Console (read/write), Grafana (read), AlertManager (acknowledge) |
| Key dashboard | SLO Management Console error budget panel for affected service |
| Environment | Production |
| Escalation | Tech lead if budget < 20% or root cause not found in 20 min |
