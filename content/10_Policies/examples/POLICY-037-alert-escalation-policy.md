---
id: POLICY-037
type: policy
title: Alert Escalation Policy
status: approved
owner: VP Engineering
created: '2024-09-21T22:33:54.554Z'
updated: '2025-08-18T17:00:05.525Z'
tags:
  - policy
  - monitoring-stack
summary: Alert Escalation Policy
example: true
related_standards:
  - STANDARD-048
  - STANDARD-047
---

## Scope

This policy governs how alerts fired by the monitoring stack are acknowledged, triaged, and escalated. It applies to all production alerts routed through AlertManager and PagerDuty, and covers all engineering teams participating in on-call rotations.

Engineers, team leads, and engineering managers responsible for on-call duties are required to follow this escalation policy. Automated runbooks and alerting integrations must also conform to these escalation timelines.

## Rationale

- Unclear escalation paths cause delays in incident response, increasing customer impact
- Consistent escalation timelines ensure that no alert is silently ignored or left unacknowledged
- Documented escalation policies reduce on-call stress by providing clear expectations for when to involve additional responders
- Escalation records provide audit evidence required for SLA compliance and post-incident review

## Policy Statements

- All critical (P1) alerts must be acknowledged within 5 minutes of firing; failure to acknowledge triggers automatic escalation
- All high (P2) alerts must be acknowledged within 15 minutes of firing
- On-call engineers must post an initial assessment in the designated incident channel within 10 minutes of acknowledging a P1 alert
- Unresolved P1 incidents must be escalated to the team lead at 15 minutes and to the engineering manager at 30 minutes
- No alert may be silenced for more than 4 hours without a corresponding incident or maintenance ticket
- Alert routing rules must be reviewed quarterly and aligned with [[STANDARD-048|SLI/SLO Definition Standard]] and [[STANDARD-047|Dashboard Design Standard]]
- All escalation events must be recorded in the incident management system for post-incident review

## Related Standards

- [[STANDARD-048|SLI/SLO Definition Standard]]
- [[STANDARD-047|Dashboard Design Standard]]
