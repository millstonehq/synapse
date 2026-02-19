---
id: SOP-058
type: sop
title: Clear Stuck Pipeline Task SOP
status: approved
owner: Release Manager
created: '2024-09-21T04:39:59.271Z'
updated: '2026-07-19T05:21:58.002Z'
tags:
  - sop
  - data-pipeline
summary: Clear Stuck Pipeline Task SOP
related_process: PROCESS-035
related_systems:
  - SYSTEM-029
example: true
---

## Preconditions

- A pipeline task has been in "running" or "queued" state for longer than its expected maximum duration
- The task has not self-resolved after the configured retry limit
- You have confirmed that the task is genuinely stuck (not slowly processing a large dataset legitimately)

## Materials/Access

- Access to the pipeline orchestration UI (Airflow or Dagster)
- Access to pipeline task execution logs
- Access to the compute environment where the task is running (Kubernetes pod logs or Spark driver UI)
- Access to #data-incidents Slack channel

## Procedure

1. Identify the stuck task: note the DAG ID, task ID, run ID, and current runtime duration.
2. Check the task execution logs in the orchestration UI for any error messages, resource exhaustion indicators, or hung network calls.
3. If the task is running in Kubernetes, use `kubectl get pods -n data-pipelines` to find the pod and `kubectl logs [pod_name]` to inspect live output.
4. Check for external resource locks: query the target database or storage layer for open transactions or write locks held by the task's process.
5. If the task is waiting on an external dependency (upstream pipeline, API timeout), address the dependency first before killing the task.
6. If the task is confirmed stuck with no progress, mark it as "failed" in the orchestration UI using the "Mark Failed" action — do not use "Clear" as this may trigger unintended retries.
7. If the compute resource (pod or Spark executor) is still running, terminate it: `kubectl delete pod [pod_name] -n data-pipelines`.
8. Investigate the root cause before re-triggering; apply any necessary fixes (timeout configuration, resource limits, upstream fix).
9. Re-trigger the task via "Clear" in the orchestration UI and monitor through completion.

## Validation

- The previously stuck task is no longer in running state and shows either "failed" or "success"
- No orphaned compute resources (pods, Spark executors) remain from the stuck task
- The re-triggered task completes within its expected duration
- Downstream tasks resume execution once the re-run succeeds

## Rollback

1. If clearing the stuck task causes unintended cascading retries, pause the DAG immediately.
2. Manually mark any incorrectly triggered downstream tasks as skipped or failed to halt the cascade.
3. Investigate whether any partial writes occurred during the stuck task's runtime; clean up incomplete output partitions.
4. Re-enable the DAG only after confirming the root cause and applying the fix.
5. Document the stuck task event and resolution in the incident tracker.
