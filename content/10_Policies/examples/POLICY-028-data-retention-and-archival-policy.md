---
id: POLICY-028
type: policy
title: Data Retention and Archival Policy
status: approved
owner: CTO
created: '2025-09-10T19:03:51.962Z'
updated: '2025-07-14T04:27:10.551Z'
tags:
  - policy
  - data-pipeline
summary: Data Retention and Archival Policy
example: true
related_standards:
  - STANDARD-032
  - STANDARD-036
---

## Scope

This policy applies to all data assets produced, processed, or stored within the organization's data pipeline infrastructure, including raw ingestion data, intermediate transformation outputs, and published datasets in the data lake, data warehouse, and message broker topics. It covers all storage tiers: hot (operational), warm (analytical), and cold (archival).

## Rationale

- Retaining data beyond business necessity increases storage costs and regulatory exposure
- Deletion obligations under GDPR and CCPA require enforceable data lifecycle controls
- Unmanaged data growth degrades pipeline performance and increases infrastructure spend
- Archival policies enable cost optimization by tiering infrequently accessed data to cheaper storage

## Policy Statements

- Raw ingestion data must be retained for a minimum of 90 days and a maximum of 2 years unless subject to a legal hold
- Transformed and aggregated datasets must define a retention period in their catalog metadata entry before promotion to production
- Data containing PII must be purged or anonymized within the retention window mandated by applicable data protection regulation
- Archival to cold storage must be automated via lifecycle policies; manual archival is not permitted for datasets exceeding 1 TB
- Kafka topic retention must not exceed 7 days for operational topics without explicit data governance approval
- Retention schedules must be reviewed annually and updated following regulatory changes

## Related Standards

- [[STANDARD-032|Event Schema Registry Standard]]
- [[STANDARD-036|Data Catalog Metadata Standard]]
