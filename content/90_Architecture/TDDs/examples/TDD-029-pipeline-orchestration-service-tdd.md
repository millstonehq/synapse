---
id: TDD-029
type: tdd
title: Pipeline Orchestration Service TDD
status: proposed
owner: Senior Engineer
created: '2025-08-11T23:01:00.046Z'
updated: '2026-09-01T14:19:37.499Z'
tags:
  - tdd
  - data-pipeline
summary: Pipeline Orchestration Service TDD
related_adrs:
  - ADR-0024
  - ADR-0022
example: true
---

## Summary

Design the Pipeline Orchestration Service — the Airflow-based orchestration layer that schedules and coordinates all data pipeline DAGs, manages inter-DAG dependencies, enforces SLA windows, and provides a centralized operational view of pipeline health. The service replaces ad-hoc cron-based scheduling with dependency-aware DAG execution backed by a managed Airflow deployment.

This TDD follows the dbt transformation layer established in [[ADR-0024|ADR-0024: Adopt dbt for Data Transformations]] and incorporates pipeline reliability patterns from [[ADR-0022|ADR-0022]].

## Overview

The Pipeline Orchestration Service runs as Apache Airflow 2.7+ on AWS MWAA (Managed Workflows for Apache Airflow). All pipeline DAGs are defined as Python code in the `dags/` directory of the data-pipeline repository and deployed via a CI/CD pipeline that syncs DAG files to the MWAA S3 DAG bucket. Orchestration covers: ingestion trigger DAGs, dbt transformation DAGs (using the dbt-airflow operator), data quality check DAGs, and SLA monitoring DAGs.

Key design principles:
- **DAGs as code**: All DAG definitions live in the data-pipeline repository under version control; no DAG authoring in the Airflow UI
- **Strict retry limits**: All DAGs enforce `retries <= 5` and `retry_delay >= timedelta(minutes=5)`; DAG validation CI step rejects pathological configurations (lesson from Oct 2024 deadlock incident)
- **SLA callbacks**: All Tier-1 DAGs define `sla=timedelta(hours=2)` miss callbacks that publish to the SLA breach SNS topic
- **Idempotent tasks**: All tasks are idempotent; rerunning a DAG from any task produces the same result

## Architecture

### Component Diagram

The service has three layers:

- **MWAA Environment**: Managed Airflow scheduler and workers; auto-scales workers 1–10 based on task queue depth
- **DAG Layer**: Python DAG definitions; organized by pipeline domain (ingestion/, transformation/, quality/, monitoring/)
- **Operator Plugins**: Custom operators for dbt runs (`DbtRunOperator`), Iceberg compaction triggers (`IcebergCompactOperator`), and SLA check publication (`SLAPublishOperator`)

### DAG Categories

- **`ingestion/`** (Continuous/Sensor): Monitor ECS ingestion task health, trigger backfill on gap detection
- **`transformation/`** (Hourly): Run dbt models against Iceberg tables
- **`quality/`** (Post-dbt): Invoke Data Quality Validation Framework Lambda
- **`monitoring/`** (Daily): Capacity and freshness SLA compliance reports

## Information Model

### Core Entities

- **DAGRun**: Airflow metadata. Fields: `dag_id`, `run_id`, `execution_date`, `state`, `start_date`, `end_date`, `external_trigger`
- **TaskInstance**: Airflow metadata. Fields: `dag_id`, `task_id`, `execution_date`, `state`, `try_number`, `start_date`, `duration`
- **SLAMiss**: Airflow SLA tracking. Fields: `dag_id`, `task_id`, `execution_date`, `timestamp`, `description`

### MWAA Configuration

- Worker instance class: `mw1.medium` (4 vCPU, 16 GB RAM)
- Max worker count: 10
- Scheduler count: 2 (active-standby)
- Metadata DB: Aurora PostgreSQL (managed by MWAA)
- DAG serialization: enabled (reduces scheduler metadata DB load)

## Interfaces

### dbt-Airflow Operator

```python
DbtRunOperator(
    task_id="run_dbt_marts",
    dbt_project_dir="/opt/airflow/dbt",
    dbt_profile="prod",
    models="tag:mart",
    select="state:modified+",
    fail_fast=True,
    retries=2,
    retry_delay=timedelta(minutes=10),
)
```

### DAG Validation Rules (CI enforcement)

- `retries` must be <= 5
- `retry_delay` must be >= `timedelta(minutes=5)`
- All Tier-1 DAGs must define `sla` callback
- No dynamic task generation without `max_active_tasks` cap

## Files and Layout

```
dags/
  ingestion/
    ingestion_health_monitor.py     - ECS task health sensor DAG
    backfill_trigger.py             - Kafka gap-triggered backfill DAG
  transformation/
    dbt_staging_hourly.py           - Hourly dbt staging run
    dbt_marts_hourly.py             - Hourly dbt marts run (depends on staging)
    iceberg_compaction_daily.py     - Daily Iceberg snapshot compaction
  quality/
    quality_check_post_dbt.py       - Lambda-based quality check trigger
  monitoring/
    sla_compliance_daily.py         - Daily SLA compliance report DAG
plugins/
  operators/
    dbt_run_operator.py
    iceberg_compact_operator.py
    sla_publish_operator.py
  hooks/
    trino_hook.py                   - Trino connection hook
```

## Work Plan

1. **Phase 1 — MWAA Setup (Week 1)**: MWAA environment provisioning via Terraform, DAG S3 bucket, CI/CD deployment pipeline, DAG validation step
2. **Phase 2 — Core DAGs (Week 2-3)**: dbt staging and marts DAGs, dependency chain, SLA callbacks
3. **Phase 3 — Quality Integration (Week 4)**: Quality check DAGs, Lambda trigger operator, breach routing
4. **Phase 4 — Custom Operators (Week 5)**: Iceberg compaction operator, SLA publish operator
5. **Phase 5 — Monitoring DAGs (Week 6)**: Capacity and SLA compliance report DAGs, Airflow metrics dashboard

## Risks and Mitigations

- **Risk**: Misconfigured DAG with infinite retry loop causes scheduler deadlock (Oct 2024 incident). **Mitigation**: CI validation step rejects DAGs with `retries > 5` or `retry_delay < 5 minutes` before merge; scheduler heartbeat alert pages on interval > 30 seconds.
- **Risk**: MWAA metadata DB becomes a bottleneck under high DAG run volume. **Mitigation**: DAG serialization enabled; scheduler count set to 2; `max_active_runs_per_dag` capped at 3 per DAG.
- **Risk**: DAG S3 sync lag causes scheduler to run stale DAG code after deployment. **Mitigation**: CI pipeline verifies DAG file checksum in S3 matches deployed commit before closing the deployment gate.
- **Risk**: MWAA upgrade path is constrained by AWS managed versioning cadence. **Mitigation**: MWAA version pinned in Terraform; upgrade window planned quarterly with rollback to previous version if scheduler health checks fail.

## Operations

- **Deployment**: CI/CD syncs DAG files to S3 DAG bucket on merge to main; MWAA picks up changes within 30 seconds.
- **Monitoring**: MWAA metrics dashboard (scheduler heartbeat, task slot utilization, DAG parse time, SLA miss count).
- **Alerting**: Page on scheduler heartbeat > 30 seconds, task slot utilization > 80% for 10 minutes, SLA miss for any Tier-1 DAG.
- **Rollback**: Revert the data-pipeline repository commit and re-sync DAG files to S3; DAG versions are tracked via git history.
