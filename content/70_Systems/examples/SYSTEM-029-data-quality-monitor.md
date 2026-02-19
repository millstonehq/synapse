---
id: SYSTEM-029
type: system
title: Data Quality Monitor
status: approved
owner: Data Engineering
owner_team: Data Engineering
runtime: Lambda / Node.js 20 / DynamoDB
created: '2024-10-15T11:29:18.847Z'
updated: '2026-05-22T20:52:02.364Z'
tags:
  - system
  - data-pipeline
summary: Data Quality Monitor
sla: 99.95% monthly uptime
repos:
  - https://git.example.com/acme/data-quality-monitor
dependencies:
  - Data Transformation Engine
  - Data Lake Ingestion Service
runbooks:
  - RUNBOOK-038
  - RUNBOOK-076
example: true
---

## Overview

The Data Quality Monitor continuously evaluates data quality rules against datasets as they flow through the pipeline. It subscribes to completion events from the Data Transformation Engine and the Data Lake Ingestion Service, runs configured rule sets against each dataset, and publishes quality scores and violation alerts.

The monitor evaluates approximately 400 quality rule checks per day across 90 active datasets. Rules cover completeness, uniqueness, referential integrity, and statistical range checks. Violations above configured severity thresholds trigger PagerDuty alerts and optionally block downstream pipeline consumers.

## Architecture

- **Rule Engine**: Lambda functions execute rule sets per dataset. Each rule is a SQL predicate evaluated against the target Iceberg table via Athena. Results are stored in DynamoDB with pass/fail status and violation counts.
- **Subscription Layer**: Listens to pipeline completion events via SQS. Each event triggers the rule engine for the completed dataset.
- **Alerting Layer**: Violations are classified by severity (WARN, ERROR, CRITICAL). CRITICAL violations page the on-call engineer; ERROR violations log to the quality dashboard; WARN violations accumulate as trend data.
- **Dashboard API**: REST API (Lambda / Node.js 20) serves quality scores per dataset, trend data, and violation history to the Data Quality Dashboard frontend.

## Repositories

- [data-quality-monitor](https://git.example.com/acme/data-quality-monitor) - Lambda functions, rule definitions, DynamoDB schemas

## Runtime Environment

- **Platform**: Lambda / Node.js 20 / DynamoDB
- **Concurrency**: Up to 50 concurrent Lambda executions for parallel rule evaluation
- **Deployment**: SAM-based deployments via ArgoCD; rule definitions deployed as DynamoDB seed migrations

## Dependencies

- Data Transformation Engine - emits dataset completion events that trigger quality checks
- Data Lake Ingestion Service - emits raw dataset completion events for ingestion-layer quality checks

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.95% monthly uptime |
| Rule evaluation latency | P95 < 5 minutes from dataset completion event to quality score published |
| Alert delivery | CRITICAL violations alerted within 2 minutes of detection |
| Recovery | MTTR < 30 minutes for SEV-1 incidents |

## Runbooks

- [[RUNBOOK-038|Quality Rule Failure Response]]
- [[RUNBOOK-076|Data Pipeline Checkpoint Recovery]]
