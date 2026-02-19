---
id: SOP-053
type: sop
title: Backfill Historical Data SOP
status: approved
owner: SRE Lead
created: '2025-12-22T22:31:44.564Z'
updated: '2025-01-17T10:13:15.414Z'
tags:
  - sop
  - data-pipeline
summary: Backfill Historical Data SOP
related_process: PROCESS-066
related_systems:
  - SYSTEM-030
example: true
---

## Preconditions

- A backfill ticket has been created and approved specifying the date range, pipeline, and reason for the backfill
- Source data for the target date range is confirmed present and valid in the source system
- The target output partitions to be overwritten have been identified and consumers notified of the reprocessing window
- Sufficient compute capacity is available; large backfills (>30 days) require capacity pre-approval

## Materials/Access

- Airflow web UI or CLI access to trigger DAG backfill runs
- Write access to the target data lake bucket or warehouse table
- Access to Grafana pipeline monitoring dashboard
- Access to #data-releases Slack channel

## Procedure

1. Post in #data-releases: "Starting backfill of [pipeline] for date range [start] to [end]. Ticket: [ID]."
2. Verify the current production pipeline code handles the historical date range correctly; check for date-range-sensitive logic or schema differences in historical data.
3. In the Airflow UI, navigate to the target DAG and select "Trigger DAG w/ config" or use `airflow dags backfill -s [start_date] -e [end_date] [dag_id]` from the CLI.
4. Set `--reset-dagruns` flag if prior failed runs exist for the target dates to avoid task state conflicts.
5. Monitor the backfill run queue; for large ranges, limit concurrency with `--max-active-runs` to avoid resource contention.
6. Watch the first 3 execution dates complete and verify output record counts match expected values from the source.
7. After all backfill runs complete, run a reconciliation query comparing source record counts to target record counts per partition.
8. Post in #data-releases: "Backfill of [pipeline] complete. Partitions [start] to [end] reconciled. Ticket [ID] closed."

## Validation

- All backfill DAG runs show "success" status in Airflow for the specified date range
- Record counts in the target table match source record counts per partition within 0.1% tolerance
- No duplicate records exist in the target partitions (verified via primary key uniqueness check)
- Downstream consumers confirm data is correctly reflected for the backfilled date range

## Rollback

1. If backfilled data is incorrect, drop or overwrite the affected target partitions using the idempotent delete-and-reload pattern.
2. Pause the pipeline to prevent new data from overwriting the state during investigation.
3. Notify downstream consumers that the backfill data for the affected range is being corrected.
4. Investigate the root cause (code logic, source data quality) before re-triggering the backfill.
5. Document the failed backfill attempt and corrective steps in the backfill ticket before closing.
