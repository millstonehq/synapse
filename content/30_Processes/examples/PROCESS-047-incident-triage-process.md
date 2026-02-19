---
id: PROCESS-047
type: process
title: Incident Triage Process
status: review
owner: Engineering Manager
created: '2024-03-26T02:11:58.420Z'
updated: '2025-07-16T14:27:29.866Z'
tags:
  - process
  - monitoring-stack
summary: Incident Triage Process
related_standards:
  - STANDARD-045
  - STANDARD-048
related_sops:
  - SOP-079
  - SOP-071
related_systems:
  - SYSTEM-039
example: true
---

## Purpose

This process defines how the monitoring team triages incoming incidents fired by the monitoring stack. Rapid, consistent triage ensures that incidents are correctly classified by severity, routed to the right team, and tracked from first alert to resolution.

Effective triage prevents both under-response (ignoring serious incidents) and over-response (treating minor blips as critical outages), reducing wasted engineering effort and minimizing customer impact.

## Scope

- All production incidents triggered by the monitoring stack via PagerDuty
- Incidents escalated manually by engineers who observe anomalies not yet caught by alerts
- Cross-team incidents requiring coordination between service owners and the platform monitoring team

## Roles and Responsibilities

- **On-Call Engineer**: First responder; acknowledges the alert, performs initial diagnosis, and assigns severity
- **Incident Commander**: Takes over coordination for P1 incidents; ensures communication cadence is maintained
- **Platform Engineer**: Provides monitoring stack support (trace queries, log searches, metric deep-dives) during the triage investigation
- **Engineering Manager**: Notified for P1 incidents; authorizes customer communication and escalation to external vendors

## Triggers

- A PagerDuty alert fires and is acknowledged by the on-call engineer
- An engineer manually raises an incident after observing anomalous behavior in dashboards or logs
- A customer reports a service degradation that has not yet triggered automated alerts

## Inputs

- Active PagerDuty alert with service name, alert name, and firing timestamp
- Relevant Grafana dashboard showing the affected service's golden signals
- Recent deployment history from the deployments channel
- Trace samples from Jaeger for the affected service

## Outputs

- Classified incident with severity (P1/P2/P3), affected services, and estimated customer impact
- Initial assessment posted in the incident channel within 10 minutes of acknowledgement
- Incident ticket created in the incident tracking system
- Escalation triggered per the Alert Escalation Policy if resolution is not achieved within SLA

## Steps

1. On-Call Engineer acknowledges the PagerDuty alert and posts in the incident channel: service name, alert name, time fired, and initial assessment
2. On-Call Engineer opens the service's primary Grafana dashboard and checks the four golden signals to assess scope and severity
3. On-Call Engineer checks recent deploy history and correlates the alert onset with any recent changes; if a deploy is suspected, severity is immediately set to P1 pending confirmation
4. On-Call Engineer assigns a severity level: P1 (customer-facing outage or SLO breach), P2 (degradation, no outage), P3 (internal only, no customer impact)
5. For P1 incidents, On-Call Engineer pages the Incident Commander and notifies the Engineering Manager per [[SOP-071|Respond to PagerDuty Alert SOP]]
6. Incident Commander opens an incident channel and war-room call; assigns roles (scribe, comms lead, technical lead)
7. Platform Engineer queries distributed traces via Jaeger per [[STANDARD-045|Distributed Tracing Standard]] to identify root service and failing span
8. Team works the remediation steps per the relevant runbook; Incident Commander provides status updates every 15 minutes until resolved

## Controls

- All P1 incidents must have an Incident Commander assigned within 5 minutes of severity classification
- Severity classification must be documented in the incident ticket before remediation begins
- The incident channel must not be archived until the post-incident review is complete
- SLO impact calculations must use the SLI methodology defined in [[STANDARD-048|SLI/SLO Definition Standard]]
