---
id: SOP-051
type: sop
title: Restart Failed Airflow DAG SOP
status: review
owner: DevOps Lead
created: '2024-01-03T07:07:45.104Z'
updated: '2025-07-28T15:05:04.050Z'
tags:
  - sop
  - data-pipeline
summary: Restart Failed Airflow DAG SOP
related_process: PROCESS-066
related_systems:
  - SYSTEM-026
example: true
---

## Preconditions

- You have identified which DAG and which task instance failed (DAG ID, run ID, and task ID are known)
- The root cause of the failure has been assessed — do not restart if the root cause is still active
- Access to the Airflow web UI or CLI is confirmed
- The data for the affected time partition is available and valid in the source system
- Downstream consumers of this DAG's output have been notified if delay exceeds SLA

## Materials/Access

- Airflow web UI access or `airflow` CLI on the scheduler host
- Read access to pipeline execution logs (Airflow logs or S3 log bucket)
- Access to #data-incidents Slack channel
- Grafana dashboard for the affected pipeline

## Procedure

1. Open the Airflow web UI, navigate to DAGs, and locate the failed DAG run by run ID and execution date.
2. Click on the failed task instance and review the task logs to confirm the failure reason before proceeding.
3. Verify the underlying cause is resolved (e.g., source data restored, upstream dependency succeeded, transient error cleared).
4. If only a specific task failed and upstream tasks succeeded, right-click the failed task and select "Clear" to reset it for retry.
5. If the entire DAG run must be restarted, click "Clear" on the DAG run row to reset all tasks from the beginning.
6. Monitor the restarted task or DAG run in the UI; confirm task status transitions from "queued" to "running" within 2 minutes.
7. Watch the task log in real-time or refresh every 2 minutes until the task reaches "success" status.
8. Verify the DAG's downstream tasks complete successfully and the final output dataset is populated correctly.
9. Post in #data-incidents: "DAG [dag_id] run [run_id] restarted and completed successfully. Execution date: [date]."

## Validation

- The restarted task shows "success" status in the Airflow UI
- The output dataset or downstream artifact reflects the expected record count for the execution date
- No duplicate records exist in the target table (confirm via idempotency check query)
- All downstream tasks dependent on this DAG run have also completed successfully

## Rollback

1. If the restarted DAG produces incorrect output, pause the DAG in the Airflow UI to prevent further runs.
2. Delete or overwrite the incorrect output partition in the target storage using the standard idempotent write procedure.
3. Notify downstream consumers that the published data for the affected partition is being corrected.
4. Escalate to the Pipeline Owner to investigate the root cause before authorizing a second restart attempt.
5. Open an incident ticket documenting the failed restart, the incorrect data window, and the corrective action taken.
