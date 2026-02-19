---
id: SOP-054
type: sop
title: Deploy Data Pipeline Changes SOP
status: approved
owner: SRE Lead
created: '2025-02-02T13:02:12.757Z'
updated: '2026-11-10T09:05:19.473Z'
tags:
  - sop
  - data-pipeline
summary: Deploy Data Pipeline Changes SOP
related_process: PROCESS-035
related_systems:
  - SYSTEM-027
example: true
---

## Preconditions

- The pipeline change PR has been reviewed, approved, and merged with passing CI
- A release ticket exists with risk classification and a documented rollback plan
- For schema changes: schema compatibility check has passed and consumer teams have been notified
- The on-call data engineer is available and monitoring during the deployment window

## Materials/Access

- Access to the pipeline orchestration platform (Airflow or Dagster UI)
- CI/CD pipeline deployment credentials or GitOps access to the pipeline configuration repo
- Access to Grafana pipeline monitoring dashboard
- Access to #data-releases Slack channel

## Procedure

1. Post in #data-releases: "Starting pipeline release for [pipeline_name]. Release ticket: [ID]. On-call: [name]."
2. In the CI/CD system, trigger the pipeline deployment job for the approved commit SHA targeting the production environment.
3. Monitor the deployment job output; confirm the new DAG or job definition is loaded without syntax errors.
4. In the orchestration UI, verify the updated pipeline definition is visible and shows the correct version.
5. Pause the pipeline scheduler temporarily to prevent an immediate run while you verify the configuration.
6. Review the deployed DAG or job configuration against the PR to confirm all changes landed correctly.
7. Un-pause the pipeline and trigger one manual test run for the most recent complete execution date.
8. Monitor the test run through completion; confirm all tasks succeed and output record counts are within expected range.
9. Mark the release ticket as deployed with the commit SHA and first successful run timestamp.

## Validation

- The orchestration UI shows the updated pipeline version active in production
- The first post-deployment run completes with all tasks in "success" state
- Output dataset record counts are consistent with pre-deployment baseline
- No new alerts have fired in the monitoring system following deployment

## Rollback

1. If the deployed pipeline fails, pause the pipeline immediately to halt further runs.
2. Revert the pipeline definition by re-deploying the previous commit SHA via the CI/CD system.
3. Confirm the orchestration UI reflects the reverted pipeline definition.
4. Un-pause the pipeline and verify a run completes successfully with the previous version.
5. Update the release ticket with rollback timestamp and reason; open an investigation ticket.
