---
id: SOP-055
type: sop
title: Investigate Data Quality Alert SOP
status: proposed
owner: Release Manager
created: '2024-09-25T20:23:38.280Z'
updated: '2025-07-19T21:51:48.701Z'
tags:
  - sop
  - data-pipeline
summary: Investigate Data Quality Alert SOP
related_process: PROCESS-034
related_systems:
  - SYSTEM-028
example: true
---

## Preconditions

- A data quality alert has fired and been acknowledged in PagerDuty or the alerting system
- The alert details are available: pipeline name, check name, threshold, observed value, and execution timestamp
- Access to pipeline execution logs and the data catalog entry for the affected dataset is confirmed

## Materials/Access

- Grafana data quality monitoring dashboard
- Access to Airflow or Dagster UI for pipeline run history
- Read access to the target data lake bucket or warehouse table
- Access to #data-incidents Slack channel

## Procedure

1. Acknowledge the alert and post in #data-incidents: "Investigating data quality alert on [pipeline] - [check_name]. Observed: [value], threshold: [threshold]."
2. Open the Grafana data quality dashboard and identify which specific check failed (completeness, uniqueness, schema, or referential integrity).
3. Identify the affected execution date and time window; check whether previous runs for adjacent dates also show failures or if this is isolated.
4. Pull the pipeline execution log for the failing run and look for upstream errors, schema mismatches, or source data anomalies.
5. Query the target dataset partition directly to verify the observed anomaly (e.g., count nulls in the failing column, check for duplicates on the primary key).
6. Check the source system or upstream pipeline output for the same time window to determine if the issue originates upstream or in the transformation logic.
7. Classify the root cause: (a) source data issue, (b) pipeline logic bug, (c) schema change, or (d) infrastructure transient failure.
8. Based on classification: for transient failures, clear and re-run the task; for data issues, escalate to the Pipeline Owner and halt downstream propagation.
9. Post updated status in #data-incidents with root cause classification and next steps.

## Validation

- The failing quality check passes on re-execution or the affected partition is halted from downstream propagation
- Downstream consumers are confirmed to not have received the bad data partition
- The incident ticket is updated with root cause, impact window, and resolution status

## Rollback

1. If bad data has already propagated to consumers, flag the affected dataset partition as invalid in the catalog.
2. Notify all downstream consumer teams of the affected partition and time window.
3. Delete or overwrite the bad data partition using the idempotent write procedure after the root cause is fixed.
4. Trigger a re-run of the corrected pipeline for the affected time window.
5. Confirm corrected data is received by consumers and close the incident ticket with a full timeline.
