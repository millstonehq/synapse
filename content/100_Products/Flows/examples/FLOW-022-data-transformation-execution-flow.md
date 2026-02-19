---
id: FLOW-022
type: flow
title: Data Transformation Execution Flow
status: approved
owner: QA Engineer
created: '2024-01-31T04:18:15.120Z'
updated: '2026-02-08T06:19:39.679Z'
tags:
  - flow
  - data-pipeline
summary: Data Transformation Execution Flow
feature_area: Data Pipeline
related_prds:
  - PRD-026
example: true
---

## Steps

### Step 1: Airflow Triggers dbt Run

The Airflow transformation DAG fires on its configured schedule (hourly for standard models, every 15 minutes for Tier-1 models). The `DbtRunOperator` task starts the dbt process with `--select state:modified+` to run only models downstream of data changes detected via dbt state comparison. The dbt project connects to the Trino cluster using the credentials injected from AWS Secrets Manager.

### Step 2: dbt Resolves Dependency Graph

dbt reads the project's `manifest.json` to construct the DAG of models. It compares the current state against the previous successful run to identify modified models and their dependents. The execution plan is logged, including the model order and parallelism level (default: 4 threads).

### Step 3: Staging Layer Models Execute

dbt executes staging layer models first. Each staging model reads directly from the raw Iceberg table layer via Trino, performs lightweight field renaming, type casting, and null coalescing, and writes results to the `staging` schema Iceberg tables using the `incremental` materialization strategy. New records (those with `event_time` > the previous high watermark) are inserted; no updates to existing records at the staging layer.

### Step 4: Intermediate Layer Models Execute

After staging models complete, dbt executes intermediate models that join across staging tables (e.g., joining `stg_orders` with `stg_customers`). Intermediate models use `incremental` materialization with merge key on business ID. The Trino `MERGE INTO` statement handles upserts atomically in the intermediate Iceberg table.

### Step 5: Mart Layer Models Execute

Finally, dbt executes mart-layer models. These models aggregate from intermediate tables to produce business-facing metrics and dimension tables. Mart models use `incremental` materialization with date partitioning. dbt tests (not_null, unique, relationships) run automatically after each mart model completes; a test failure marks the task as failed in Airflow.

### Step 6: dbt Run Summary Posted and Lineage Updated

On dbt run completion (success or failure), the `DbtRunOperator` captures the dbt run artifacts (`run_results.json`, updated `manifest.json`) and uploads them to the S3 artifacts bucket. The Airflow DAG's post-run task triggers the Data Lineage Tracker Lambda to parse the updated manifest and refresh the lineage graph. The Airflow UI shows the full dbt run summary including row counts and test results per model.

## Expected Results

- Staging, intermediate, and mart layer Iceberg tables are updated with data from the most recent ingestion cycle
- dbt tests pass for all mart-layer models; failures block downstream DAG tasks and alert on-call
- Data Lineage Tracker is refreshed with any new or modified model lineage within 10 minutes of run completion
- Mart layer data reflects all raw events ingested before the dbt run start time
- Failed models are logged with the dbt error context; Airflow marks the DAG run as failed for operator review

## User Info

| Field | Value |
|-------|-------|
| Role | Data pipeline operator / data engineer |
| Permissions | Read access to Airflow DAG run history, dbt run artifacts in S3, Trino query logs |
| Test dbt project | `dbt/` in the data-pipeline repository, `staging` profile |
| Test Iceberg tables | `data-lake-staging.staging.*`, `data-lake-staging.marts.*` |
| Environment | Staging |
