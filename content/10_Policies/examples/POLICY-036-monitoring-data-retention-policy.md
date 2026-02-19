---
id: POLICY-036
type: policy
title: Monitoring Data Retention Policy
status: approved
owner: VP Engineering
created: '2025-11-25T15:03:31.143Z'
updated: '2025-03-20T14:39:10.936Z'
tags:
  - policy
  - monitoring-stack
summary: Monitoring Data Retention Policy
example: true
related_standards:
  - STANDARD-043
  - STANDARD-047
---

## Scope

This policy applies to all monitoring data collected and stored by the engineering organization, including metrics, logs, traces, and alerting records. It covers data produced by all production services, infrastructure components, and monitoring platform systems such as Prometheus, Grafana, and Jaeger.

All engineering teams, platform operators, and automated systems that generate or consume monitoring data are subject to this policy.

## Rationale

- Retaining monitoring data for appropriate durations is essential for incident investigation and root cause analysis
- Regulatory and compliance requirements may mandate minimum retention periods for operational logs
- Uncontrolled growth of monitoring data leads to excessive storage costs and degraded query performance
- Consistent retention policies prevent accidental deletion of data needed for active investigations
- Standardized retention schedules enable capacity planning for monitoring storage infrastructure

## Policy Statements

- High-resolution metrics (raw scrape data) must be retained for a minimum of 15 days
- Downsampled metrics (5-minute resolution) must be retained for a minimum of 90 days
- Long-term metrics aggregates (1-hour resolution) must be retained for a minimum of 13 months
- Structured application logs must be retained for a minimum of 30 days in hot storage and 12 months in cold/archive storage
- Distributed traces must be retained for a minimum of 7 days; sampled traces for significant events for 90 days
- Alerting records and PagerDuty incident history must be retained for a minimum of 24 months
- Data retention configurations must be reviewed semi-annually and aligned with [[STANDARD-043|Metric Naming Convention Standard]] and [[STANDARD-047|Dashboard Design Standard]]
- Monitoring data containing personal information must follow data classification guidelines and may require shorter retention periods

## Related Standards

- [[STANDARD-043|Metric Naming Convention Standard]]
- [[STANDARD-047|Dashboard Design Standard]]
