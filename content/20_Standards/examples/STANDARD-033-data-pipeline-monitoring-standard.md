---
id: STANDARD-033
type: standard
title: Data Pipeline Monitoring Standard
status: draft
owner: Head of Engineering
created: '2024-12-17T10:59:57.215Z'
updated: '2025-03-27T16:12:09.780Z'
tags:
  - standard
  - data-pipeline
summary: Data Pipeline Monitoring Standard
related_policies:
  - POLICY-029
  - POLICY-030
example: true
related_systems:
  - SYSTEM-029
  - SYSTEM-026
---

## Area

This standard defines the minimum observability requirements for all production data pipelines, including metrics, alerting, logging, and dashboard coverage. It applies to batch pipelines, streaming pipelines, Kafka consumers, and data quality checks.

## Controls

- Every production pipeline must emit task-level duration, record count, and error count metrics to the central metrics store
- Kafka consumer groups must expose consumer lag metrics; lag exceeding 10,000 messages for more than 5 minutes must trigger an alert
- Pipeline failure alerts must route to PagerDuty with P2 severity or higher
- Data quality gate failures must be logged with the failing check name, threshold, and observed value
- Pipelines processing SLA-bound data must have end-to-end latency dashboards with threshold annotations
- Log retention for pipeline execution logs must be a minimum of 30 days

## Compliance Mappings

- SOC 2: CC7.2 (Monitoring of system components)
- NIST SP 800-53: AU-12 (Audit Record Generation)

## Related Policies

- [[POLICY-029|PII Masking in Pipelines Policy]]
- [[POLICY-030|Data Pipeline Change Management Policy]]
