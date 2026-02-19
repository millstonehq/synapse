---
id: RUNBOOK-039
type: runbook
title: Spark Job OOM Failure Runbook
status: draft
owner: On-Call Engineer
created: '2024-06-15T22:59:04.373Z'
updated: '2026-05-30T16:39:44.589Z'
tags:
  - runbook
  - data-pipeline
summary: Spark Job OOM Failure Runbook
example: true
---

## Service

- **System**: [[SYSTEM-027|Spark Cluster]]
- **Owner team**: Data Platform Engineering
- **On-call rotation**: PagerDuty schedule "data-platform-oncall"
- **Slack channel**: #data-incidents
- **Runtime**: Apache Spark 3.4 / Kubernetes / S3

## Alerts

- `spark_job_oom_killed` - Spark executor or driver killed with OOM error
- `spark_job_failed_oom` - Spark job exits with exit code 137 (OOM kill)
- `spark_executor_memory_high` - Executor JVM heap usage exceeds 90% for 5 minutes
- `spark_driver_gc_time_high` - GC pause time exceeds 30% of execution time for 10 minutes

## Diagnosis Steps

1. **Identify the failing job and stage** - Open the Spark History Server UI and find the failed application; review the event timeline to identify the stage and task where OOM occurred.
2. **Check executor memory configuration** - Review the job's Spark configuration: `spark.executor.memory`, `spark.executor.memoryOverhead`, and `spark.driver.memory`. Compare against the actual JVM heap usage shown in the Executor tab.
3. **Identify the data volume for the failing stage** - Check the stage details for shuffle read/write size and task input size. Unexpectedly large data volumes (due to upstream data growth or missing partition filters) are the most common OOM cause.
4. **Check for data skew** - Inspect the task duration distribution in the failing stage; if a small number of tasks are taking much longer than others and failing, data skew is likely causing individual tasks to process disproportionate data volumes.
5. **Review recent code or data changes** - Check if a recent pipeline code change introduced a broad table scan, a cross-join, or a missing filter that increased data volume significantly.

## Remediation Steps

1. **If executor memory is simply undersized for current data volume**: Increase `spark.executor.memory` and `spark.executor.memoryOverhead` in the job configuration and re-submit.
2. **If data skew is the cause**: Apply salting to the skewed join key or use Spark's adaptive query execution (AQE) with `spark.sql.adaptive.skewJoin.enabled=true`.
3. **If a missing partition filter is causing a full table scan**: Fix the transformation code to include the appropriate date partition filter and re-deploy.
4. **If the driver is OOM**: Increase `spark.driver.memory` and investigate whether the driver is collecting large result sets via `collect()` that should instead be written directly to storage.
5. **If the issue is a recent code change**: Roll back the pipeline change and investigate the data volume impact in staging before re-deploying.
6. **If persistent memory issues continue after tuning**: Escalate to the Data Platform lead for architecture review.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer identifies failing job and reviews Spark UI |
| 15 min | Post findings in #data-incidents with job name and failure stage |
| 30 min | If tuning does not resolve: escalate to Pipeline Owner for code review |
| 60 min | If downstream SLA is at risk: notify Data Platform lead |

## Dashboards

- [Spark Job History](https://spark-history.example.com) - Job and stage execution details
- [Spark Executor Memory](https://grafana.example.com/d/spark-executors) - Heap usage, GC time per job
- [Data Pipeline Run Status](https://grafana.example.com/d/pipeline-runs) - Job success/failure history
- [Data Volume Trends](https://grafana.example.com/d/data-volumes) - Input record counts per pipeline per day
