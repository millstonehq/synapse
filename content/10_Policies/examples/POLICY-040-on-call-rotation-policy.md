---
id: POLICY-040
type: policy
title: On-Call Rotation Policy
status: draft
owner: CISO
created: '2024-07-22T06:47:48.933Z'
updated: '2026-03-31T11:04:34.581Z'
tags:
  - policy
  - monitoring-stack
summary: On-Call Rotation Policy
example: true
related_standards:
  - STANDARD-045
  - STANDARD-043
---

## Scope

This policy governs how on-call rotations are structured and staffed across all engineering teams responsible for production services. It applies to all engineers who participate in on-call duties, their managers, and the platform team that maintains the PagerDuty scheduling and escalation configuration.

On-call coverage is required for all production services that have customer-facing SLOs or that are dependencies of such services.

## Rationale

- Unstructured on-call coverage leads to burnout and causes engineers to ignore alerts
- Clear rotation policies ensure every on-call shift has a primary and backup responder
- Documented expectations reduce ambiguity about what engineers are responsible for during their on-call week
- Fair rotation design is necessary to maintain sustainable engineering team health
- Regular rotation reviews enable improvement of alert quality and runbook coverage

## Policy Statements

- Every production service must have a designated primary on-call engineer and a backup at all times
- On-call shifts must not exceed one week per rotation cycle; longer shifts require VP Engineering approval
- Engineers must not be scheduled on-call more than once every four weeks unless they volunteer
- New engineers must shadow an experienced on-call engineer for at least one full rotation before taking primary shifts
- On-call engineers must be reachable via PagerDuty and respond within the timeframes defined in the Alert Escalation Policy
- Runbooks must exist for all P1 and P2 alerts before a service may be added to a production on-call rotation
- Teams must conduct a monthly on-call retrospective to review alert volume, response times, and runbook quality
- Metrics and traces referenced in on-call runbooks must conform to [[STANDARD-045|Distributed Tracing Standard]] and [[STANDARD-043|Metric Naming Convention Standard]]

## Related Standards

- [[STANDARD-045|Distributed Tracing Standard]]
- [[STANDARD-043|Metric Naming Convention Standard]]
