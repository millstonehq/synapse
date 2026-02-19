---
id: CAPABILITY-024
type: capability
title: SLO Management Capability
status: approved
owner: VP Engineering
created: '2024-02-10T14:16:33.425Z'
updated: '2025-08-11T01:12:45.636Z'
tags:
  - capability
  - monitoring-stack
summary: SLO Management Capability
evidence_links:
  - STANDARD-047
  - STANDARD-046
  - POLICY-036
example: true
---

## Domain

- SLO Management is the capability to define, track, and act on Service Level Objectives across all production services.
- It includes SLO definition practices, error budget tracking, burn rate alerting, quarterly reporting, and the organizational processes for making reliability vs. velocity trade-offs using error budget data.
- Maturity at this capability determines whether reliability investments are driven by data or by intuition.

## Maturity (0-5)

- SLO definition coverage: 3/5 - 65% of services with on-call rotations have defined SLOs per [[STANDARD-047|SLO Definition Standard]]; remaining 35% have informal availability targets only
- Error budget tracking: 3/5 - Real-time tracking operational for services with SLOs; manual spreadsheet for the rest; SLO Management Console in development (PRD-037)
- Burn rate alerting: 3/5 - Burn rate alerting deployed for 40% of services; remainder use only threshold alerting
- SLO-driven decision making: 2/5 - Error budget data is available but not consistently used in quarterly planning or deployment decisions; cultural adoption is in progress

## Metrics

- SLO coverage (services with defined SLOs): 65% of on-call services (target: 100%)
- Quarterly SLO compliance review completion rate: 80% (target: 100% per [[STANDARD-046|SLO Reporting Standard]])
- Services with burn rate alerting enabled: 40% (target: 100%)
- SLO breaches that triggered postmortems: 90% (target: 100%)

## Evidence Links

- [[STANDARD-047|SLO Definition Standard]] - Defines how SLOs must be specified (target, window, indicator metric, owner)
- [[STANDARD-046|SLO Reporting Standard]] - Defines quarterly reporting requirements for SLO compliance
- [[POLICY-036|Reliability Policy]] - Policy mandating SLOs for all production services with on-call coverage

## Notes

- The gap from level 3 to level 4 is primarily organizational: SLO data is available but not embedded in sprint planning, deployment decisions, or quarterly OKRs as a first-class input. The SLO Management Console (PRD-037), if adopted, would automate reporting and make error budget data more accessible, which should drive cultural adoption.
- The 35% of services without SLOs are mostly internal tooling and monitoring-stack components that were deprioritized. These will be addressed in Q3 as part of the SLO coverage push.
