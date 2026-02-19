---
id: RUNBOOK-037
type: runbook
title: Airflow Scheduler Down Runbook
status: review
owner: On-Call Engineer
created: '2024-01-27T00:37:25.108Z'
updated: '2025-03-22T03:36:22.132Z'
tags:
  - runbook
  - data-pipeline
summary: Airflow Scheduler Down Runbook
example: true
---

## Service

- **System**: [[SYSTEM-027|Airflow Scheduler]]
- **Owner team**: Data Platform Engineering
- **On-call rotation**: PagerDuty schedule "data-platform-oncall"
- **Slack channel**: #data-incidents
- **Runtime**: Airflow 2.7 / Kubernetes / PostgreSQL (metadata DB)

## Alerts

- `airflow_scheduler_heartbeat_missing` - Scheduler has not emitted a heartbeat for more than 5 minutes
- `airflow_scheduler_pod_not_running` - Airflow scheduler pod is not in Running state
- `airflow_dag_runs_not_progressing` - No DAG runs have transitioned state in 10 minutes during expected active hours
- `airflow_metadata_db_connection_failed` - Scheduler cannot connect to the metadata database

## Diagnosis Steps

1. **Check scheduler pod status** - Run `kubectl get pods -n airflow -l component=scheduler` to verify the scheduler pod state; note any restart count or error status.
2. **Review scheduler pod logs** - Run `kubectl logs -n airflow -l component=scheduler --since=30m` and look for database connection errors, OOM events, or Python import errors.
3. **Check metadata database connectivity** - Verify the Airflow metadata database is accessible: connect to the DB host and run a simple query. Scheduler failure is most commonly caused by metadata DB unavailability.
4. **Check recent Airflow upgrades or config changes** - Review the #data-releases channel for any Airflow version upgrades, configuration changes, or DAG code deployments in the last hour.
5. **Check scheduler resource utilization** - Run `kubectl top pod -n airflow -l component=scheduler` to check for CPU or memory exhaustion; memory leaks can cause the scheduler to be OOM-killed.
6. **Inspect DAG parse errors** - If the scheduler is running but not progressing DAGs, check for DAG parse errors by running `airflow dags list-import-errors` or reviewing the Airflow UI DAG error panel.

## Remediation Steps

1. **If scheduler pod is crashlooping**: Describe the pod for the exit reason (`kubectl describe pod [pod] -n airflow`), address the root cause, then restart: `kubectl rollout restart deployment/airflow-scheduler -n airflow`.
2. **If metadata DB is unavailable**: Page the database on-call; the scheduler cannot operate without the metadata DB. Do not attempt to restart the scheduler until the DB is confirmed healthy.
3. **If DAG parse errors are blocking the scheduler**: Identify and fix the broken DAG file, then trigger a DAG reload. Broken DAG imports can prevent the scheduler from processing any runs.
4. **If scheduler is resource-exhausted**: Increase scheduler pod memory limits in the Helm values and re-deploy.
5. **If a recent deployment caused the failure**: Roll back the Airflow version or configuration change using the CI/CD system.
6. **If cause is unknown after 15 minutes**: Escalate to the Data Platform tech lead.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 5 min | Post status in #data-incidents |
| 15 min | If not resolved: page Data Platform tech lead via PagerDuty |
| 30 min | If not resolved: notify downstream teams of pipeline delay |
| 60 min | If not resolved: escalate to Engineering Manager |

## Dashboards

- [Airflow Scheduler Health](https://grafana.example.com/d/airflow-scheduler) - Heartbeat rate, DAG run state transitions
- [Airflow DAG Run Status](https://grafana.example.com/d/airflow-dag-runs) - Active, queued, and failed run counts
- [Airflow Metadata DB](https://grafana.example.com/d/airflow-metadata-db) - Connection pool, query latency
- [Kubernetes Airflow Namespace](https://grafana.example.com/d/k8s-airflow) - Pod health, restarts, resource usage
