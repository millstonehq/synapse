---
id: PROCESS-066
type: process
title: Data Pipeline Capacity Planning Process
status: draft
owner: Engineering Manager
created: '2025-02-14T05:03:42.626Z'
updated: '2026-05-23T13:25:53.784Z'
tags:
  - process
  - data-pipeline
summary: Data Pipeline Capacity Planning Process
related_standards:
  - STANDARD-034
  - STANDARD-031
related_sops:
  - SOP-055
  - SOP-059
related_systems:
  - SYSTEM-028
example: true
---

## Purpose

Ensure the data pipeline infrastructure — Kafka cluster, ECS ingestion tasks, Aurora PostgreSQL, MWAA Airflow, and the Schema Registry Service ([[SYSTEM-028|SYSTEM-028]]) — is sized to meet throughput, latency, and availability SLAs for the next 6 months. This process prevents reactive capacity expansions driven by incidents and ensures infrastructure budget is allocated ahead of demand. The process must align with [[STANDARD-034|STANDARD-034]] capacity planning standards and [[STANDARD-031|STANDARD-031]] availability requirements.

## Scope

All capacity planning activities for the production data pipeline, including:

- Kafka broker disk, partition count, and throughput capacity
- ECS Fargate task vCPU and memory allocation for ingestion tasks
- Aurora PostgreSQL instance sizing for the checkpoint and quality result stores
- MWAA worker instance type and count for Airflow DAG execution
- DynamoDB read/write capacity for Schema Registry, quality results, and lineage tables

**Out of scope:** Development and staging environment capacity (sized separately at 20% of production), data lake S3 storage (managed via S3 Intelligent-Tiering automatically), Trino cluster sizing (managed by the Platform Engineering team).

## Roles and Responsibilities

- **Capacity Planning Owner** - Data Engineering Manager. Responsible for: initiating the quarterly capacity review, consolidating team inputs, and approving the capacity plan.
- **Platform Engineer** - Reviews Kafka broker and MWAA capacity requirements and provides infrastructure cost estimates.
- **Data Engineer (On-Call)** - Provides current utilization metrics and growth forecasts for their owned pipeline components.
- **Finance Business Partner** - Reviews infrastructure budget impact of capacity changes exceeding $10,000 quarterly.

## Triggers

- Quarterly cadence: first Monday of each quarter (January, April, July, October)
- Ad-hoc: any component sustaining > 75% utilization for > 7 consecutive days triggers an unscheduled review
- Ad-hoc: any capacity-related incident (e.g., disk exhaustion, ECS out-of-memory) triggers an emergency review within 5 business days

## Inputs

- CloudWatch utilization metrics (exported via [[SOP-055|SOP-055]] quarterly metrics export procedure) for the trailing 90-day period
- Kafka Cluster Capacity Report (from the monthly REPORT-047 cycle)
- Data Pipeline SLA Compliance Report for the prior quarter (from the REPORT-048 cycle)
- Engineering roadmap from the quarterly planning process (identifies new event sources, pipeline additions)
- Current infrastructure cost breakdown from the AWS Cost Explorer monthly export

## Outputs

- Approved capacity plan document specifying target configuration for each component for the next 6 months
- Jira epics for any capacity changes requiring engineering effort (> 4 hours)
- Updated Terraform configuration PRs for configuration changes (instance types, DynamoDB capacity modes)
- Infrastructure budget delta for the quarter (submitted to Finance for approval if > $10,000)
- Capacity review meeting notes published to the Data Engineering Confluence space

## Steps

1. **Capacity Planning Owner** exports trailing 90-day utilization metrics via [[SOP-055|SOP-055]] and distributes to the team 5 business days before the review meeting
2. **Each Data Engineer** reviews utilization trends for their owned components and prepares a forecast for the next 6 months based on the engineering roadmap and historical growth rate
3. **Capacity Planning Owner** hosts the quarterly capacity review meeting; each component owner presents their current utilization, growth projection, and recommended capacity target
4. **Platform Engineer** provides infrastructure cost estimates for proposed capacity changes
5. **Capacity Planning Owner** compiles the approved capacity plan document; changes requiring > $10,000 quarterly budget are escalated to the Finance Business Partner for approval
6. **Data Engineers** open Terraform PRs for approved configuration changes; changes are reviewed by the Platform Engineer and merged following the standard change process via [[SOP-059|SOP-059]]
7. **Capacity Planning Owner** creates Jira epics for engineering-effort changes (Kafka partition rebalancing, Aurora instance upgrades, MWAA worker class changes)
8. **Capacity Planning Owner** publishes the approved plan and meeting notes to Confluence and updates the capacity planning Jira board

## Controls

- Quarterly capacity review must be completed within the first 15 business days of each quarter
- No component may operate above 80% of its provisioned capacity for > 30 consecutive days without an approved capacity change in progress
- All capacity changes to production Kafka brokers must follow the broker maintenance procedure (cooldown intervals, communication to data engineering on-call)
- Infrastructure budget changes > $10,000 per quarter require Finance approval before Terraform changes are applied
- Capacity plan documents are retained for 24 months for audit and trend analysis
