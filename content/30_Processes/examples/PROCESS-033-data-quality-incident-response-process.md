---
id: PROCESS-033
type: process
title: Data Quality Incident Response Process
status: approved
owner: Engineering Manager
created: '2024-10-18T00:37:25.175Z'
updated: '2026-09-14T08:08:11.677Z'
tags:
  - process
  - data-pipeline
summary: Data Quality Incident Response Process
related_standards:
  - STANDARD-031
  - STANDARD-033
related_sops:
  - SOP-051
  - SOP-057
related_systems:
  - SYSTEM-028
example: true
---

## Purpose

This process defines how the data engineering team responds to data quality incidents — situations where data published to downstream consumers does not meet the expected quality thresholds. It ensures timely containment, root cause identification, and remediation to minimize downstream impact.

## Scope

- Data quality gate failures in production pipelines that result in bad data reaching consumers
- Upstream source data anomalies that invalidate a dataset partition
- Schema compatibility failures that cause consumer deserialization errors
- Silent data corruption discovered through anomaly detection or consumer reports

## Roles and Responsibilities

- **On-Call Data Engineer**: First responder; triages the alert, contains the blast radius, and initiates the response
- **Pipeline Owner**: Subject matter expert on the affected pipeline; leads root cause investigation
- **Downstream Consumer Contacts**: Notified of impact; confirm which reports or products are affected
- **Data Governance**: Notified for incidents involving PII or regulated data

## Triggers

- Automated data quality alert fires for a production pipeline
- A consumer team reports receiving incorrect or missing data
- Anomaly detection identifies an unusual pattern in published datasets
- Pipeline monitoring detects a schema deserialization error rate spike

## Inputs

- Quality alert details: pipeline name, check name, failing threshold, and observed value
- Recent pipeline run logs and task execution history
- Data catalog entry for the affected dataset

## Outputs

- Incident ticket with timeline, root cause, and remediation steps
- Corrected data reprocessed and published to consumers
- Updated quality gate thresholds or pipeline logic to prevent recurrence
- Post-incident review completed within 5 business days for P1/P2 incidents

## Steps

1. On-Call Data Engineer acknowledges the alert and assesses impact — which consumers received bad data and for which time window
2. On-Call Data Engineer notifies affected downstream consumer contacts and posts incident status in #data-incidents
3. On-Call Data Engineer halts further propagation by pausing downstream pipeline stages or flagging the affected partition
4. Pipeline Owner investigates root cause: review pipeline logs, recent schema changes, and upstream source diffs
5. Pipeline Owner implements the fix (code change, schema correction, or data re-ingestion) and deploys to staging for validation
6. On-Call Data Engineer approves the fix and triggers a backfill to reprocess the affected time window
7. On-Call Data Engineer confirms corrected data reaches consumers and lifts the propagation hold
8. Pipeline Owner opens a post-incident review ticket and updates quality gate thresholds to prevent recurrence

## Controls

- Affected downstream partitions must be flagged as suspect within 30 minutes of incident acknowledgment
- Incidents involving PII data quality failures must notify Data Governance within 2 hours
- All data quality incidents must be tracked in the incident management system with full timeline
- Backfill operations must use the idempotent write path to prevent duplication
