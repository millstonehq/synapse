---
id: POLICY-038
type: policy
title: SLO Definition Policy
status: approved
owner: VP Engineering
created: '2025-06-18T04:36:36.544Z'
updated: '2025-08-11T11:57:52.576Z'
tags:
  - policy
  - monitoring-stack
summary: SLO Definition Policy
example: true
related_standards:
  - STANDARD-044
  - STANDARD-046
---

## Scope

This policy applies to all production services owned by engineering teams. Every service that serves internal or external customers must have at least one defined Service Level Objective (SLO). SLOs must be documented, tracked via SLIs in the monitoring platform, and reviewed on a regular cadence.

Product managers, engineering leads, and service owners are responsible for defining and maintaining SLOs for their services.

## Rationale

- Without defined SLOs, teams lack an objective basis for prioritizing reliability work versus feature development
- SLOs provide a shared language between engineering and product for discussing acceptable service quality
- Undefined service reliability expectations lead to inconsistent on-call response and customer trust erosion
- SLOs tied to error budgets enable data-driven decisions about when to slow down feature development for reliability work

## Policy Statements

- Every production service must have at least one SLO defined and tracked in the monitoring platform
- SLOs must be based on measurable SLIs as defined in [[STANDARD-044|Structured Logging Standard]] and [[STANDARD-046|Alert Definition Standard]]
- SLOs must be reviewed and confirmed or updated at minimum on a quarterly basis
- New services must have SLOs defined and approved before entering production
- SLO targets must include an error budget calculation and a documented policy for error budget exhaustion
- SLO breach notifications must be routed through AlertManager and linked to runbooks
- Teams must publish SLO compliance reports monthly to engineering leadership
- SLO definitions must be version-controlled and reviewed as part of the change management process

## Related Standards

- [[STANDARD-044|Structured Logging Standard]]
- [[STANDARD-046|Alert Definition Standard]]
