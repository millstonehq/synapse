---
id: SYSTEM-027
type: system
title: Data Transformation Engine
status: approved
owner: Data Engineering
owner_team: Data Engineering
runtime: ECS Fargate / Python 3.12 / OpenSearch / Redis 7
created: '2024-12-04T14:26:45.842Z'
updated: '2025-01-21T04:59:45.166Z'
tags:
  - system
  - data-pipeline
summary: Data Transformation Engine
sla: 99.95% monthly uptime
repos:
  - https://git.example.com/acme/data-transformation-engine
dependencies:
  - Data Lake Ingestion Service
  - Data Quality Monitor
runbooks:
  - RUNBOOK-038
  - RUNBOOK-036
example: true
---

## Overview

The Data Transformation Engine executes dbt models and custom Python transformation scripts that convert raw ingested data into clean, enriched analytical datasets. It runs on ECS Fargate and is triggered by the pipeline orchestration scheduler after ingestion jobs complete.

The engine processes approximately 800 transformation jobs per day across 120 active dbt models. Transformations range from simple column renaming to complex multi-source joins with business rule application. All output is written to Iceberg tables in the data lake, with OpenSearch used for full-text indexed projections.

## Architecture

- **Execution Layer**: ECS Fargate tasks launched per-model by the orchestration scheduler. Each task pulls model code from S3, executes transformation, and writes results to the output Iceberg table.
- **Dependency Resolution**: dbt lineage graph determines task ordering. The orchestrator reads the compiled manifest.json to build the DAG and schedules tasks respecting upstream dependencies.
- **State Tracking**: Redis 7 caches job state (queued / running / succeeded / failed) with TTL of 24 hours. The orchestrator polls Redis for downstream dependency satisfaction before launching downstream tasks.
- **Error Handling**: Failed tasks retry up to 3 times with exponential backoff. After exhausting retries, the task is marked failed and alerts fire. Downstream tasks are blocked until the upstream failure is resolved.
- **Quality Gate**: After each transformation, the Data Quality Monitor is notified via an event. Quality violations above the threshold threshold block dependent downstream models.

## Repositories

- [data-transformation-engine](https://git.example.com/acme/data-transformation-engine) - dbt project, Python transform scripts, ECS task definitions

## Runtime Environment

- **Platform**: ECS Fargate / Python 3.12 / OpenSearch / Redis 7
- **Scaling**: 1-50 concurrent Fargate tasks based on queue depth; each task uses 2 vCPU and 4Gi memory
- **Deployment**: Blue-green task definition updates via ArgoCD; dbt models versioned in git

## Dependencies

- Data Lake Ingestion Service - writes raw Iceberg tables that transformation models read
- Data Quality Monitor - receives transformation completion events and validates output datasets

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.95% monthly uptime |
| Full refresh cycle time | All tier-1 models complete within 90 minutes of trigger |
| Error rate | < 2% of daily model runs fail on first attempt |
| Recovery | Failed model manually rerun within 30 minutes of alert |

## Runbooks

- [[RUNBOOK-038|Transformation Job Failure]]
- [[RUNBOOK-036|Consumer Lag Remediation]]
