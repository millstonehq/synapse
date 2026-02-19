---
id: CAPABILITY-023
type: capability
title: Incident Detection Capability
status: review
owner: VP Engineering
created: '2024-09-20T20:10:28.807Z'
updated: '2025-09-30T10:48:17.298Z'
tags:
  - capability
  - monitoring-stack
summary: Incident Detection Capability
evidence_links:
  - STANDARD-045
  - POLICY-038
  - STANDARD-044
example: true
---

## Domain

- Incident detection is the capability to identify production issues automatically and reliably before customers notice or before business impact becomes significant.
- This capability encompasses alert rule quality, anomaly detection coverage, synthetic monitoring, and the tooling that surfaces signals to on-call engineers.
- The maturity of this capability is measured by mean time to detect (MTTD) and the ratio of incidents detected by automated alerts vs. customer reports or manual observation.

## Maturity (0-5)

- Alert coverage: 4/5 - All critical service metrics have alert rules; burn rate alerting deployed for SLO-bearing services per [[STANDARD-045|STANDARD-045]]; coverage gap is log-based alerts (only 50% of services)
- Detection speed: 3/5 - MTTD of 8.4 minutes for SEV-1; target is < 3 minutes; delay caused by long evaluation windows on some alert rules
- Automated vs. manual detection: 3/5 - 78% of SEV-1/2 incidents are detected by automated alerts; 22% are detected via customer reports or manual observation
- Anomaly detection: 1/5 - No production anomaly detection in place; rely entirely on threshold-based alerting

## Metrics

- Mean time to detect (MTTD) SEV-1: 8.4 minutes (target: < 3 minutes)
- Automated detection rate (SEV-1/2): 78% (target: 95%)
- Alert coverage for on-call services: 100% have threshold alerts; 60% have burn rate alerts; 0% have anomaly detection
- False positive rate: 12% (target: < 5%), measured per [[STANDARD-044|Alert Quality Standard]]

## Evidence Links

- [[STANDARD-045|Monitoring Coverage Standard]] - Defines required alert coverage levels per service tier
- [[POLICY-038|Incident Detection Policy]] - Policy requiring automated detection capability for all production services
- [[STANDARD-044|Alert Quality Standard]] - Defines false positive rate targets and review requirements

## Notes

- The 22% of incidents detected via customer reports represents the most critical gap. These incidents fail the fundamental requirement of automated detection. Root causes: missing alert rules for some failure modes, and evaluation windows that are too long to catch fast-developing failures.
- Anomaly detection (maturity level 1) is the next major investment area. The PRD-038 product initiative, if delivered, would advance this sub-capability from 1/5 to 3/5.
