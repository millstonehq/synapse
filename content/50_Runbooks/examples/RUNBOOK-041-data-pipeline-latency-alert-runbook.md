---
id: RUNBOOK-041
type: runbook
title: Data Pipeline Latency Alert Runbook
status: approved
owner: On-Call Engineer
created: '2024-07-26T10:54:00.388Z'
updated: '2025-03-06T00:04:53.334Z'
tags:
  - runbook
  - data-pipeline
summary: Data Pipeline Latency Alert Runbook
example: true
---

## Service

- **System**: [[SYSTEM-027|Data Pipeline Platform]]
- **Owner team**: Data Platform Engineering
- **On-call rotation**: PagerDuty schedule "data-platform-oncall"
- **Slack channel**: #data-incidents
- **Runtime**: Airflow / Spark / Kafka / S3

## Alerts

- `pipeline_end_to_end_latency_high` - Pipeline end-to-end latency exceeds SLA threshold for 3 consecutive runs
- `pipeline_task_duration_anomaly` - Individual task duration is more than 3x the 7-day P95
- `pipeline_sla_breach_imminent` - Pipeline is on track to miss its SLA window based on current progress rate
- `pipeline_queue_backlog_high` - Number of queued DAG runs exceeds 50 for a single pipeline

## Diagnosis Steps

1. **Identify the slowest stage** - Open the pipeline's Gantt chart in the Airflow UI and identify which task accounts for the most time in the current run versus the historical average.
2. **Check upstream dependency wait times** - Verify that sensors or upstream tasks waiting for data availability are not blocking execution; check if a dependency pipeline has itself been delayed.
3. **Review resource contention** - Run `kubectl top pods -n data-pipelines` to assess whether worker nodes are CPU or memory constrained during the period of high latency.
4. **Check data volume growth** - Compare the input record count for the current run against the 7-day average in the pipeline metrics dashboard; a sudden data volume increase can explain latency growth.
5. **Inspect Spark or transform job execution** - If a Spark-based stage is slow, open the Spark UI for the job and check for data skew, excessive shuffle, or GC pressure.
6. **Check external storage I/O** - Review S3 latency metrics for the time window; elevated S3 latency or throttling can cause pipeline slowdowns across many stages.

## Remediation Steps

1. **If upstream dependency is delayed**: Check the upstream pipeline status; if it is also delayed, the latency cascades. Escalate to the upstream pipeline owner.
2. **If worker nodes are resource-constrained**: Scale up the Airflow worker pool or Spark executor pool to provide additional compute capacity.
3. **If a specific stage has grown due to data volume**: Optimize the transformation (add partition pruning, improve parallelism) or increase per-task resource allocation.
4. **If S3 throttling is the cause**: Implement exponential backoff in the pipeline's S3 read/write operations; request a throughput increase from the infrastructure team if persistent.
5. **If a recent code change introduced the regression**: Roll back the pipeline change and profile the transformation logic in staging before re-deploying.
6. **If SLA breach is imminent and cannot be resolved**: Notify the SLA owner and downstream consumers with an estimated completion time.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer identifies the delayed pipeline and stage |
| 15 min | Post status in #data-incidents with estimated completion time |
| 30 min | If SLA breach is confirmed: notify downstream consumer teams |
| 60 min | If not resolved: escalate to Data Platform tech lead |

## Dashboards

- [Pipeline Latency Overview](https://grafana.example.com/d/pipeline-latency) - End-to-end duration trends per pipeline
- [Pipeline Task Duration](https://grafana.example.com/d/pipeline-tasks) - Per-task duration vs historical baseline
- [Airflow Worker Utilization](https://grafana.example.com/d/airflow-workers) - CPU, memory, task slot utilization
- [S3 Throughput and Latency](https://grafana.example.com/d/s3-ops) - Read/write latency and throttling rates
